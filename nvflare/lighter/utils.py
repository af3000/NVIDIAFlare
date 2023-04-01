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
import os
import random
import shutil
import time
from base64 import b64decode, b64encode
from typing import List

import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from nvflare.fuel.flare_api.api_spec import JobNotFound, NoConnection
from nvflare.fuel.flare_api.flare_api import Session, new_secure_session, new_insecure_session
from nvflare.lighter.impl.cert import load_crt


def generate_password(passlen=16):
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    p = "".join(random.sample(s, passlen))
    return p


def sign_one(content, signing_pri_key):
    signature = signing_pri_key.sign(
        data=content,
        padding=padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        algorithm=hashes.SHA256(),
    )
    return b64encode(signature).decode("utf-8")


def load_private_key_file(file_path):
    with open(file_path, "rt") as f:
        pri_key = serialization.load_pem_private_key(f.read().encode("ascii"), password=None, backend=default_backend())
    return pri_key


def sign_folders(folder, signing_pri_key, crt_path):
    for root, folders, files in os.walk(folder):
        signatures = dict()
        for file in files:
            if file == ".__nvfl_sig.json":
                continue
            signature = signing_pri_key.sign(
                data=open(os.path.join(root, file), "rb").read(),
                padding=padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                algorithm=hashes.SHA256(),
            )
            signatures[file] = b64encode(signature).decode("utf-8")
        for folder in folders:
            signature = signing_pri_key.sign(
                data=folder.encode("utf-8"),
                padding=padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                algorithm=hashes.SHA256(),
            )
            signatures[folder] = b64encode(signature).decode("utf-8")
        json.dump(signatures, open(os.path.join(root, ".__nvfl_sig.json"), "wt"))
        shutil.copyfile(crt_path, os.path.join(root, ".__nvfl_submitter.crt"))


def verify_folder_signature(folder):
    try:
        for root, folders, files in os.walk(folder):
            try:
                signatures = json.load(open(os.path.join(root, ".__nvfl_sig.json"), "rt"))
                cert = load_crt(os.path.join(root, ".__nvfl_submitter.crt"))
                public_key = cert.public_key()
            except:
                continue
            for k in signatures:
                signatures[k] = b64decode(signatures[k].encode("utf-8"))
            for file in files:
                if file == ".__nvfl_sig.json" or file == ".__nvfl_submitter.crt":
                    continue
                signature = signatures.get(file)
                if signature:
                    public_key.verify(
                        signature=signature,
                        data=open(os.path.join(root, file), "rb").read(),
                        padding=padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                        algorithm=hashes.SHA256(),
                    )
            for folder in folders:
                signature = signatures.get(folder)
                if signature:
                    public_key.verify(
                        signature=signature,
                        data=folder.encode("utf-8"),
                        padding=padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                        algorithm=hashes.SHA256(),
                    )
        return True
    except BaseException as e:
        return False


def sign_all(content_folder, signing_pri_key):
    signatures = dict()
    for f in os.listdir(content_folder):
        path = os.path.join(content_folder, f)
        if os.path.isfile(path):
            signature = signing_pri_key.sign(
                data=open(path, "rb").read(),
                padding=padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                algorithm=hashes.SHA256(),
            )
            signatures[f] = b64encode(signature).decode("utf-8")
    return signatures


def load_yaml(file):
    if isinstance(file, str):
        return yaml.safe_load(open(file, "r"))
    elif isinstance(file, bytes):
        return yaml.safe_load(file)
    else:
        return None


def sh_replace(src, mapping_dict):
    result = src
    for k, v in mapping_dict.items():
        result = result.replace("{~~" + k + "~~}", str(v))
    return result


def update_project_config(project_config: dict, old_server_name, server_name) -> dict:
    if project_config:
        # update participants
        participants = project_config["participants"]
        for p in participants:
            if p["name"] == old_server_name:
                p["name"] = server_name

        # update overseer_agent builder
        builders = project_config["builders"]
        for b in builders:
            if "args" in b:
                if "overseer_agent" in b["args"]:
                    end_point = b["args"]["overseer_agent"]["args"]["sp_end_point"]
                    new_end_point = end_point.replace(old_server_name, server_name)
                    b["args"]["overseer_agent"]["args"]["sp_end_point"] = new_end_point
    else:
        RuntimeError("project_config is empty")
    return project_config


def update_project_server_name(project_file: str, old_server_name, server_name):
    with open(project_file, "r") as file:
        project_config = yaml.safe_load(file)

    update_project_config(project_config, old_server_name, server_name)

    with open(project_file, "w") as file:
        yaml.dump(project_config, file)


