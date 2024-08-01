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

from typing import Optional

from nvflare.app_common.app_constant import AppConstants
from nvflare.app_common.executors.client_api_launcher_executor import ClientAPILauncherExecutor
from nvflare.client.config import ExchangeFormat, TransferType
from nvflare.client.constants import CLIENT_API_CONFIG
from nvflare.fuel.utils import fobs
from nvflare.fuel.utils.import_utils import optional_import

torch, torch_ok = optional_import(module="torch")
if torch_ok:
    from nvflare.app_opt.pt.decomposers import TensorDecomposer
    from nvflare.app_opt.pt.params_converter import NumpyToPTParamsConverter, PTToNumpyParamsConverter

    DEFAULT_PARAMS_EXCHANGE_FORMAT = ExchangeFormat.PYTORCH
else:
    DEFAULT_PARAMS_EXCHANGE_FORMAT = ExchangeFormat.NUMPY

tensorflow, tf_ok = optional_import(module="tensorflow")
if tf_ok:
    from nvflare.app_opt.tf.params_converter import KerasModelToNumpyParamsConverter, NumpyToKerasModelParamsConverter


class ScriptLauncherExecutor(ClientAPILauncherExecutor):
    def __init__(
        self,
        launch_script: str,
        pipe_id: str = "pipe",
        launcher_id: Optional[str] = "launcher",
        launch_timeout: Optional[float] = None,
        task_wait_timeout: Optional[float] = None,
        last_result_transfer_timeout: float = 300.0,
        external_pre_init_timeout: float = 60.0,
        peer_read_timeout: Optional[float] = 60.0,
        monitor_interval: float = 0.01,
        read_interval: float = 0.5,
        heartbeat_interval: float = 5.0,
        heartbeat_timeout: float = 60.0,
        workers: int = 4,
        train_with_evaluation: bool = True,
        train_task_name: str = "train",
        evaluate_task_name: str = "evaluate",
        submit_model_task_name: str = "submit_model",
        from_nvflare_converter_id: Optional[str] = None,
        to_nvflare_converter_id: Optional[str] = None,
        params_exchange_format: str = ExchangeFormat.NUMPY,
        params_transfer_type: str = TransferType.FULL,
        config_file_name: str = CLIENT_API_CONFIG,
    ) -> None:
        """Wrapper around ClientAPILauncherExecutor with `launch_script` for different params_exchange_format."""
        ClientAPILauncherExecutor.__init__(
            self,
            pipe_id=pipe_id,
            launcher_id=launcher_id,
            launch_timeout=launch_timeout,
            task_wait_timeout=task_wait_timeout,
            last_result_transfer_timeout=last_result_transfer_timeout,
            external_pre_init_timeout=external_pre_init_timeout,
            peer_read_timeout=peer_read_timeout,
            monitor_interval=monitor_interval,
            read_interval=read_interval,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
            workers=workers,
            train_with_evaluation=train_with_evaluation,
            train_task_name=train_task_name,
            evaluate_task_name=evaluate_task_name,
            submit_model_task_name=submit_model_task_name,
            from_nvflare_converter_id=from_nvflare_converter_id,
            to_nvflare_converter_id=to_nvflare_converter_id,
            params_exchange_format=params_exchange_format,
            params_transfer_type=params_transfer_type,
            config_file_name=config_file_name,
        )

        self._launch_script = launch_script

        if torch_ok:
            if params_exchange_format == ExchangeFormat.PYTORCH:
                fobs.register(TensorDecomposer)

                if self._from_nvflare_converter is None:
                    self._from_nvflare_converter = NumpyToPTParamsConverter(
                        [AppConstants.TASK_TRAIN, AppConstants.TASK_VALIDATION]
                    )
                if self._to_nvflare_converter is None:
                    self._to_nvflare_converter = PTToNumpyParamsConverter(
                        [AppConstants.TASK_TRAIN, AppConstants.TASK_SUBMIT_MODEL]
                    )
        if tf_ok:
            if params_exchange_format == ExchangeFormat.NUMPY:
                if self._from_nvflare_converter is None:
                    self._from_nvflare_converter = NumpyToKerasModelParamsConverter(
                        [AppConstants.TASK_TRAIN, AppConstants.TASK_VALIDATION]
                    )
                if self._to_nvflare_converter is None:
                    self._to_nvflare_converter = KerasModelToNumpyParamsConverter(
                        [AppConstants.TASK_TRAIN, AppConstants.TASK_SUBMIT_MODEL]
                    )
        # TODO: support other params_exchange_format
