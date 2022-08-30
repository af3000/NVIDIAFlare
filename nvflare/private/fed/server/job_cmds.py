# Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import io
import json
import logging
import os
import shutil
import traceback
from typing import Dict, List

import nvflare.fuel.hci.file_transfer_defs as ftd
from nvflare.apis.fl_constant import AdminCommandNames
from nvflare.apis.job_def import Job, JobDataKey, JobMetaKey
from nvflare.apis.job_def_manager_spec import JobDefManagerSpec, RunStatus
from nvflare.apis.utils.common_utils import get_size
from nvflare.fuel.hci.base64_utils import b64str_to_bytes, bytes_to_b64str
from nvflare.fuel.hci.conn import Connection
from nvflare.fuel.hci.proto import ConfirmMethod
from nvflare.fuel.hci.reg import CommandModule, CommandModuleSpec, CommandSpec
from nvflare.fuel.hci.server.authz import PreAuthzReturnCode
from nvflare.fuel.hci.server.constants import ConnProps
from nvflare.fuel.hci.table import Table
from nvflare.fuel.hci.zip_utils import convert_legacy_zip, unzip_all_from_bytes, zip_directory_to_bytes
from nvflare.fuel.utils.argument_utils import SafeArgumentParser
from nvflare.private.defs import RequestHeader, TrainingTopic
from nvflare.private.fed.server.admin import new_message
from nvflare.private.fed.server.job_meta_validator import JobMetaValidator
from nvflare.private.fed.server.server_engine import ServerEngine
from nvflare.private.fed.server.server_engine_internal_spec import ServerEngineInternalSpec

from .cmd_utils import CommandUtil

META_FILE = "meta.json"
MAX_DOWNLOAD_JOB_SIZE = 50 * 1024 * 1024 * 1204


