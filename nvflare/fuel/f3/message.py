#  Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from abc import ABC, abstractmethod

import msgpack

from nvflare.fuel.f3.drivers.connection import Bytes
from nvflare.fuel.f3.endpoint import Endpoint


class AppIds:
    """Reserved application IDs"""

    ALL = 0
    DEFAULT = 1
    CELL_NET = 2
    PUB_SUB = 3


class Headers(dict):

    # Reserved Keys
    MSG_ID = "_MSG_ID_"
    TOPIC = "_TOPIC_"
    DEST = "_DEST_"
    JOB_ID = "_JOB_ID_"


class Message:

    def __init__(self, headers: Headers, payload: Bytes):
        """Construct an FCI message

         Raises:
             CommError: If any error encountered while starting up
         """

        self.headers = headers
        self.payload = payload


class MessageReceiver(ABC):

    @abstractmethod
    def process_message(self, endpoint: Endpoint, app_id: int, message: Message):
        pass
