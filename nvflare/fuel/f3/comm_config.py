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
import logging
from typing import Dict, Optional

from nvflare.fuel.f3.drivers.net_utils import MAX_PAYLOAD_SIZE
from nvflare.fuel.utils.config import Config
from nvflare.fuel.utils.config_service import ConfigService

_comm_config_files = ["comm_config.json", "comm_config.json.default"]


DEFAULT_MAX_MSG_SIZE = MAX_PAYLOAD_SIZE


class VarName:

    MAX_MSG_SIZE = "max_message_size"
    ALLOW_ADHOC_CONNECTIONS = "allow_adhoc_conns"
    ADHOC_CONNECTION_SCHEME = "adhoc_conn_scheme"
    INTERNAL_CONNECTION_SCHEME = "internal_conn_scheme"
    BACKBONE_CONNECTION_GENERATION = "backbone_conn_gen"
    SUBNET_HEARTBEAT_INTERVAL = "subnet_heartbeat_interval"
    SUBNET_TROUBLE_THRESHOLD = "subnet_trouble_threshold"


class CommConfigurator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        config: Config = ConfigService.load_configuration(file_basename=_comm_config_files[0])
        self.config = config

    def get_config(self) -> Optional[Dict]:
        return self.config.to_dict() if self.config else None

    def get_max_message_size(self):
        return self.config.get_int(VarName.MAX_MSG_SIZE, DEFAULT_MAX_MSG_SIZE) if self.config else DEFAULT_MAX_MSG_SIZE
        # return ConfigService.get_int_var(VarName.MAX_MSG_SIZE, self.config, default=DEFAULT_MAX_MSG_SIZE)

    def allow_adhoc_connections(self, default):
        return self.config.get_bool(VarName.ALLOW_ADHOC_CONNECTIONS, default) if self.config else default
        # return ConfigService.get_bool_var(VarName.ALLOW_ADHOC_CONNECTIONS, self.config, default=default)

    def get_adhoc_connection_scheme(self, default):
        return self.config.get_str(VarName.ADHOC_CONNECTION_SCHEME, default) if self.config else default
        # return ConfigService.get_str_var(VarName.ADHOC_CONNECTION_SCHEME, self.config, default=default)

    def get_internal_connection_scheme(self, default):
        return self.config.get_str(VarName.INTERNAL_CONNECTION_SCHEME, default) if self.config else default
        # return ConfigService.get_str_var(VarName.INTERNAL_CONNECTION_SCHEME, self.config, default=default)

    def get_backbone_connection_generation(self, default):
        # return self.config.get_int(VarName.BACKBONE_CONNECTION_GENERATION, default) if self.config else default
        return ConfigService.get_int_var(VarName.BACKBONE_CONNECTION_GENERATION, self.config, default=default)

    def get_subnet_heartbeat_interval(self, default):
        return self.config.get_int(VarName.SUBNET_HEARTBEAT_INTERVAL, default) if self.config else default
        # return ConfigService.get_int_var(VarName.SUBNET_HEARTBEAT_INTERVAL, self.config, default)

    def get_subnet_trouble_threshold(self, default):
        return self.config.get_int(VarName.SUBNET_TROUBLE_THRESHOLD, default) if self.config else default
        # return ConfigService.get_int_var(VarName.SUBNET_TROUBLE_THRESHOLD, self.config, default)
