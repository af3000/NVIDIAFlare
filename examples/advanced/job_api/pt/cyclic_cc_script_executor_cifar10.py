# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

from src.net import Net

from nvflare.app_common.ccwf.ccwf_job import CCWFJob, CyclicClientConfig, CyclicServerConfig
from nvflare.app_common.ccwf.comps.simple_model_shareable_generator import SimpleModelShareableGenerator
from nvflare.app_opt.pt.file_model_persistor import PTFileModelPersistor
from nvflare.app_opt.script_executor import ScriptExecutor

if __name__ == "__main__":
    n_clients = 2
    num_rounds = 3
    train_script = "src/cifar10_fl.py"

    job = CCWFJob(name="cifar10_cyclic")

    job.add_cyclic(
        server_config=CyclicServerConfig(num_rounds=num_rounds, max_status_report_interval=300),
        client_config=CyclicClientConfig(
            executor=ScriptExecutor(task_script_path=train_script),
            persistor=PTFileModelPersistor(model=Net()),
            shareable_generator=SimpleModelShareableGenerator(),
        ),
    )

    # job.export_job("/tmp/nvflare/jobs/job_config")
    job.simulator_run("/tmp/nvflare/jobs/workdir", n_clients=n_clients, gpu="0")
