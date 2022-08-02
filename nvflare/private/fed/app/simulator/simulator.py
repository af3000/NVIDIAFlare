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

"""Federated server launching script."""

import argparse
import logging
import logging.config
import os
import shutil
import sys

from nvflare.apis.fl_constant import WorkspaceConstants
from nvflare.fuel.hci.server.authz import AuthorizationService
from nvflare.fuel.hci.zip_utils import split_path, zip_directory_to_bytes
from nvflare.fuel.sec.audit import AuditService
from nvflare.private.defs import AppFolderConstants
from nvflare.private.fed.app.deployer.simulator_deployer import SimulatorDeploy
from nvflare.private.fed.app.simulator.simulator_runner import SimulatorRunner
from nvflare.private.fed.server.job_meta_validator import JobMetaValidator
from nvflare.security.security import EmptyAuthorizer


def main():
    if sys.version_info >= (3, 9):
        raise RuntimeError("Python versions 3.9 and above are not yet supported. Please use Python 3.8 or 3.7.")
    if sys.version_info < (3, 7):
        raise RuntimeError("Python versions 3.6 and below are not supported. Please use Python 3.8 or 3.7.")
    parser = argparse.ArgumentParser()
    parser.add_argument("job_folder")
    parser.add_argument("--data_path", "-i", type=str, help="Input data_path")
    parser.add_argument("--workspace", "-m", type=str, help="WORKSPACE folder", required=True)
    parser.add_argument("--clients", "-n", type=int, help="number of clients")
    parser.add_argument("--client_file", "-f", type=str, help="client names file")
    parser.add_argument("--threads", "-t", type=int, help="number of running threads", required=True)

    parser.add_argument("--set", metavar="KEY=VALUE", nargs="*")

    args = parser.parse_args()

    client_names = []
    if args.client_file:
        with open(args.client_file, "r") as f:
            client_names = f.read().split()
    elif args.clients:
        for i in range(args.clients):
            client_names.append("client" + str(i))
    else:
        logging.error("Please provide a simulate client names file, or the number of clients")
        sys.exit()

    if args.threads > len(client_names):
        logging.error("The number of threads to run can not be larger then the number of clients.")
        sys.exit(-1)

    log_config_file_path = os.path.join(args.workspace, "startup", "log.config")
    assert os.path.isfile(log_config_file_path), "missing log config file {}".format(log_config_file_path)
    logging.config.fileConfig(fname=log_config_file_path, disable_existing_loggers=False)

    logger = logging.getLogger()
    args.log_config = None
    args.config_folder = "config"
    args.job_id = "simulate_job"
    args.client_config = os.path.join(args.config_folder, "config_fed_client.json")
    args.env = os.path.join("config", AppFolderConstants.CONFIG_ENV)

    os.chdir(args.workspace)
    AuthorizationService.initialize(EmptyAuthorizer())
    AuditService.initialize(audit_file_name=WorkspaceConstants.AUDIT_LOG)

    simulator_root = os.path.join(args.workspace, "simulate_job")
    if os.path.exists(simulator_root):
        shutil.rmtree(simulator_root)

    deployer = SimulatorDeploy()
    federated_clients = []

    try:
        # Validate the simulate job
        job_name = split_path(args.job_folder)[1]
        data_bytes = zip_directory_to_bytes("", args.job_folder)
        job_validator = JobMetaValidator()
        valid, error, _ = job_validator.validate(job_name, data_bytes)
        if not valid:
            raise RuntimeError(error)

        # Deploy the FL server
        logger.info("Create the Simulator Server.")
        simulator_server, services = deployer.create_fl_server(args)
        services.deploy(args, grpc_args=simulator_server)

        # Deploy the FL clients
        logger.info("Create the simulate clients.")
        for client_name in client_names:
            federated_clients.append(deployer.create_fl_client(client_name, args))

        logger.info("Start the Simulator Run.")
        simulator_runner = SimulatorRunner()
        simulator_runner.run(simulator_root, args, logger, services, federated_clients)

    except BaseException as error:
        logger.error(error)
    finally:
        for client in federated_clients:
            client.engine.shutdown()
        deployer.close()

    logger.info("Simulator run completed.")


if __name__ == "__main__":
    """
    This is the main program when starting the NVIDIA FLARE server process.
    """

    main()
    os._exit(0)

