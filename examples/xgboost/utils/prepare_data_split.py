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

import numpy as np


def data_split_args_parser():
    parser = argparse.ArgumentParser(description="generate data split for HIGGS dataset")
    parser.add_argument("--data_path", type=str, default="./dataset/HIGGS_UCI.csv", help="Path to data file")
    parser.add_argument("--site_num", type=int, default=5, help="Total number of sites")
    parser.add_argument("--site_name", type=str, default="site-", help="Site name prefix")
    parser.add_argument(
        "--size_total", type=int, default=11000000, help="Total number of instances, default 11 million"
    )
    parser.add_argument("--size_valid", type=int, default=1000000, help="Validation size, default 1 million")
    parser.add_argument("--split_method", type=str, default="uniform", help="How to split the dataset")
    parser.add_argument("--out_path", type=str, default="data_splits/data_split.json", help="Path to json file")
    return parser


def split_num_proportion(n, site_num, option: str):
    split = []
    if option == "uniform":
        ratio_vec = np.ones(site_num)
    elif option == "linear":
        ratio_vec = np.linspace(1, site_num, num=site_num)
    elif option == "square":
        ratio_vec = np.square(np.linspace(1, site_num, num=site_num))
    elif option == "exponential":
        ratio_vec = np.exp(np.linspace(1, site_num, num=site_num))
    else:
        raise ValueError("Split method not implemented!")

    total = sum(ratio_vec)
    left = n
    for site in range(site_num - 1):
        x = int(n * ratio_vec[site] / total)
        left = left - x
        split.append(x)
    split.append(left)
    return split


def main():
    parser = data_split_args_parser()
    args = parser.parse_args()

    json_data = {}
    json_data["data_path"] = args.data_path
    json_data["data_index"] = {}
    json_data["data_index"]["valid"] = {}
    json_data["data_index"]["valid"]["start"] = 0
    json_data["data_index"]["valid"]["end"] = args.size_valid

    site_size = split_num_proportion((args.size_total - args.size_valid), args.site_num, args.split_method)

    for site in range(args.site_num):
        site_id = args.site_name + str(site + 1)
        idx_start = args.size_valid + sum(site_size[:site])
        idx_end = args.size_valid + sum(site_size[: site + 1])
        json_data["data_index"][site_id] = {}
        json_data["data_index"][site_id]["start"] = idx_start
        json_data["data_index"][site_id]["end"] = idx_end
        json_data["data_index"][site_id]["lr_scale"] = site_size[site] / sum(site_size)

    with open(out_path, "w") as f:
        json.dump(json_data, f, indent=4)


if __name__ == "__main__":
    main()
