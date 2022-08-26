# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
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

import argparse
import os
import signal

import docker
import requests

from nvflare.lighter.utils import generate_password


def start(port, folder, app_url, app_dest_filename, dashboard_image):
    if not folder:
        folder = os.getcwd()
    environment = dict()
    if not os.path.exists(os.path.join(folder, "db.sqlite")):
        answer = input(
            f"Please provide project admin email address.  This person will be the super user of the dashboard and this project.\n"
        )
        print("generating random password")
        pwd = generate_password(8)
        print(f"Project admin credential is {answer} and the password is {pwd}")
        environment.update({"NVFL_CREDENTIAL": f"{answer}:{pwd}"})
    if app_url and app_dest_filename:
        images_folder = os.path.join(folder, "images")
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)
        dest_file = os.path.join(images_folder, app_dest_filename)
        print(f"downloding {app_url} to {dest_file}")
        with open(dest_file, "wb") as out_file:
            content = requests.get(app_url, stream=True).content
            out_file.write(content)
    client = docker.from_env()
    try:
        container_obj = client.containers.run(
            dashboard_image,
            entrypoint=["/usr/local/bin/python3", "nvflare/web/wsgi.py"],
            detach=True,
            auto_remove=True,
            name="nvflare-dashboard",
            ports={8443: port},
            volumes={folder: {"bind": "/var/tmp/nvflare/web", "model": "rw"}},
            environment=environment,
        )
    except docker.errors.APIError as e:
        print(f"Either {dashboard_image} image does not exist or another nvflare-dashboard instance is still running.")
        print("Please either provide an existing container image or stop the running container instance.")
        print(e)
        exit(1)
    if container_obj:
        print(f"Dashboard container started")
        print("Container name nvflare-dashboard")
        print(f"id is {container_obj.id}")
    else:
        print("Container failed to start")


def stop():
    client = docker.from_env()
    try:
        container_obj = client.containers.get("nvflare-dashboard")
    except docker.errors.NotFound:
        print("No nvflare-dashboard container found")
        exit(0)
    container_obj.kill(signal=signal.SIGINT)
    print("nvflare-dashboard exited")


def dashboard():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true", help="start dashboard")
    parser.add_argument("--stop", action="store_true", help="stop dashboard")
    parser.add_argument("-p", "--port", type=str, default="443", help="port to listen")
    parser.add_argument(
        "-f", "--folder", type=str, help="folder containing necessary info (default: current working directory)"
    )
    parser.add_argument(
        "-u",
        "--app_url",
        help="URL of the application.  The application will be copied to the folder available to dashboard to run.",
    )
    parser.add_argument("-d", "--app_dest_filename", type=str, help="filename of downloaded application")
    parser.add_argument(
        "-i", "--dashboard_image", default="nvflare/nvflare", help="container image for running dashboard"
    )
    args = parser.parse_args()
    port = args.port
    folder = args.folder
    app_url = args.app_url
    app_dest_filename = args.app_dest_filename
    dashboard_image = args.dashboard_image
    if args.stop:
        stop()
    elif args.start:
        start(port, folder, app_url, app_dest_filename, dashboard_image)


if __name__ == "__main__":
    dashboard()
