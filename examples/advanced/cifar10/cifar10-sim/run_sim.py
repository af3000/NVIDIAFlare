# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
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

from nvflare import SimulatorRunner

n_clients = 8

simulator = SimulatorRunner(
    job_folder="jobs/cifar10_fedavg",
    workspace="/tmp/nvflare/sim_cifar10/cifar10_fedavg_alpha1.0",
    n_clients=n_clients,
    threads=n_clients,
)

run_status = simulator.run()
print("Simulator finished with run_status", run_status)
