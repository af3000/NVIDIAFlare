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
import time
from typing import Optional

import msgpack

from nvflare.fuel.f3.drivers.connection import Connection, Bytes
from nvflare.fuel.f3.drivers.driver import Mode
from nvflare.fuel.f3.drivers.prefix import Prefix, PREFIX_LEN
from nvflare.fuel.f3.endpoint import Endpoint
from nvflare.fuel.f3.message import Headers
from nvflare.fuel.f3.sfm.constants import Types, HandshakeKeys


class SfmConnection:
    """A wrapper of driver connection. Driver connection deals with frame.
    This connection handles messages"""

    def __init__(self, conn: Connection, local_endpoint: Endpoint, mode: Mode):
        self.conn = conn
        self.local_endpoint = local_endpoint
        self.endpoint = None
        self.mode = mode
        self.last_activity = 0
        self.sequence = 0
        self.lock = threading.Lock()

    def get_name(self) -> str:
        return self.conn.name

    def next_sequence(self) -> int:
        """Get next sequence number for the connection
        Sequence is used to detect lost frames
        """

        with self.lock:
            self.sequence = (self.sequence + 1) & 0xffff
            return self.sequence

    def send_handshake(self, frame_type: int):
        """Send HELLO/READY frame"""

        data = {
            HandshakeKeys.ENDPOINT_NAME: self.local_endpoint.name,
            HandshakeKeys.TIMESTAMP: time.time()}

        if self.local_endpoint.properties:
            data.update(self.local_endpoint.properties)

        self.send_dict(frame_type, 1, data)

    def send_data(self, app_id: int, stream_id: int, headers: Headers, payload: Bytes):
        """Send user data"""

        prefix = Prefix(0, 0, Types.DATA, 0, 0, app_id, stream_id, 0)
        self.send_frame(prefix, headers, payload)

    def send_dict(self, frame_type: int, stream_id: int, data: dict):
        """Send a dict as payload"""

        prefix = Prefix(0, 0, frame_type, 0, 0, 0, stream_id, 0)

        payload = msgpack.packb(data)
        self.send_frame(prefix, None, payload)

    def send_frame(self, prefix: Prefix, headers: Optional[Headers], payload: Optional[Bytes]):

        headers_bytes = self.headers_to_bytes(headers)
        header_len = len(headers_bytes) if headers_bytes else 0

        length = PREFIX_LEN + header_len

        if payload:
            length += len(payload)

        prefix.length = length
        prefix.header_len = header_len
        prefix.sequence = self.next_sequence()

        buffer: bytearray = bytearray(length)

        offset = 0
        prefix.to_buffer(buffer, offset)
        offset += PREFIX_LEN

        if headers_bytes:
            buffer[offset:] = headers_bytes
            offset += header_len

        if payload:
            buffer[offset:] = payload

        self.conn.send_frame(buffer)

    @staticmethod
    def headers_to_bytes(headers: Optional[dict]) -> Optional[bytes]:
        if headers:
            return msgpack.packb(headers)
        else:
            return None

