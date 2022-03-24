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


class SpecialTaskName(object):

    TRY_AGAIN = "__try_again__"
    END_RUN = "__end_run__"


class TaskConstant(object):
    WAIT_TIME = "__wait_time__"


class EngineConstant(object):

    FL_TOKEN = "fl_token"
    CLIENT_TOKEN_FILE = "client_token.txt"


class InfoCollectorTopic(object):

    SHOW_STATS = "info.show_stats"
    SHOW_ERRORS = "info.show_errors"
    RESET_ERRORS = "info.reset_errors"


class ComponentCallerTopic(object):

    CALL_COMPONENT = "comp_caller.call"


class TrainingTopic(object):

    START = "train.start"
    ABORT = "train.abort"
    ABORT_TASK = "train.abort_task"
    DELETE_RUN = "train.delete_run"
    DEPLOY = "train.deploy"
    SHUTDOWN = "train.shutdown"
    RESTART = "train.restart"
    CHECK_STATUS = "train.check_status"
    SET_RUN_NUMBER = "train.set_run_number"


class RequestHeader(object):

    RUN_NUM = "run_number"
    APP_NAME = "app_name"
    CONTROL_COMMAND = "control_command"
    CALL_NAME = "call_name"
    COMPONENT_TARGET = "component_target"


class SysCommandTopic(object):

    SYS_INFO = "sys.info"
    SHELL = "sys.shell"


class ClientStatusKey(object):

    RUN_NUM = "run_number"
    CURRENT_TASK = "current_task"
    STATUS = "status"
    APP_NAME = "app_name"


# TODO:: Remove some of these constants
class AppFolderConstants:
    """hard coded file names inside the app folder."""

    CONFIG_TRAIN = "config_train.json"
    CONFIG_ENV = "environment.json"
    CONFIG_FED_SERVER = "config_fed_server.json"
    CONFIG_FED_CLIENT = "config_fed_client.json"


class SSLConstants:
    """hard coded names related to SSL."""

    CERT = "ssl_cert"
    PRIVATE_KEY = "ssl_private_key"
    ROOT_CERT = "ssl_root_cert"


class WorkspaceConstants:
    """hard coded file names inside the workspace folder."""

    LOGGING_CONFIG = "log.config"
    AUDIT_LOG = "audit.log"

    # these two files is used by shell scripts to determine restart / shutdown
    RESTART_FILE = "restart.fl"
    SHUTDOWN_FILE = "shutdown.fl"
