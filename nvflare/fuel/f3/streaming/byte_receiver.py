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
import threading
from collections import deque
from typing import Callable

from nvflare.fuel.f3.cellnet.cell import Cell
from nvflare.fuel.f3.cellnet.defs import MessageHeaderKey
from nvflare.fuel.f3.cellnet.registry import Callback, Registry
from nvflare.fuel.f3.message import Headers, Message
from nvflare.fuel.f3.streaming.stream_const import (
    EOS,
    STREAM_ACK_TOPIC,
    STREAM_CHANNEL,
    STREAM_DATA_TOPIC,
    StreamDataType,
    StreamHeaderKey,
)
from nvflare.fuel.f3.streaming.stream_types import Stream, StreamError, StreamFuture

log = logging.getLogger(__name__)

MAX_OUT_SEQ_CHUNKS = 8
# 1/4 of the window size
ACK_INTERVAL = 1024 * 1024 * 4


class RxTask:
    """Receiving task for ByteStream"""

    def __init__(self, sid: str, channel: str, topic: str, origin: str, headers: dict):
        self.sid = sid
        self.channel = channel
        self.topic = topic
        self.origin = origin
        self.headers = headers
        self.size = 0

        self.buffers = deque()
        self.out_seq_buffers = {}
        self.stream_future = None
        self.expected_seq = 0
        self.offset = 0
        self.offset_ack = 0
        self.eos = False
        self.waiter = threading.Event()

    def __str__(self):
        return f"[Rx{self.sid} to {self.origin} for {self.channel}/{self.topic}]"


class RxStream(Stream):
    """A stream that's used to read streams from the buffer"""

    def __init__(self, cell: Cell, task: RxTask):
        super().__init__(task.size, task.headers)
        self.cell = cell
        self.task = task

    def read(self, chunk_size: int) -> bytes:
        if self.closed:
            raise StreamError("Read from closed stream")

        if (not self.task.buffers) and self.task.eos:
            if not self.task.stream_future.done():
                self.task.stream_future.set_result(self.task.offset)

            return EOS

        # Block if buffers are empty
        if not self.task.buffers:
            self.task.waiter.clear()
            self.task.waiter.wait()

        buf = self.task.buffers.popleft()
        if 0 < chunk_size < len(buf):
            result = buf[0:chunk_size]
            # Put leftover to the head of the queue
            self.task.buffers.appendleft(buf[chunk_size:])
        else:
            result = buf

        self.task.offset += len(buf)
        if self.task.offset - self.task.offset_ack > ACK_INTERVAL:
            # Send ACK
            message = Message(Headers(), None)
            message.add_headers(
                {
                    StreamHeaderKey.STREAM_ID: self.task.sid,
                    StreamHeaderKey.DATA_TYPE: StreamDataType.ACK,
                    StreamHeaderKey.OFFSET: self.task.offset,
                }
            )
            self.cell.fire_and_forget(STREAM_CHANNEL, STREAM_ACK_TOPIC, self.task.origin, message)
            self.task.offset_ack = self.task.offset

        return result

    def close(self):
        if not self.task.stream_future.done():
            self.task.stream_future.set_result(self.task.offset)
        self.closed = True


class ByteReceiver:
    def __init__(self, cell: Cell):
        self.cell = cell
        self.cell.register_request_cb(channel=STREAM_CHANNEL, topic=STREAM_DATA_TOPIC, cb=self._data_handler)
        self.registry = Registry()
        self.rx_task_map = {}

    def register_callback(self, channel: str, topic: str, stream_cb: Callable, *args, **kwargs):
        if not callable(stream_cb):
            raise StreamError(f"specified stream_cb {type(stream_cb)} is not callable")

        self.registry.set(channel, topic, Callback(stream_cb, args, kwargs))

    def _data_handler(self, message: Message):

        sid = message.get_header(StreamHeaderKey.STREAM_ID)
        origin = message.get_header(MessageHeaderKey.ORIGIN)
        task = self.rx_task_map.get(sid, None)
        if not task:
            # Handle new stream
            channel = message.get_header(StreamHeaderKey.CHANNEL)
            topic = message.get_header(StreamHeaderKey.TOPIC)
            task = RxTask(sid, channel, topic, origin, message.headers)
            task.stream_future = StreamFuture(sid, message.headers)
            task.size = message.get_header(StreamHeaderKey.SIZE, 0)
            self.rx_task_map[sid] = task

            # Invoke callback
            callback = self.registry.find(channel, topic)
            if not callback:
                self._stop_task(task, StreamError(f"No callback is registered for {channel}/{topic}"))
                return

            stream = RxStream(self.cell, task)
            callback.cb(task.stream_future, stream, False, *callback.args, **callback.kwargs)

        error = message.get_header(StreamHeaderKey.ERROR_MSG, None)
        if error:
            self._stop_task(task, StreamError(f"Received error from {origin}: {error}"))
            return

        seq = message.get_header(StreamHeaderKey.STREAM_ID)

        if seq == task.expected_seq:
            self._append(task, message.payload)
            task.expected_seq += 1

            # Try to reassemble out-of-seq buffers
            while task.expected_seq in task.out_seq_buffers:
                chunk = task.out_seq_buffers.pop(task.expected_seq)
                self._append(task, chunk)
                task.expected_seq += 1

        else:

            if len(task.out_seq_buffers) >= MAX_OUT_SEQ_CHUNKS:
                self._stop_task(task, StreamError(f"Too many out-of-sequence chunks: {len(task.out_seq_buffers)}"))
            else:
                task.out_seq_buffers[seq] = message.payload

        data_type = message.get_header(StreamHeaderKey.DATA_TYPE)
        if data_type == StreamDataType.FINAL:
            # Task is not done till all buffers are read so future is not set here
            self._stop_task(task)

    @staticmethod
    def _append(task: RxTask, buf: bytes):
        if not buf:
            return

        task.buffers.append(buf)

        # Wake up blocking read()
        if not task.waiter.is_set():
            task.waiter.set()

    def _stop_task(self, task: RxTask, error: StreamError = None):
        if error:
            task.stream_future.set_exception(error)

            # Send error to sender
            message = Message(Headers(), None)

            message.add_headers(
                {
                    StreamHeaderKey.STREAM_ID: task.sid,
                    StreamHeaderKey.DATA_TYPE: StreamDataType.ERROR,
                    StreamHeaderKey.ERROR_MSG: str(error),
                }
            )
            self.cell.fire_and_forget(STREAM_CHANNEL, STREAM_ACK_TOPIC, task.origin, message)

        task.eos = True
