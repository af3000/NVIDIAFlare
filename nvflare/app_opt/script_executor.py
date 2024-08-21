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

import os

from nvflare.app_common.app_constant import AppConstants
from nvflare.client.config import ExchangeFormat
from nvflare.fuel.utils.import_utils import optional_import


class FrameworkType:
    RAW = "raw"
    NUMPY = "numpy"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"


class ScriptExecutor:
    def __init__(
        self,
        script: str,
        script_args: str = "",
        launch_external_process: bool = False,
        command: str = "python3",
        framework: FrameworkType = FrameworkType.PYTORCH,
    ):
        """ScriptExecutor is used with FedJob API to run or launch a script.

        in-process `launch_external_process=False` uses InProcessClientAPIExecutor (default).
        ex-process `launch_external_process=True` uses ClientAPILauncherExecutor.

        Args:
            script (str): Script to run. For in-process must be a python script path. For ex-process can be any script support by `command`.
            script_args (str): Optional arguments for script (appended to script).
            launch_external_process (bool): Whether to launch the script in external process. Defaults to False.
            command (str): If launch_external_process=True, command to run script (preprended to script). Defaults to "python3".
            framework (str): Framework type to connfigure converter and params exchange formats. Defaults to FrameworkType.PYTORCH.
        """
        self._script = script
        self._script_args = script_args
        self._command = command
        self._launch_external_process = launch_external_process
        self._framework = framework

        self._params_exchange_format = None
        self._from_nvflare_converter = None
        self._to_nvflare_converter = None

        if self._framework == FrameworkType.PYTORCH:
            _, torch_ok = optional_import(module="torch")
            if torch_ok:
                from nvflare.app_opt.pt.params_converter import NumpyToPTParamsConverter, PTToNumpyParamsConverter

                self._from_nvflare_converter = NumpyToPTParamsConverter(
                    [AppConstants.TASK_TRAIN, AppConstants.TASK_VALIDATION]
                )
                self._to_nvflare_converter = PTToNumpyParamsConverter(
                    [AppConstants.TASK_TRAIN, AppConstants.TASK_SUBMIT_MODEL]
                )
                self._params_exchange_format = ExchangeFormat.PYTORCH
            else:
                raise ValueError("Using FrameworkType.PYTORCH, but unable to import torch")
        elif self._framework == FrameworkType.TENSORFLOW:
            _, tf_ok = optional_import(module="tensorflow")
            if tf_ok:
                from nvflare.app_opt.tf.params_converter import (
                    KerasModelToNumpyParamsConverter,
                    NumpyToKerasModelParamsConverter,
                )

                self._from_nvflare_converter = NumpyToKerasModelParamsConverter(
                    [AppConstants.TASK_TRAIN, AppConstants.TASK_VALIDATION]
                )
                self._to_nvflare_converter = KerasModelToNumpyParamsConverter(
                    [AppConstants.TASK_TRAIN, AppConstants.TASK_SUBMIT_MODEL]
                )
                self._params_exchange_format = ExchangeFormat.NUMPY
            else:
                raise ValueError("Using FrameworkType.TENSORFLOW, but unable to import tensorflow")
        elif self._framework == FrameworkType.NUMPY:
            self._params_exchange_format = ExchangeFormat.NUMPY
        elif self._framework == FrameworkType.RAW:
            self._params_exchange_format = ExchangeFormat.RAW
        else:
            raise ValueError(f"Framework {self._framework} unsupported")

    def add_to_fed_job(self, job, ctx, **kwargs):
        """This method is used by Job API.

        Args:
            job: the Job object to add to
            ctx: Job Context

        Returns:

        """
        job.check_kwargs(args_to_check=kwargs, args_expected={"tasks": False})
        tasks = kwargs.get("tasks", ["*"])

        from_nvflare_id = None
        to_nvflare_id = None

        if self._from_nvflare_converter and self._to_nvflare_converter:
            from_nvflare_id = job.add_component("from_nvflare", self._from_nvflare_converter, ctx)
            to_nvflare_id = job.add_component("to_nvflare", self._to_nvflare_converter, ctx)

        if self._launch_external_process:
            from nvflare.app_common.executors.client_api_launcher_executor import ClientAPILauncherExecutor
            from nvflare.app_common.launchers.subprocess_launcher import SubprocessLauncher
            from nvflare.app_common.widgets.external_configurator import ExternalConfigurator
            from nvflare.app_common.widgets.metric_relay import MetricRelay
            from nvflare.fuel.utils.pipe.cell_pipe import CellPipe

            component = CellPipe(
                mode="PASSIVE",
                site_name="{SITE_NAME}",
                token="{JOB_ID}",
                root_url="{ROOT_URL}",
                secure_mode="{SECURE_MODE}",
                workspace_dir="{WORKSPACE}",
            )
            pipe_id = job.add_component("pipe", component, ctx)

            component = SubprocessLauncher(
                script=self._command + " custom/" + os.path.basename(self._script) + " " + self._script_args,
            )
            launcher_id = job.add_component("launcher", component, ctx)

            executor = ClientAPILauncherExecutor(
                pipe_id=pipe_id,
                launcher_id=launcher_id,
                params_exchange_format=self._params_exchange_format,
                from_nvflare_converter_id=from_nvflare_id,
                to_nvflare_converter_id=to_nvflare_id,
            )
            job.add_executor(executor, tasks=tasks, ctx=ctx)

            component = CellPipe(
                mode="PASSIVE",
                site_name="{SITE_NAME}",
                token="{JOB_ID}",
                root_url="{ROOT_URL}",
                secure_mode="{SECURE_MODE}",
                workspace_dir="{WORKSPACE}",
            )
            metric_pipe_id = job.add_component("metrics_pipe", component, ctx)

            component = MetricRelay(
                pipe_id=metric_pipe_id,
                event_type="fed.analytix_log_stats",
            )
            metric_relay_id = job.add_component("metric_relay", component, ctx)

            component = ExternalConfigurator(
                component_ids=[metric_relay_id],
            )
            job.add_component("config_preparer", component, ctx)
        else:
            from nvflare.app_common.executors.in_process_client_api_executor import InProcessClientAPIExecutor

            executor = InProcessClientAPIExecutor(
                task_script_path=os.path.basename(self._script),
                task_script_args=self._script_args,
                params_exchange_format=self._params_exchange_format,
                from_nvflare_converter_id=from_nvflare_id,
                to_nvflare_converter_id=to_nvflare_id,
            )
            job.add_executor(executor, tasks=tasks, ctx=ctx)

        job.add_resources(resources=[self._script], ctx=ctx)
