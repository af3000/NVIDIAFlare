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

import json
import logging
import os
from typing import List

from nvflare.fuel.hci.client.api_status import APIStatus
from nvflare.fuel.hci.conn import Connection
from nvflare.fuel.hci.reg import CommandModule, CommandModuleSpec, CommandSpec
from nvflare.fuel.hci.zip_utils import unzip_all_from_bytes
from nvflare.mt.job_def import JobMetaKey


class JobCommandModule(CommandModule):
    """Command module with commands for job management."""

    def __init__(self, upload_dir: str, download_dir: str):  # , job_def_manager: JobDefManagerSpec):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not os.path.isdir(upload_dir):
            raise ValueError("upload_dir {} is not a valid dir".format(upload_dir))

        if not os.path.isdir(download_dir):
            raise ValueError("download_dir {} is not a valid dir".format(download_dir))

        self.upload_dir = upload_dir
        self.download_dir = download_dir

    def get_spec(self):
        return CommandModuleSpec(
            name="job_mgmt",
            cmd_specs=[
                CommandSpec(
                    name="list_all_jobs",
                    description="list all job defs",
                    usage="list_all_jobs",
                    handler_func=self.list_all_jobs,
                ),
                CommandSpec(
                    name="get_job_details",
                    description="get the details for a job",
                    usage="get_job_details job_id",
                    handler_func=self.get_job_details,
                ),
                CommandSpec(
                    name="delete_job",
                    description="delete a job",
                    usage="delete_job job_id",
                    handler_func=self.delete_job,
                ),
                CommandSpec(
                    name="abort_job",
                    description="abort a job if it is running or dispatched",
                    usage="abort_job job_id",
                    handler_func=self.abort_job,  # see if running, if running, send abort command
                ),
                CommandSpec(
                    name="clone_job",
                    description="clone a job with a new job_id",
                    usage="clone_job job_id",
                    handler_func=self.clone_job,
                ),
            ],
        )

    def list_all_jobs(self, conn: Connection, args: List[str]):
        engine = conn.app_ctx
        jobs = engine.job_def_manager.list_all()
        if jobs:
            conn.append_string("Jobs:")
            for job in jobs:
                conn.append_string(job.job_id)
            conn.append_string("\nJob details for each job:")
            for job in jobs:
                conn.append_string(json.dumps(job.meta, indent=4))
        conn.append_success("")

    def get_job_details(self, conn: Connection, args: List[str]):
        if len(args) != 2:
            conn.append_error("syntax error: usage: get_job_details job_id")
        job_id = args[1]
        engine = conn.app_ctx
        try:
            job = engine.job_def_manager.get_job(job_id)
            job_meta = job.meta
            conn.append_string(json.dumps(job_meta, indent=4))
        except Exception as e:
            conn.append_error("exception occurred getting job details: " + str(e))
            return

    def delete_job(self, conn: Connection, args: List[str]):
        if len(args) != 2:
            conn.append_error("syntax error: usage: delete_job job_id")
        job_id = args[1]
        engine = conn.app_ctx
        try:
            engine.job_def_manager.delete(job_id)
            conn.append_string("Job {} deleted.".format(job_id))
        except Exception as e:
            conn.append_error("exception occurred: " + str(e))
            return
        conn.append_success("")

    def abort_job(self, conn: Connection, args: List[str]):
        pass

    def clone_job(self, conn: Connection, args: List[str]):
        pass
