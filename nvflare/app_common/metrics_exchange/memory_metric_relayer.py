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

from queue import Queue

from nvflare.apis.event_type import EventType
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.metrics_exchange.metrics_exchanger import MetricsExchanger
from nvflare.fuel.utils.constants import Mode
from nvflare.fuel.utils.pipe.memory_pipe import MemoryPipe
from nvflare.fuel.utils.pipe.pipe_handler import PipeHandler

from .metric_relayer import MetricRelayer


class MemoryMetricRelayer(MetricRelayer):
    def __init__(
        self,
        metrics_exchanger_id: str,
        pipe_id: str = "_memory_pipe",
        read_interval: float = 0.1,
        heartbeat_interval: float = 5.0,
        heartbeat_timeout: float = 30.0,
    ):
        """Metrics receiver with memory pipe."""
        super().__init__(
            pipe_id=pipe_id,
            read_interval=read_interval,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
        )
        self.metrics_exchanger_id = metrics_exchanger_id

        self.x_queue = Queue()
        self.y_queue = Queue()

    def _create_metrics_exchanger(self):
        pipe = MemoryPipe(x_queue=self.x_queue, y_queue=self.y_queue, mode=Mode.ACTIVE)

        # init pipe handler
        pipe_handler = PipeHandler(
            pipe,
            read_interval=self._read_interval,
            heartbeat_interval=self._heartbeat_interval,
            heartbeat_timeout=self._heartbeat_timeout,
        )
        pipe_handler.start()
        metrics_exchanger = MetricsExchanger(pipe_handler=pipe_handler)
        return metrics_exchanger

    def handle_event(self, event_type: str, fl_ctx: FLContext):
        if event_type == EventType.ABOUT_TO_START_RUN:
            engine = fl_ctx.get_engine()
            # inserts MetricsExchanger into engine components
            metrics_exchanger = self._create_metrics_exchanger()
            all_components = engine.get_all_components()
            all_components[self.metrics_exchanger_id] = metrics_exchanger
            # inserts MemoryPipe into engine components
            pipe = MemoryPipe(x_queue=self.x_queue, y_queue=self.y_queue, mode=Mode.PASSIVE)
            all_components[self.pipe_id] = pipe

        super().handle_event(event_type, fl_ctx)