def update_storage_locations(
        local_dir: str,
        workspace: str,
        default_resource_name: str = "resources.json.default",
        job_storage_name: str = "jobs-storage",
        snapshot_storage_name: str = "snapshot-storage",
):
    default_resource = f"{local_dir}/{default_resource_name}"
    target_resource = f"{local_dir}/resources.json"
    job_storage = f"{workspace}/{job_storage_name}"
    snapshot_storage = f"{workspace}/{snapshot_storage_name}"

    # load resources.json
    with open(default_resource, "r") as f:
        resources = json.load(f)

    # update resources
    resources["snapshot_persistor"]["args"]["storage"]["args"]["root_dir"] = snapshot_storage
    components = resources["components"]
    job_mgr_comp = [comp for comp in components if comp["id"] == "job_manager"][0]
    job_mgr_comp["args"]["uri_root"] = job_storage

    # Serializing json, Writing to resources.json
    json_object = json.dumps(resources, indent=4)
    with open(target_resource, "w") as outfile:
        outfile.write(json_object)


def shutdown_prod_system(prod_dir: str, username: str, timeout_in_sec: int = 30):
    admin_user_dir = os.path.join(prod_dir, username)
    print("connect to nvflare server")
    sess = None
    try:
        sess = new_secure_session(username=username, startup_kit_location=admin_user_dir)
        shutdown_system_by_session(sess=sess, timeout_in_sec=timeout_in_sec)
    except NoConnection:
        # system is already shutdown
        return
    finally:
        if sess:
            sess.close()


def shutdown_poc_system(poc_workspace: str, timeout_in_sec: int = 30):
    admin_dir = os.path.join(poc_workspace, "admin")
    print("connect to nvflare server")
    sess = None
    try:
        sess = new_insecure_session(admin_dir)
        shutdown_system_by_session(sess=sess, timeout_in_sec=timeout_in_sec)
    except NoConnection:
        # system is already shutdown
        return
    except Exception as e:
        print("failure", e)
    finally:
        if sess:
            sess.close()


def shutdown_system_by_session(sess: Session, timeout_in_sec: int = 20):
    print("checking running jobs")
    jobs = sess.list_jobs()
    active_job_ids = get_running_job_ids(jobs)
    if len(active_job_ids) > 0:
        print("Warning: current running jobs will be aborted")
        abort_jobs(sess, active_job_ids)
    print("shutdown NVFLARE")
    sess.api.do_command("shutdown all")
    wait_for_system_shutdown(sess, timeout_in_sec=timeout_in_sec)


def get_running_job_ids(jobs: list) -> List[str]:
    if len(jobs) > 0:
        running_job_ids = [job for job in jobs if job["status"] == "RUNNING"]
        return running_job_ids
    else:
        return []


def abort_jobs(sess, job_ids):
    for job_id in job_ids:
        try:
            sess.abort_job(job_id)
        except JobNotFound:
            # ignore invalid job id
            pass


def wait_for_system_shutdown(sess: Session, timeout_in_sec: int = 30):
    start = time.time()
    duration = 0
    cnt = 0
    status = None
    while (status is None or status == "started") and duration < timeout_in_sec:
        try:
            print("trying to connect to NVFLARE server")
            sys_info = sess.get_system_info()
            status = sys_info.server_info.status
            curr = time.time()
            duration = curr - start
            if cnt % 25 == 0:
                print("waiting system to shutdown")
            cnt += 1
            time.sleep(0.1)
        except BaseException:
            # Server is already shutdown
            return


def get_system_info(sess: Session, num_clients: int, second_to_wait: int = 20) -> bool:
    print(f"wait for {second_to_wait} seconds before FL system is up")
    time.sleep(second_to_wait)
    # just in case try to connect before server started
    flare_not_ready = True
    while flare_not_ready:
        print("trying to connect to server")
        try:
            sys_info = sess.get_system_info()
            print(f"Server info:\n{sys_info.server_info}")
            print("\nClient info")
            for client in sys_info.client_info:
                print(client)
            flare_not_ready = len(sys_info.client_info) < num_clients

            time.sleep(2)
        except BaseException:
            # system is not ready
            pass

    if flare_not_ready:
        print("can't not connect to server")
        return False
    else:
        print("ready to go")
        return True


def test_prod_connection(prod_dir: str, username: str, num_clients: int):
    admin_user_dir = os.path.join(prod_dir, username)
    sess = None
    try:
        sess = new_secure_session(username=username, startup_kit_location=admin_user_dir)
        if not get_system_info(sess=sess, num_clients=num_clients):
            raise ValueError("can't connect to FL system")
    except NoConnection:
        # system is already shutdown
        return
    except Exception as e:
        print("failure", e)
    finally:
        if sess:
            sess.close()


def test_poc_connection(prod_dir: str, num_clients: int):
    admin_user_dir = os.path.join(prod_dir, "admin")
    sess = None
    try:
        sess = new_insecure_session(admin_user_dir)
        if not get_system_info(sess=sess, num_clients=num_clients):
            raise ValueError("can't connect to FL system")
    except NoConnection:
        # system is already shutdown
        return
    except Exception as e:
        print("failure", e)
    finally:
        if sess:
            sess.close()

