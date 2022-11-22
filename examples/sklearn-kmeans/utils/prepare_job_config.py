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

import argparse
import json
import os
import pathlib
import shutil

from nvflare.apis.fl_constant import JobConstants

JOB_CONFIGS_ROOT = "job_configs"
BASE_FOLDER = "sklearn_kmeans_base"


def job_config_args_parser():
    parser = argparse.ArgumentParser(description="generate train configs for HIGGS dataset")
    parser.add_argument(
        "--data_split_root",
        type=str,
        default="/tmp/nvflare/iris_dataset",
        help="Path to dataset config files for each site",
    )
    parser.add_argument("--site_num", type=int, default=5, help="Total number of sites")
    parser.add_argument("--site_name_prefix", type=str, default="site-", help="Site name prefix")
    parser.add_argument("--split_method", type=str, default="uniform", help="How to split the dataset")
    return parser


def _read_json(filename):
    if not os.path.isfile(filename):
        raise ValueError(f"{filename} does not exist!")
    with open(filename, "r") as f:
        return json.load(f)


def _write_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def _get_job_name(args) -> str:
    return "iris_" + str(args.site_num) + "_" + args.split_method


def _get_data_split_name(args, site_name: str) -> str:
    return os.path.join(args.data_split_root, f"{args.site_num}_{args.split_method}", f"data_{site_name}.json")


def _gen_deploy_map(num_sites: int, site_name_prefix: str) -> dict:
    deploy_map = {"app_server": ["server"]}
    for i in range(1, num_sites + 1):
        deploy_map[f"app_{site_name_prefix}{i}"] = [f"{site_name_prefix}{i}"]
    return deploy_map


def _update_meta(meta: dict, args):
    name = _get_job_name(args)
    meta["name"] = name
    meta["deploy_map"] = _gen_deploy_map(args.site_num, args.site_name_prefix)
    meta["min_clients"] = args.site_num


def _update_client_config(config: dict, args, site_name: str):
    data_split_name = _get_data_split_name(args, site_name)
    # update client config
    config["executors"][0]["executor"]["args"]["data_split_filename"] = data_split_name


def _update_server_config(config: dict, args):
    config["workflows"][0]["args"]["min_clients"] = args.site_num


def _copy_custom_files(src_job_path, src_app_name, dst_job_path, dst_app_name):
    dst_path = dst_job_path / dst_app_name / "custom"
    os.makedirs(dst_path, exist_ok=True)
    src_path = src_job_path / src_app_name / "custom"
    if os.path.isdir(src_path):
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)


def create_server_app(src_job_path, src_app_name, dst_job_path, site_name, args):
    dst_app_name = f"app_{site_name}"
    server_config = _read_json(src_job_path / src_app_name / "config" / JobConstants.SERVER_JOB_CONFIG)
    dst_config_path = dst_job_path / dst_app_name / "config"

    # make target config folders
    if not os.path.exists(dst_config_path):
        os.makedirs(dst_config_path)

    _update_server_config(server_config, args)
    server_config_filename = dst_config_path / JobConstants.SERVER_JOB_CONFIG
    _write_json(server_config, server_config_filename)

    # copy custom file
    _copy_custom_files(src_job_path, src_app_name, dst_job_path, dst_app_name)


def create_client_app(src_job_path, src_app_name, dst_job_path, site_name, args):
    dst_app_name = f"app_{site_name}"
    client_config = _read_json(src_job_path / src_app_name / "config" / JobConstants.CLIENT_JOB_CONFIG)
    dst_config_path = dst_job_path / dst_app_name / "config"

    # make target config folders
    if not os.path.exists(dst_config_path):
        os.makedirs(dst_config_path)

    # get lr scale
    data_split_name = _get_data_split_name(args, site_name)
    data_split = _read_json(data_split_name)

    # adjust file contents according to each job's specs
    _update_client_config(client_config, args, site_name)
    client_config_filename = dst_config_path / JobConstants.CLIENT_JOB_CONFIG
    _write_json(client_config, client_config_filename)

    # copy custom file
    _copy_custom_files(src_job_path, src_app_name, dst_job_path, dst_app_name)


def main():
    parser = job_config_args_parser()
    args = parser.parse_args()
    job_name = _get_job_name(args)
    src_job_path = pathlib.Path(JOB_CONFIGS_ROOT) / BASE_FOLDER

    # create a new job
    dst_job_path = pathlib.Path(JOB_CONFIGS_ROOT) / job_name
    if not os.path.exists(dst_job_path):
        os.makedirs(dst_job_path)

    # update meta
    meta_config_dst = dst_job_path / JobConstants.META_FILE
    meta_config = _read_json(src_job_path / JobConstants.META_FILE)
    _update_meta(meta_config, args)
    _write_json(meta_config, meta_config_dst)

    # create server side app
    create_server_app(
        src_job_path=src_job_path, src_app_name="app", dst_job_path=dst_job_path, site_name="server", args=args
    )

    # create client side app
    for i in range(1, args.site_num + 1):
        create_client_app(
            src_job_path=src_job_path,
            src_app_name="app",
            dst_job_path=dst_job_path,
            site_name=f"{args.site_name_prefix}{i}",
            args=args,
        )


if __name__ == "__main__":
    main()
