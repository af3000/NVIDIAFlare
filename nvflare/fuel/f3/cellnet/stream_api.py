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
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from concurrent.futures import Future
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)
lock = threading.Lock()
start_time = time.time() * 1000000  # microseconds
stream_count = 0


def gen_stream_id():
    global lock, stream_count, start_time
    with lock:
        stream_count += 1
    return "SID%16d" % (start_time + stream_count)


class StreamError(Exception):
    """All stream API throws this error"""

    pass


class StreamCancelled(StreamError):
    """Streaming is cancelled by sender"""


class Stream(ABC):
    """A raw, read-only, seekable binary byte stream"""

    def __init__(self, size: int = 0, headers: Optional[dict] = None):
        """Constructor for stream

        Args:
            size: The total size of stream. 0 if unknown
            headers: Optional headers to be passed to the receiver
        """
        self.sid = gen_stream_id()
        self.size = size
        self.pos = 0
        self.headers = headers

    def get_size(self) -> int:
        return self.size

    def get_pos(self):
        return self.pos

    def get_headers(self) -> Optional[dict]:
        return self.headers

    def stream_id(self):
        return self.sid

    @abstractmethod
    def read(self, chunk_size: int) -> bytes:
        """Read and return up to chunk_size bytes. It can return less but not more than the chunk_size.
        An empty bytes object is returned if the stream reaches the end.

        Args:
            chunk_size: Up to (but maybe less) this many bytes will be returned

        Returns:
            Binary data. If empty, it means the stream is depleted (EOF)
        """
        pass

    @abstractmethod
    def close(self):
        """Close the stream"""
        pass

    def seek(self, offset: int):
        """Change the stream position to the given byte offset.
        Args:
            offset: Offset relative to the start of the stream

        Exception:
            StreamError: If the stream is not seekable
        """
        self.pos = offset


class ObjectIterator(Iterator, ABC):
    """An object iterator that returns next object
    The __next__() method must be defined to return next object.
    """

    def __init__(self, headers: Optional[dict] = None):
        self.sid = gen_stream_id()
        self.headers = headers
        self.index = 0

    def get_headers(self) -> Optional[dict]:
        return self.headers

    def stream_id(self):
        return self.sid

    def get_index(self) -> int:
        return self.index

    def set_index(self, index: int):
        self.index = index


class StreamFuture:
    """Base future class for all stream calls.

    Fashioned after concurrent.futures.Future
    """

    def __init__(self, stream_id: str, task: Future, headers: Optional[dict] = None):
        self.stream_id = stream_id
        self.task = task
        self.headers = headers
        self.waiter = threading.Event()
        self.lock = threading.Lock()
        self.error: Optional[StreamError] = None
        self.value = None
        self.size = 0
        self.progress = 0
        self.done_callbacks = []

    def get_stream_id(self) -> str:
        return self.stream_id

    def get_headers(self) -> Optional[dict]:
        return self.headers

    def get_size(self) -> int:
        return self.size

    def set_size(self, size: int):
        self.size = size

    def get_progress(self) -> int:
        return self.progress

    def set_progress(self, progress: int):
        self.progress = progress

    def cancel(self):
        """Cancel the future if possible.

        Returns True if the future was cancelled, False otherwise. A future
        cannot be cancelled if it is running or has already completed.
        """

        with self.lock:
            if self.error or self.result:
                return False

            self.error = StreamCancelled("Stream is cancelled")
            self.task.cancel()

            return True

    def cancelled(self):
        with self.lock:
            return isinstance(self.error, StreamCancelled)

    def running(self):
        """Return True if the future is currently executing."""
        with self.lock:
            return not self.waiter.isSet()

    def done(self):
        """Return True of the future was cancelled or finished executing."""
        with self.lock:
            return self.error or self.waiter.isSet()

    def add_done_callback(self, status_cb: Callable, *args, **kwargs):
        """Attaches a callable that will be called when the future finishes.

        Args:
            status_cb: A callable that will be called with this future.
        """
        with self.lock:
            self.done_callbacks.append((status_cb, args, kwargs))

    def result(self, timeout=None) -> Any:
        """Return the result of the call that the future represents.

        Args:
            timeout: The number of seconds to wait for the result if the future
                isn't done. If None, then there is no limit on the wait time.

        Returns:
            The final result

        Raises:
            CancelledError: If the future was cancelled.
            TimeoutError: If the future didn't finish executing before the given
                timeout.
        """

        with self.lock:
            self.waiter.wait(timeout)

            if self.error:
                raise self.error

            return self.value

    def exception(self, timeout=None):
        """Return the exception raised by the call that the future represents.

        Args:
            timeout: The number of seconds to wait for the exception if the
                future isn't done. If None, then there is no limit on the wait
                time.

        Returns:
            The exception raised by the call that the future represents or None
            if the call completed without raising.

        Raises:
            CancelledError: If the future was cancelled.
            TimeoutError: If the future didn't finish executing before the given
                timeout.
        """

        with self.lock:
            self.waiter.wait(timeout)
            return self.error

    def set_result(self, value: Any):
        """Sets the return value of work associated with the future."""

        with self.lock:
            if self.error:
                raise StreamError("Invalid state, future already failed")
            self.value = value
            self.waiter.set()

        self._invoke_callbacks()

    def set_exception(self, exception):
        """Sets the result of the future as being the given exception."""
        with self.lock:
            self.error = exception
            self.waiter.set()

        self._invoke_callbacks()

    def _invoke_callbacks(self):
        for callback, args, kwargs in self.done_callbacks:
            try:
                callback(self, args, kwargs)
            except Exception as ex:
                log.error(f"Exception calling callback for {callback}: {ex}")


class ObjectStreamFuture(StreamFuture):
    def __init__(self, stream_id: str, task: Future):
        super().__init__(stream_id, task)
        self.index = 0
        self.object_cb = None
        self.cb_args = None
        self.cb_kwargs = None

    def get_index(self) -> int:
        """Current object index, which is only available for ObjectStream"""
        return self.index

    def set_index(self, index: int):
        """Set current object index"""
        self.index = index
