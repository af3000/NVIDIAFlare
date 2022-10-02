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

import time

from nvflare.apis.event_type import EventType
from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import ReturnCode
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import ReservedHeaderKey, Shareable, make_reply
from nvflare.apis.signal import Signal
from nvflare.app_common.app_constant import AppConstants
from nvflare.fuel.utils.pipe.pipe import Pipe

from .defs import Topic, receive_from_pipe, send_to_pipe


class HubExecutor(Executor):
    def __init__(
        self, pipe_id: str, task_wait_time: float, result_poll_interval: float = 0.5, task_read_wait_time: float = 10
    ):
        """

        Args:
            pipe_id:
            task_wait_time: how long to wait for result from T2
            result_poll_interval: polling interval for T2 result
            task_read_wait_time: how long to wait for T2 to read a task assignment
        """
        Executor.__init__(self)
        self.pipe_id = pipe_id
        self.task_wait_time = task_wait_time
        self.result_poll_interval = result_poll_interval
        self.task_read_wait_time = task_read_wait_time
        self.pipe = None
        self.task_seq_num = 0
        self.t2_ended = False
        self.pipe_monitor = None

    def handle_event(self, event_type: str, fl_ctx: FLContext):
        engine = fl_ctx.get_engine()
        if event_type == EventType.START_RUN:
            job_id = fl_ctx.get_job_id()
            self.pipe = engine.get_component(self.pipe_id)
            if not isinstance(self.pipe, Pipe):
                raise TypeError(f"pipe must be Pipe type. Got: {type(self.pipe)}")
            self.pipe.open(name=job_id, me="x")

    def execute(self, task_name: str, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        # send the task to T2
        task_id = shareable.get_header(ReservedHeaderKey.TASK_ID)
        self.task_seq_num += 1
        req_topic = f"{task_name}.{self.task_seq_num}"
        self.log_info(fl_ctx, f"sent task data to T2 for task {task_name}")
        task_received_by_t2 = send_to_pipe(self.pipe, topic=req_topic, data=shareable, timeout=self.task_read_wait_time)
        if not task_received_by_t2:
            return make_reply(ReturnCode.SERVICE_UNAVAILABLE)

        # wait for result from T2
        start = time.time()
        while True:
            if abort_signal.triggered:
                # notify T2 that the task is aborted
                send_to_pipe(self.pipe, Topic.ABORT_TASK, task_id)
                return make_reply(ReturnCode.TASK_ABORTED)

            topic, data = receive_from_pipe(self.pipe)
            if not topic:
                if self.task_wait_time and time.time() - start > self.task_wait_time:
                    # timed out
                    self.log_error(fl_ctx, f"task '{req_topic}' timeout after {self.task_wait_time} secs")
                    # also tell T2 to abort the task
                    send_to_pipe(self.pipe, Topic.ABORT_TASK, task_id)
                    return make_reply(ReturnCode.EXECUTION_EXCEPTION)
            elif topic == Topic.ABORT_TASK:
                # T2 told us to abort the task!
                if data == task_id:
                    return make_reply(ReturnCode.TASK_ABORTED)
            elif topic == Topic.END_RUN:
                # T2 told us it has ended the run
                self.log_error(fl_ctx, f"received {topic} from T2 while waiting for result for {req_topic}")
                return make_reply(ReturnCode.SERVICE_UNAVAILABLE)
            elif topic != req_topic:
                # ignore wrong task name
                self.log_error(fl_ctx, f"ignored '{topic}' when waiting for '{req_topic}'")
            else:
                self.log_info(fl_ctx, f"got result for request '{req_topic}' from T2")
                if not isinstance(data, Shareable):
                    self.log_error(fl_ctx, f"bad result data from T2 - must be Shareable but got {type(data)}")
                    return make_reply(ReturnCode.EXECUTION_EXCEPTION)
                # add important meta information
                if shareable.get_header(AppConstants.CURRENT_ROUND):
                    data.set_header(AppConstants.CURRENT_ROUND, shareable.get_header(AppConstants.CURRENT_ROUND))
                return data
            time.sleep(self.result_poll_interval)
