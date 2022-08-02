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
import os

from .package_checker import (
    AdminConsolePackageChecker,
    ClientPackageChecker,
    OverseerPackageChecker,
    ServerPackageChecker,
)


def main():
    parser = argparse.ArgumentParser("nvflare preflight check")
    parser.add_argument("--package_root", required=True, type=str, help="root folder of all the packages")
    parser.add_argument(
        "--packages",
        type=str,
        nargs="*",
        help="package to be checked, if not specified, will check all the package inside the root.",
    )
    args = parser.parse_args()
    package_root = args.package_root
    dry_run = False

    if not os.path.isdir(package_root):
        print(f"package_root {package_root} is not a valid directory.")
        return

    if not args.packages:
        print("Did not specify any package. will run a full check including a dry run.")
        dry_run = True

    package_names = list(os.listdir(package_root))
    package_to_check = args.packages if args.packages is not None else package_names
    for name in package_to_check:
        if name not in package_names:
            print(f"package name {name} is not in the specified root dir.")
            return

        if not os.path.isdir(os.path.join(package_root, name, "startup")):
            print(f"package {name} is not in the correct format.")
            return

    package_checkers = [
        OverseerPackageChecker(),
        ServerPackageChecker(),
        ClientPackageChecker(),
        AdminConsolePackageChecker(),
    ]
    for p in package_checkers:
        for name in package_to_check:
            package_path = os.path.abspath(os.path.join(package_root, name))
            if p.should_be_checked(package_path):
                result = p.check_package(package_path)
                if result and dry_run:
                    p.dry_run(package_path)
        if p.report:
            p.print_report()

    for p in package_checkers[::-1]:
        for name in package_to_check:
            package_path = os.path.abspath(os.path.join(package_root, name))
            if p.should_be_checked(package_path):
                if dry_run:
                    p.stop_dry_run(package_path)


if __name__ == "__main__":
    main()
