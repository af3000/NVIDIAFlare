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

import os
from typing import Any, Dict, Optional, Tuple, Union

from nvflare.apis.analytix import AnalyticsDataType
from nvflare.apis.utils.analytix_utils import create_analytic_dxo
from nvflare.app_common.abstract.fl_model import FLModel
from nvflare.app_common.data_exchange.constants import ExchangeFormat
from nvflare.fuel.utils import fobs
from nvflare.fuel.utils.import_utils import optional_import
from nvflare.fuel.utils.pipe.cell_pipe import CellPipe
from nvflare.fuel.utils.pipe.file_pipe import FilePipe
from nvflare.fuel.utils.pipe.pipe import Pipe

from .config import ClientConfig, ConfigKey, from_file
from .constants import CONFIG_DATA_EXCHANGE, CONFIG_METRICS_EXCHANGE
from .flare_agent import FlareAgentException
from .flare_agent_with_fl_model import FlareAgentWithFLModel
from .model_registry import ModelRegistry

PROCESS_MODEL_REGISTRY = None
PIPE_CLASS_MAPPING = {
    "FilePipe": {"pipe_class": FilePipe},
    "CellPipe": {"pipe_class": CellPipe},
}


def _create_client_config(config: Union[str, Dict]) -> ClientConfig:
    if isinstance(config, str):
        client_config = from_file(config_file=config)
    elif isinstance(config, dict):
        client_config = ClientConfig(config=config)
    else:
        raise ValueError("config should be either a string or dictionary.")
    return client_config


def _create_pipe_using_config(client_config: ClientConfig) -> Tuple[Pipe, str]:
    pipe_class = client_config.get_pipe_class()
    if pipe_class not in PIPE_CLASS_MAPPING:
        raise RuntimeError(f"Pipe class {pipe_class} is not supported.")

    pipe_args = client_config.get_pipe_args()
    pipe = PIPE_CLASS_MAPPING[pipe_class]["pipe_class"](**pipe_args)
    pipe_channel_name = client_config.get_pipe_channel_name()
    return pipe, pipe_channel_name


def _register_tensor_decomposer():
    tensor_decomposer, ok = optional_import(module="nvflare.app_opt.pt.decomposers", name="TensorDecomposer")
    if ok:
        fobs.register(tensor_decomposer)
    else:
        raise RuntimeError(f"Can't import TensorDecomposer for format: {ExchangeFormat.PYTORCH}")


def init(
    config: Union[str, Dict] = f"config/{CONFIG_DATA_EXCHANGE}",
    config_metrics: Union[str, Dict] = f"config/{CONFIG_METRICS_EXCHANGE}",
    rank: Optional[str] = None,
):
    """Initializes NVFlare Client API environment.

    Args:
        config (str or dict): configuration file or config dictionary.
        config_metrics (str or dict): configuration file or config dictionary for metrics exchange.
        rank (str): local rank of the process.
            It is only useful when the training script has multiple worker processes. (for example multi GPU)
    """
    global PROCESS_MODEL_REGISTRY  # Declare PROCESS_MODEL_REGISTRY as global

    if rank is None:
        rank = os.environ.get("RANK", "0")

    if PROCESS_MODEL_REGISTRY:
        raise RuntimeError("Can't call init twice.")

    client_config = _create_client_config(config=config)
    client_config_metrics = None
    try:
        client_config_metrics = _create_client_config(config=config_metrics)
    except Exception as e:
        print(
            f"ignoring setup metrics exchange due to exception: {e}. You can safely ignore this message if you are not using flare.log api."
        )

    flare_agent = None
    try:
        if rank == "0":
            if client_config.get_exchange_format() == ExchangeFormat.PYTORCH:
                _register_tensor_decomposer()

            pipe, task_channel_name = _create_pipe_using_config(client_config=client_config)
            metric_pipe, metric_channel_name = None, ""
            if client_config_metrics:
                metric_pipe, metric_channel_name = _create_pipe_using_config(client_config=client_config_metrics)

            flare_agent = FlareAgentWithFLModel(
                pipe=pipe,
                task_channel_name=task_channel_name,
                metric_pipe=metric_pipe,
                metric_channel_name=metric_channel_name,
            )
            flare_agent.start()

        PROCESS_MODEL_REGISTRY = ModelRegistry(client_config, rank, flare_agent)
    except Exception as e:
        print(f"flare.init failed: {e}")
        raise e


def get_model_registry() -> ModelRegistry:
    if PROCESS_MODEL_REGISTRY is None:
        raise RuntimeError("needs to call init method first")
    return PROCESS_MODEL_REGISTRY


def receive(timeout: Optional[float] = None) -> Optional[FLModel]:
    """Receives model from NVFlare side.

    Returns:
        An FLModel received.
    """
    model_registry = get_model_registry()
    return model_registry.get_model(timeout)


def send(fl_model: FLModel, clear_registry: bool = True) -> None:
    """Sends the model to NVFlare side.

    Args:
        fl_model (FLModel): Sends a FLModel object.
        clear_registry (bool): To clear the registry or not.
    """
    model_registry = get_model_registry()
    model_registry.submit_model(model=fl_model)
    if clear_registry:
        clear()


def clear():
    """Clears the model registry."""
    model_registry = get_model_registry()
    model_registry.clear()


def system_info() -> Dict:
    """Gets NVFlare system information.

    System information will be available after a valid FLModel is received.
    It does not retrieve information actively.

    Returns:
       A dict of system information.
    """
    model_registry = get_model_registry()
    return model_registry.get_sys_info()


def get_config() -> Dict:
    model_registry = get_model_registry()
    return model_registry.config.config


def get_job_id() -> str:
    sys_info = system_info()
    return sys_info.get(ConfigKey.JOB_ID, "")


def get_site_name() -> str:
    sys_info = system_info()
    return sys_info.get(ConfigKey.SITE_NAME, "")


def is_running() -> bool:
    try:
        receive()
        return True
    except FlareAgentException:
        return False


def is_train() -> bool:
    model_registry = get_model_registry()
    if model_registry.rank != "0":
        raise RuntimeError("only rank 0 can call is_train!")
    return model_registry.task_name == model_registry.config.config[ConfigKey.TRAIN_TASK_NAME]


def is_evaluate() -> bool:
    model_registry = get_model_registry()
    if model_registry.rank != "0":
        raise RuntimeError("only rank 0 can call is_evaluate!")
    return model_registry.task_name == model_registry.config.config[ConfigKey.EVAL_TASK_NAME]


def is_submit_model() -> bool:
    model_registry = get_model_registry()
    if model_registry.rank != "0":
        raise RuntimeError("only rank 0 can call is_submit_model!")
    return model_registry.task_name == model_registry.config.config[ConfigKey.SUBMIT_MODEL_TASK_NAME]


def log(key: str, value: Any, data_type: AnalyticsDataType, **kwargs):
    model_registry = get_model_registry()
    if model_registry.rank != "0":
        raise RuntimeError("only rank 0 can call log!")

    flare_agent = model_registry.flare_agent
    dxo = create_analytic_dxo(tag=key, value=value, data_type=data_type, **kwargs)
    flare_agent.log(dxo)
