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

"""FL Server deployer."""
import threading

from nvflare.apis.workspace import Workspace
from nvflare.private.fed.server.fed_server import FederatedServer
from nvflare.private.fed.server.job_runner import JobRunner
from nvflare.private.fed.server.run_manager import RunManager
from nvflare.private.fed.server.server_cmd_modules import ServerCommandModules


class ServerDeployer:
    """FL Server deployer."""

    def __init__(self):
        """Init the ServerDeployer."""
        # self.app_validator = None
        self.services = None
        self.cmd_modules = ServerCommandModules.cmd_modules

    def build(self, build_ctx):
        """To build the ServerDeployer.

        Args:
            build_ctx: build context

        """
        self.server_config = build_ctx["server_config"]
        self.secure_train = build_ctx["secure_train"]
        self.app_validator = build_ctx["app_validator"]
        self.host = build_ctx["server_host"]
        self.enable_byoc = build_ctx["enable_byoc"]
        self.snapshot_persistor = build_ctx["snapshot_persistor"]
        self.overseer_agent = build_ctx["overseer_agent"]

        self.components = build_ctx.get("server_components", {})

    def train(self):
        """To start the ServerDeployer."""
        self.services = self.deploy()
        self.start_training(self.services)

    def start_training(self, services):
        """Start the deployemnt."""
        services.start()

    def create_fl_server(self, args, secure_train=False):
        """To create the FL Server.

        Args:
            args: command args
            secure_train: True/False

        Returns: FL Server

        """
        # We only deploy the first server right now .....
        first_server = sorted(self.server_config)[0]
        wait_after_min_clients = first_server.get("wait_after_min_clients", 10)
        heart_beat_timeout = 600
        if first_server["heart_beat_timeout"]:
            heart_beat_timeout = first_server["heart_beat_timeout"]

        if self.host:
            target = first_server["service"].get("target", None)
            first_server["service"]["target"] = self.host + ":" + target.split(":")[1]

        services = FederatedServer(
            project_name=first_server.get("name", ""),
            min_num_clients=first_server.get("min_num_clients", 1),
            max_num_clients=first_server.get("max_num_clients", 100),
            wait_after_min_clients=wait_after_min_clients,
            cmd_modules=self.cmd_modules,
            heart_beat_timeout=heart_beat_timeout,
            args=args,
            secure_train=secure_train,
            enable_byoc=self.enable_byoc,
            snapshot_persistor=self.snapshot_persistor,
            overseer_agent=self.overseer_agent,
        )
        return first_server, services

    def deploy(self, args):
        """To deploy the FL server services.

        Args:
            args: command args.

        Returns: FL Server

        """
        first_server, services = self.create_fl_server(args, secure_train=self.secure_train)
        services.deploy(args, grpc_args=first_server, secure_train=self.secure_train)

        # self._start_job_runner(args, services)
        threading.Thread(target=self._start_job_runner, args=[services, args]).start()

        # self.create_builder(services)
        print("deployed FL server trainer.")
        return services

    def _start_job_runner(self, services, args):
        job_runner = JobRunner(workspace_root=args.workspace)
        workspace = Workspace(args.workspace, "server", args.config_folder)
        run_manager = RunManager(
            server_name=services.project_name,
            engine=services.engine,
            run_num="",
            workspace=workspace,
            components=self.components,
            # client_manager=self.client_manager,
            handlers=[],
        )
        services.engine.set_run_manager(run_manager)
        services.engine.set_job_runner(job_runner)
        fl_ctx = services.engine.new_context()
        job_runner.run(fl_ctx)

    def close(self):
        """To close the services."""
        if self.services:
            self.services.close()
