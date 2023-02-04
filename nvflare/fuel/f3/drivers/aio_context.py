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

import asyncio
import logging
import threading
import time


class AioContext:

    counter_lock = threading.Lock()
    thread_count = 0

    def __init__(self, name):
        self.closed = False
        self.name = name
        with AioContext.counter_lock:
            AioContext.thread_count += 1
        self.loop = None
        self.ready = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def run_aio_loop(self):
        self.logger.debug(f"{self.name}: started AioContext in thread {threading.current_thread().name}")
        # self.loop = asyncio.get_event_loop()
        self.loop = asyncio.new_event_loop()
        self.logger.debug(f"{self.name}: got loop: {id(self.loop)}")
        self.ready = True
        try:
            self.loop.run_forever()
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        except:
            self.logger.error("error running aio loop")
        finally:
            self.logger.debug(f"{self.name}: AIO Loop run done!")
            self.loop.close()
        self.logger.debug(f"{self.name}: AIO Loop Completed!")

    def run_coro(self, coro):
        while not self.ready:
            self.logger.debug(f"{self.name}: waiting for loop to be ready")
            time.sleep(0.5)
        self.logger.debug(f"{self.name}: coro loop: {id(self.loop)}")
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop_aio_loop(self):
        self.logger.debug("Cancelling pending tasks")
        pending_tasks = asyncio.all_tasks(self.loop)
        for task in pending_tasks:
            self.logger.debug(f"{self.name}: cancelled a task")
            try:
                task.cancel()
            except BaseException as ex:
                self.logger.debug(f"{self.name}: error cancelling task {type(ex)}")

        self.logger.debug("Stopping AIO loop")
        self.loop.call_soon_threadsafe(self.loop.stop)
        while self.loop.is_running():
            self.logger.debug("looping still running ...")
            time.sleep(0.5)
        self.logger.debug("stopped loop!")
