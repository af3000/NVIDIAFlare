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

import argparse, os

from nvflare.fuel.common.excepts import ConfigError

from nvflare.fuel.hci.client.cli import AdminClient, CredentialType
from nvflare.fuel.hci.client.file_transfer import FileTransferModule
from nvflare.private.fed.app.fl_conf import FLAdminClientStarterConfigurator


def main():
    """
    Script to launch the admin client to issue admin commands to the server.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", "-m", type=str, help="WORKSPACE folder", required=True)

    parser.add_argument(
        "--fed_admin", "-s", type=str, help="json file with configurations for launching admin client", required=True
    )
    parser.add_argument("--upload_folder_cmd_name", type=str, default="upload_app")
    parser.add_argument("--cli_history_size", type=int, default=1000)
    parser.add_argument("--with_debug", action="store_true")

    args = parser.parse_args()

    try:
        os.chdir(args.workspace)
        workspace = os.path.join(args.workspace, "startup")

        conf = FLAdminClientStarterConfigurator(
            app_root=workspace,
            admin_config_file_name=args.fed_admin
        )
        conf.configure()

        # stuff for admin launching maybe?

    except ConfigError as ex:
        print("ConfigError:", str(ex))

    admin_config = conf.config_data["admin"]
    modules = []

    if admin_config["with_file_transfer"]:
        modules.append(
            FileTransferModule(
                upload_dir=admin_config["upload_dir"],
                download_dir=admin_config["download_dir"],
                upload_folder_cmd_name=args.upload_folder_cmd_name,
            )
        )

    ca_cert = admin_config["ca_cert"]
    client_cert = admin_config["client_cert"]
    client_key = admin_config["client_key"]

    if admin_config["with_ssl"]:
        if len(ca_cert) <= 0:
            print("missing CA Cert file name field ca_cert in fed_admin configuration")
            return

        if len(client_cert) <= 0:
            print("missing Client Cert file name field client_cert in fed_admin configuration")
            return

        if len(client_key) <= 0:
            print("missing Client Key file name field client_key in fed_admin configuration")
            return
    else:
        ca_cert = None
        client_key = None
        client_cert = None

    if args.with_debug:
        print("SSL: {}".format(admin_config["with_ssl"]))
        print("File Transfer: {}".format(admin_config["with_file_transfer"]))

        if admin_config["with_file_transfer"]:
            print("  Upload Dir: {}".format(admin_config["upload_dir"]))
            print("  Download Dir: {}".format(admin_config["download_dir"]))

    client = AdminClient(
        prompt=admin_config["prompt"],
        cmd_modules=modules,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=client_key,
        require_login=admin_config["with_login"],
        credential_type=CredentialType.PASSWORD if admin_config["cred_type"] == "password" else CredentialType.CERT,
        debug=args.with_debug,
        overseer_end_point=admin_config["overseer_agent"]["args"]["overseer_end_point"],
        project=admin_config["overseer_agent"]["args"]["project"],
        name=admin_config["overseer_agent"]["args"]["name"],
        # cli_history_size=args.cli_history_size,
    )

    client.run()


if __name__ == "__main__":
    main()