class JobCommandModule(CommandModule, CommandUtil):
    """Command module with commands for job management."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_spec(self):
        return CommandModuleSpec(
            name="job_mgmt",
            cmd_specs=[
                CommandSpec(
                    name=AdminCommandNames.DELETE_WORKSPACE,
                    description="delete the workspace of a job",
                    usage="delete_workspace job_id",
                    handler_func=self.delete_job_id,
                    authz_func=self.authorize_job,
                    enabled=False,
                    confirm=ConfirmMethod.AUTH,
                ),
                CommandSpec(
                    name=AdminCommandNames.START_APP,
                    description="start the FL app",
                    usage="start_app job_id server|client|all",
                    handler_func=self.start_app,
                    authz_func=self.authorize_job,
                ),
                CommandSpec(
                    name=AdminCommandNames.LIST_JOBS,
                    description="list submitted jobs",
                    usage="list_jobs [-n name_prefix] [-d] [job_id_prefix]",
                    handler_func=self.list_jobs,
                    authz_func=self.command_authz_required,
                ),
                CommandSpec(
                    name=AdminCommandNames.DELETE_JOB,
                    description="delete a job and persisted workspace",
                    usage="delete_job job_id",
                    handler_func=self.delete_job,
                    authz_func=self.authorize_job,
                    confirm=ConfirmMethod.AUTH,
                ),
                CommandSpec(
                    name=AdminCommandNames.ABORT_JOB,
                    description="abort a job if it is running or dispatched",
                    usage="abort_job job_id",
                    handler_func=self.abort_job,  # see if running, if running, send abort command
                    authz_func=self.authorize_job,
                    confirm=ConfirmMethod.YESNO,
                ),
                CommandSpec(
                    name=AdminCommandNames.ABORT_TASK,
                    description="abort the client current task execution",
                    usage="abort_task job_id <client-name>",
                    handler_func=self.abort_task,
                    authz_func=self.authorize_abort_client_operation,
                ),
                CommandSpec(
                    name=AdminCommandNames.CLONE_JOB,
                    description="clone a job with a new job_id",
                    usage="clone_job job_id",
                    handler_func=self.clone_job,
                    authz_func=self.authorize_job,
                ),
                CommandSpec(
                    name=AdminCommandNames.SUBMIT_JOB,
                    description="submit a job",
                    usage="submit_job job_folder",
                    handler_func=self.submit_job,
                    authz_func=self.command_authz_required,
                    client_cmd=ftd.UPLOAD_FOLDER_FQN,
                ),
                CommandSpec(
                    name=AdminCommandNames.DOWNLOAD_JOB,
                    description="download a specified job",
                    usage="download_job job_id",
                    handler_func=self.download_job,
                    authz_func=self.authorize_job,
                    client_cmd=ftd.DOWNLOAD_FOLDER_FQN,
                ),
            ],
        )

    def authorize_job(self, conn: Connection, args: List[str]):
        if len(args) < 2:
            conn.append_error("syntax error: missing job_id")
            return PreAuthzReturnCode.ERROR

        job_id = args[1].lower()
        conn.set_prop(self.JOB_ID, job_id)
        engine = conn.app_ctx
        job_def_manager = engine.job_def_manager

        with engine.new_context() as fl_ctx:
            job = job_def_manager.get_job(job_id, fl_ctx)

        if not job:
            conn.append_error(f"Job with ID {job_id} doesn't exist")
            return PreAuthzReturnCode.ERROR

        conn.set_prop(self.JOB, job)

        conn.set_prop(ConnProps.SUBMITTER_NAME, job.meta.get(JobMetaKey.SUBMITTER_NAME, ""))
        conn.set_prop(ConnProps.SUBMITTER_ORG, job.meta.get(JobMetaKey.SUBMITTER_ORG, ""))
        conn.set_prop(ConnProps.SUBMITTER_ROLE, job.meta.get(JobMetaKey.SUBMITTER_ROLE, ""))

        if len(args) > 2:
            err = self.validate_command_targets(conn, args[2:])
            if err:
                conn.append_error(err)
                return PreAuthzReturnCode.ERROR

        return PreAuthzReturnCode.REQUIRE_AUTHZ

    def abort_task(self, conn, args: List[str]) -> str:
        engine = conn.app_ctx
        if not isinstance(engine, ServerEngineInternalSpec):
            raise TypeError("engine must be ServerEngineInternalSpec but got {}".format(type(engine)))

        job_id = conn.get_prop(self.JOB_ID)
        message = new_message(conn, topic=TrainingTopic.ABORT_TASK, body="", require_authz=False)
        message.set_header(RequestHeader.JOB_ID, str(job_id))
        replies = self.send_request_to_clients(conn, message)
        return self.process_replies_to_table(conn, replies)

    # Start App
    def _start_app_on_server(self, conn: Connection, job_id: str) -> bool:
        engine = conn.app_ctx
        err = engine.start_app_on_server(job_id)
        if err:
            conn.append_error(err)
            return False
        else:
            conn.append_string("Server app is starting....")
            return True

    def _start_app_on_clients(self, conn: Connection, job_id: str) -> bool:
        engine = conn.app_ctx
        err = engine.check_app_start_readiness(job_id)
        if err:
            conn.append_error(err)
            return False

        message = new_message(conn, topic=TrainingTopic.START, body="", require_authz=False)
        message.set_header(RequestHeader.JOB_ID, job_id)
        replies = self.send_request_to_clients(conn, message)
        self.process_replies_to_table(conn, replies)
        return True

    def start_app(self, conn: Connection, args: List[str]):
        engine = conn.app_ctx
        if not isinstance(engine, ServerEngineInternalSpec):
            raise TypeError("engine must be ServerEngineInternalSpec but got {}".format(type(engine)))

        job_id = conn.get_prop(self.JOB_ID)
        target_type = args[2]
        if target_type == self.TARGET_TYPE_SERVER:
            if not self._start_app_on_server(conn, job_id):
                return
        elif target_type == self.TARGET_TYPE_CLIENT:
            if not self._start_app_on_clients(conn, job_id):
                return
        else:
            # all
            success = self._start_app_on_server(conn, job_id)

            if success:
                client_names = conn.get_prop(self.TARGET_CLIENT_NAMES, None)
                if client_names:
                    if not self._start_app_on_clients(conn, job_id):
                        return
        conn.append_success("")

    def delete_job_id(self, conn: Connection, args: List[str]):
        job_id = args[1]
        engine = conn.app_ctx
        if not isinstance(engine, ServerEngine):
            raise TypeError("engine must be ServerEngine but got {}".format(type(engine)))

        if job_id in engine.run_processes.keys():
            conn.append_error(f"Current running run_{job_id} can not be deleted.")
            return

        err = engine.delete_job_id(job_id)
        if err:
            conn.append_error(err)
            return

        # ask clients to delete this RUN
        message = new_message(conn, topic=TrainingTopic.DELETE_RUN, body="", require_authz=False)
        message.set_header(RequestHeader.JOB_ID, str(job_id))
        clients = engine.get_clients()
        if clients:
            conn.set_prop(self.TARGET_CLIENT_TOKENS, [x.token for x in clients])
            replies = self.send_request_to_clients(conn, message)
            self.process_replies_to_table(conn, replies)

        conn.append_success("")

    def list_jobs(self, conn: Connection, args: List[str]):
        try:
            parser = SafeArgumentParser(prog="list_jobs")
            parser.add_argument("job_id", nargs="?", help="Job ID prefix")
            parser.add_argument("-d", action="store_true", help="Show detailed list")
            parser.add_argument("-n", help="Filter by job name prefix")
            parsed_args = parser.parse_args(args[1:])

            engine = conn.app_ctx
            job_def_manager = engine.job_def_manager
            if not isinstance(job_def_manager, JobDefManagerSpec):
                raise TypeError(
                    f"job_def_manager in engine is not of type JobDefManagerSpec, but got {type(job_def_manager)}"
                )

            with engine.new_context() as fl_ctx:
                jobs = job_def_manager.get_all_jobs(fl_ctx)
            if jobs:
                id_prefix = parsed_args.job_id
                name_prefix = parsed_args.n

                filtered_jobs = [job for job in jobs if self._job_match(job.meta, id_prefix, name_prefix)]
                if not filtered_jobs:
                    conn.append_error("No jobs matching the searching criteria")
                    return

                filtered_jobs.sort(key=lambda job: job.meta.get(JobMetaKey.SUBMIT_TIME, 0.0))

                if parsed_args.d:
                    self._send_detail_list(conn, filtered_jobs)
                else:
                    self._send_summary_list(conn, filtered_jobs)

            else:
                conn.append_string("No jobs.")
        except Exception as e:
            conn.append_error(str(e))
            return

        conn.append_success("")

    def delete_job(self, conn: Connection, args: List[str]):
        job = conn.get_prop(self.JOB)
        if not job:
            conn.append_error("program error: job not set in conn")
            return

        job_id = conn.get_prop(self.JOB_ID)
        if job.meta.get(JobMetaKey.STATUS, "") in [RunStatus.DISPATCHED.value, RunStatus.RUNNING.value]:
            conn.append_error(f"job: {job_id} is running, could not be deleted at this time.")
            return

        try:
            engine = conn.app_ctx
            job_def_manager = engine.job_def_manager

            with engine.new_context() as fl_ctx:
                job_def_manager.delete(job_id, fl_ctx)
                conn.append_string("Job {} deleted.".format(job_id))
        except BaseException as e:
            conn.append_error("exception occurred: " + str(e))
            return
        conn.append_success("")

    def abort_job(self, conn: Connection, args: List[str]):
        engine = conn.app_ctx
        job_runner = engine.job_runner

        try:
            job_id = conn.get_prop(self.JOB_ID)
            with engine.new_context() as fl_ctx:
                job_runner.stop_run(job_id, fl_ctx)
            conn.append_string("Abort signal has been sent to the server app.")
            conn.append_success("")
        except Exception as e:
            conn.append_error("Exception occurred trying to abort job: " + str(e))
            return

    def clone_job(self, conn: Connection, args: List[str]):
        job = conn.get_prop(self.JOB)
        job_id = conn.get_prop(self.JOB_ID)
        engine = conn.app_ctx
        try:
            if not isinstance(engine, ServerEngine):
                raise TypeError(f"engine is not of type ServerEngine, but got {type(engine)}")
            job_def_manager = engine.job_def_manager
            if not isinstance(job_def_manager, JobDefManagerSpec):
                raise TypeError(
                    f"job_def_manager in engine is not of type JobDefManagerSpec, but got {type(job_def_manager)}"
                )
            with engine.new_context() as fl_ctx:
                data_bytes = job_def_manager.get_content(job_id, fl_ctx)

                # set the submitter info for the new job
                job.meta[JobMetaKey.SUBMITTER_NAME] = conn.get_prop(ConnProps.USER_NAME)
                job.meta[JobMetaKey.SUBMITTER_ORG] = conn.get_prop(ConnProps.USER_ORG)
                job.meta[JobMetaKey.SUBMITTER_ROLE] = conn.get_prop(ConnProps.USER_ROLE)

                meta = job_def_manager.create(job.meta, data_bytes, fl_ctx)
                conn.append_string("Cloned job {} as: {}".format(job_id, meta.get(JobMetaKey.JOB_ID)))
        except Exception as e:
            conn.append_error("Exception occurred trying to clone job: " + str(e))
            return
        conn.append_success("")

    @staticmethod
    def _job_match(job_meta: Dict, id_prefix: str, name_prefix: str) -> bool:
        return ((not id_prefix) or job_meta.get("job_id").lower().startswith(id_prefix.lower())) and (
            (not name_prefix) or job_meta.get("name").lower().startswith(name_prefix.lower())
        )

    @staticmethod
    def _send_detail_list(conn: Connection, jobs: List[Job]):
        for job in jobs:
            JobCommandModule._set_duration(job)
            conn.append_string(json.dumps(job.meta, indent=4))

    @staticmethod
    def _send_summary_list(conn: Connection, jobs: List[Job]):

        table = Table(["Job ID", "Name", "Status", "Submit Time", "Run Duration"])
        for job in jobs:
            JobCommandModule._set_duration(job)
            table.add_row(
                [
                    job.meta.get(JobMetaKey.JOB_ID, ""),
                    CommandUtil.get_job_name(job.meta),
                    job.meta.get(JobMetaKey.STATUS, ""),
                    job.meta.get(JobMetaKey.SUBMIT_TIME_ISO, ""),
                    str(job.meta.get(JobMetaKey.DURATION, "N/A")),
                ]
            )

        writer = io.StringIO()
        table.write(writer)
        conn.append_string(writer.getvalue())

    @staticmethod
    def _set_duration(job):
        if job.meta.get(JobMetaKey.STATUS) == RunStatus.RUNNING.value:
            start_time = datetime.datetime.strptime(job.meta.get(JobMetaKey.START_TIME), "%Y-%m-%d %H:%M:%S.%f")
            duration = datetime.datetime.now() - start_time
            job.meta[JobMetaKey.DURATION] = str(duration)

    def submit_job(self, conn: Connection, args: List[str]):
        folder_name = args[1]
        zip_b64str = args[2]
        data_bytes = convert_legacy_zip(b64str_to_bytes(zip_b64str))
        engine = conn.app_ctx

        try:
            with engine.new_context() as fl_ctx:
                job_validator = JobMetaValidator()
                valid, error, meta = job_validator.validate(folder_name, data_bytes)
                if not valid:
                    conn.append_error(error)
                    return

                job_def_manager = engine.job_def_manager
                if not isinstance(job_def_manager, JobDefManagerSpec):
                    raise TypeError(
                        f"job_def_manager in engine is not of type JobDefManagerSpec, but got {type(job_def_manager)}"
                    )

                # set submitter info
                meta[JobMetaKey.SUBMITTER_NAME.value] = conn.get_prop(ConnProps.USER_NAME, "")
                meta[JobMetaKey.SUBMITTER_ORG.value] = conn.get_prop(ConnProps.USER_ORG, "")
                meta[JobMetaKey.SUBMITTER_ROLE.value] = conn.get_prop(ConnProps.USER_ROLE, "")

                meta = job_def_manager.create(meta, data_bytes, fl_ctx)
                conn.append_string("Submitted job: {}".format(meta.get(JobMetaKey.JOB_ID)))
        except Exception as e:
            conn.append_error("Exception occurred trying to submit job: " + str(e))
            return

        conn.append_success("")

    def _unzip_data(self, download_dir, job_data, job_id):
        job_id_dir = os.path.join(download_dir, job_id)
        if os.path.exists(job_id_dir):
            shutil.rmtree(job_id_dir)
        os.mkdir(job_id_dir)

        data_bytes = job_data[JobDataKey.JOB_DATA.value]
        job_dir = os.path.join(job_id_dir, "job")
        os.mkdir(job_dir)
        unzip_all_from_bytes(data_bytes, job_dir)

        workspace_bytes = job_data[JobDataKey.WORKSPACE_DATA.value]
        workspace_dir = os.path.join(job_id_dir, "workspace")
        os.mkdir(workspace_dir)
        if workspace_bytes is not None:
            unzip_all_from_bytes(workspace_bytes, workspace_dir)

    def download_job(self, conn: Connection, args: List[str]):
        job_id = args[1]
        download_dir = conn.get_prop(ConnProps.DOWNLOAD_DIR)
        download_job_url = conn.get_prop(ConnProps.DOWNLOAD_JOB_URL)

        engine = conn.app_ctx
        try:
            job_def_manager = engine.job_def_manager
            if not isinstance(job_def_manager, JobDefManagerSpec):
                raise TypeError(
                    f"job_def_manager in engine is not of type JobDefManagerSpec, but got {type(job_def_manager)}"
                )
            with engine.new_context() as fl_ctx:
                job_data = job_def_manager.get_job_data(job_id, fl_ctx)
                size = get_size(job_data, seen=None)
                if size > MAX_DOWNLOAD_JOB_SIZE:
                    conn.append_string(ftd.DOWNLOAD_URL_MARKER + download_job_url + job_id)
                    return

                self._unzip_data(download_dir, job_data, job_id)
        except Exception as e:
            conn.append_error("Exception occurred trying to get job from store: " + str(e))
            return
        try:
            data = zip_directory_to_bytes(download_dir, job_id)
            b64str = bytes_to_b64str(data)
            conn.append_string(b64str)
        except FileNotFoundError:
            conn.append_error("No record found for job '{}'".format(job_id))
        except BaseException:
            traceback.print_exc()
            conn.append_error("Exception occurred during attempt to zip data to send for job: {}".format(job_id))
