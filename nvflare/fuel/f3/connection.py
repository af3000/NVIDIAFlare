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
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Union

from nvflare.fuel.f3.drivers.connnector import Connector

BytesAlike = Union[bytes, bytearray, memoryview]


class ConnState(Enum):
    IDLE = 1           # Initial state
    CONNECTED = 2      # New connection
    CLOSED = 3         # Connection is closed


class FrameReceiver(ABC):

    @abstractmethod
    def process_frame(self, frame: BytesAlike):
        """Frame received callback

         Args:
             frame: The frame received

         Raises:
             CommError: If any error happens while processing the frame
        """
        pass


class Connection(ABC):
    """FCI connection spec. A connection is used to transfer opaque frames"""

    lock = threading.Lock()
    conn_count = 0

    def __init__(self, connector: Connector):
        self.name = Connection._get_connection_name()
        self.state = ConnState.IDLE
        self.frame_receiver = None
        self.connector = connector

    @abstractmethod
    def get_conn_properties(self) -> dict:
        """Get connection specific properties, like peer address, TLS certificate etc

        Raises:
            CommError: If any errors
        """
        pass

    @abstractmethod
    def close(self):
        """Close connection

        Raises:
            CommError: If any errors
        """
        pass

    @abstractmethod
    def send_frame(self, frame: BytesAlike):
        """Send a SFM frame through the connection to the remote endpoint.

        Args:
            frame: The frame to be sent

        Raises:
            CommError: If any error happens while sending the frame
        """
        pass

    def register_frame_receiver(self, receiver: FrameReceiver):
        """Register frame receiver

        Args:
            receiver: The frame receiver

        Raises:
            CommError: If any error happens while processing the frame
        """
        self.frame_receiver = receiver

    @staticmethod
    def _get_connection_name():
        with Connection.lock:
            Connection.conn_count += 1

        return "CN%05d" % Connection.conn_count
