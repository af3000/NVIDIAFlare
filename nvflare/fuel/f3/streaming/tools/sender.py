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
import time

from nvflare.fuel.f3.cellnet.cell import Cell
from nvflare.fuel.f3.message import Message
from nvflare.fuel.f3.stream_cell import StreamCell
from nvflare.fuel.f3.streaming.stream_types import StreamFuture
from nvflare.fuel.f3.streaming.tools.utils import TEST_CHANNEL, TEST_TOPIC, RX_CELL, TX_CELL, make_buffer, BUF_SIZE

logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter(fmt="%(relativeCreated)6d [%(threadName)-12s] [%(levelname)-5s] %(name)s: %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
root_log = logging.getLogger()
root_log.handlers.clear()
root_log.addHandler(handler)


class Sender:

    def __init__(self, url: str):
        core_cell = Cell(TX_CELL, url, secure=False, credentials={})
        self.stream_cell = StreamCell(core_cell)
        core_cell.start()

    def send(self,  blob: bytes) -> StreamFuture:
        return self.stream_cell.send_blob(TEST_CHANNEL, TEST_TOPIC, RX_CELL, Message(None, blob))


connect_url = "tcp://localhost:1234"
sender = Sender(connect_url)
time.sleep(2)

buffer = make_buffer(BUF_SIZE)
fut = sender.send(buffer)
n = fut.result()
print(f"Bytes sent: {n}")