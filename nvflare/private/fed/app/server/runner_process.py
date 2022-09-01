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

"""Provides a command line interface for federated server."""

import argparse
import logging
import os

from nvflare.apis.fl_constant import MachineStatus
from nvflare.apis.workspace import Workspace
from nvflare.fuel.common.excepts import ConfigError
from nvflare.fuel.sec.audit import AuditService
from nvflare.fuel.sec.security_content_service import SecurityContentService
from nvflare.fuel.utils.argument_utils import parse_vars
from nvflare.private.defs import AppFolderConstants
from nvflare.private.fed.app.fl_conf import FLServerStarterConfiger, create_privacy_manager
from nvflare.private.fed.server.collective_command_agent import CollectiveCommandAgent
from nvflare.private.fed.server.server_app_runner import ServerAppRunner
from nvflare.private.fed.server.server_command_agent import ServerCommandAgent
from nvflare.private.fed.server.server_engine import ServerEngine
from nvflare.private.fed.server.server_json_config import ServerJsonConfigurator
from nvflare.private.fed.server.server_runner import ServerRunnerConfig
from nvflare.private.fed.server.server_status import ServerStatus
from nvflare.private.fed.utils.fed_utils import add_logfile_handler
from nvflare.private.privacy_manager import PrivacyService


def main():
    """FL Server program starting point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", "-m", type=str, help="WORKSPACE folder", required=True)
    parser.add_argument(
        "--fed_server", "-s", type=str, help="an aggregation server specification json file", required=True
    )
    parser.add_argument("--app_root", "-r", type=str, help="App Root", required=True)
    parser.add_argument("--job_id", "-n", type=str, help="job id", required=True)
    parser.add_argument("--port", "-p", type=str, help="listen port", required=True)
    parser.add_argument("--collective_command_port", type=str, help="collective command listen port", required=True)
    parser.add_argument("--conn", "-c", type=str, help="connection port", required=True)

    parser.add_argument("--set", metavar="KEY=VALUE", nargs="*")

    args = parser.parse_args()
    kv_list = parse_vars(args.set)

    config_folder = kv_list.get("config_folder", "")
    if config_folder == "":
        args.server_config = AppFolderConstants.CONFIG_FED_SERVER
    else:
        args.server_config = os.path.join(config_folder, AppFolderConstants.CONFIG_FED_SERVER)

    # TODO:: remove env and train config since they are not core
    args.env = os.path.join("config", AppFolderConstants.CONFIG_ENV)
    args.config_folder = config_folder
    args.log_config = None
    args.snapshot = kv_list.get("restore_snapshot")

    workspace = Workspace(root_dir=args.workspace, site_name="server")

    command_agent = None
    collective_command_agent = None
    try:
        os.chdir(args.workspace)
        SecurityContentService.initialize(content_folder=workspace.get_startup_kit_dir())

        # Initialize audit service since the job execution will need it!
        audit_file_name = workspace.get_audit_file_path()
        AuditService.initialize(audit_file_name)

        conf = FLServerStarterConfiger(
            workspace=workspace,
            kv_list=args.set,
        )
        log_file = workspace.get_app_log_file_path(args.job_id)
        add_logfile_handler(log_file)
        logger = logging.getLogger("runner_process")
        logger.info("Runner_process started.")

        log_level = os.environ.get("FL_LOG_LEVEL", "")
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logging.getLogger().setLevel(numeric_level)
            logger.debug("loglevel debug enabled")
            logger.info("loglevel info enabled")
            logger.warning("loglevel warn enabled")
            logger.error("loglevel error enabled")
            logger.critical("loglevel critical enabled")

        conf.configure()

        deployer = conf.deployer
        secure_train = conf.cmd_vars.get("secure_train", False)

        try:
            # create the FL server
            _, server = deployer.create_fl_server(args, secure_train=secure_train)

            command_agent = ServerCommandAgent(int(args.port))
            command_agent.start(server.engine)

            collective_command_agent = CollectiveCommandAgent(int(args.collective_command_port))
            collective_command_agent.start(server.engine)

            snapshot = None
            if args.snapshot:
                snapshot = server.snapshot_persistor.retrieve_run(args.job_id)

            server_app_runner = ServerAppRunner()
            server_app_runner.start_server_app(server, args, args.app_root, args.job_id, snapshot, logger)
        finally:
            if command_agent:
                command_agent.shutdown()
            if collective_command_agent:
                collective_command_agent.shutdown()
            if deployer:
                deployer.close()
            AuditService.close()

    except ConfigError as ex:
        logger.exception(f"ConfigError: {ex}", exc_info=True)
        raise ex


def start_server_app(workspace: Workspace, server, args, app_root, job_id, snapshot, logger):

    try:
        server_config_file_name = os.path.join(app_root, args.server_config)

        conf = ServerJsonConfigurator(
            config_file_name=server_config_file_name,
        )
        conf.configure()

        set_up_run_config(workspace, server, conf)

        if not isinstance(server.engine, ServerEngine):
            raise TypeError(f"server.engine must be ServerEngine. Got type:{type(server.engine).__name__}")
        server.engine.create_parent_connection(int(args.conn))
        server.engine.sync_clients_from_main_process()

        server.start_run(job_id, app_root, conf, args, snapshot)
    except BaseException as e:
        logger.exception(f"FL server execution exception: {e}", exc_info=True)
        raise e
    finally:
        server.status = ServerStatus.STOPPED
        server.engine.engine_info.status = MachineStatus.STOPPED
        server.stop_training()


def set_up_run_config(workspace: Workspace, server, conf):
    runner_config = conf.runner_config
    assert isinstance(runner_config, ServerRunnerConfig)

    # configure privacy control!
    privacy_manager = create_privacy_manager(workspace, names_only=False)
    if privacy_manager.is_policy_defined():
        if privacy_manager.components:
            for cid, comp in privacy_manager.components.items():
                runner_config.add_component(cid, comp)

    # initialize Privacy Service
    PrivacyService.initialize(privacy_manager)
    server.heart_beat_timeout = conf.heartbeat_timeout
    server.runner_config = runner_config
    server.handlers = runner_config.handlers


if __name__ == "__main__":
    """
    This is the program when starting the child process for running the NVIDIA FLARE server runner.
    """
    main()
