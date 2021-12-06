# Copyright (c) 2021, NVIDIA CORPORATION.
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

from nvflare.apis.dxo import from_shareable, DXO, DataKind
from nvflare.apis.event_type import EventType
from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import ReturnCode
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable, make_reply
from nvflare.apis.signal import Signal
from nvflare.app_common.abstract.learner_spec import Learner
from nvflare.app_common.abstract.model import model_learnable_to_dxo
from nvflare.app_common.app_constant import AppConstants


class LearnerExecutor(Executor):
    def __init__(self, learner_id):
        super().__init__()
        self.learner_id = learner_id
        self.learner = None

    def handle_event(self, event_type: str, fl_ctx: FLContext):
        if event_type == EventType.START_RUN:
            self.initialize(fl_ctx)
        elif event_type == EventType.ABORT_TASK:
            if self.learner:
                self.learner.abort(fl_ctx)
        elif event_type == EventType.END_RUN:
            self.finalize(fl_ctx)

    def initialize(self, fl_ctx: FLContext):
        engine = fl_ctx.get_engine()
        self.learner = engine.get_component(self.learner_id)
        if not isinstance(self.learner, Learner):
            raise TypeError(f"learner must be Learner type. Got: {type(self.learner)}")
        self.learner.initialize(engine.get_all_components(), fl_ctx)

    def execute(self, task_name: str, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        self.logger.info(f"Client trainer got task: {task_name}")

        if task_name == AppConstants.TASK_TRAIN:
            return self.train(shareable, fl_ctx, abort_signal)
        elif task_name == AppConstants.TASK_SUBMIT_MODEL:
            return self.submit_model(shareable, fl_ctx)
        elif task_name == AppConstants.TASK_VALIDATION:
            return self.validate(shareable, fl_ctx, abort_signal)
        else:
            self.logger.error(f"Could not handle task: {task_name}")
            return make_reply(ReturnCode.TASK_UNKNOWN)

    def train(self, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        self.logger.info(f"ClientTrainer abort signal: {abort_signal.triggered}")
        if abort_signal.triggered:
            self.finalize(fl_ctx)
            return make_reply(ReturnCode.TASK_ABORTED)

        current_round = shareable.get_header(AppConstants.CURRENT_ROUND, None)
        incoming_dxo = from_shareable(shareable)

        local_model_dict, meta_data = self.learner.train(incoming_dxo.data, fl_ctx)

        self.logger.info(f"Completed the training for   round: {current_round}")
        return DXO(data_kind=DataKind.WEIGHTS, data=local_model_dict, meta=meta_data).to_shareable()

    def submit_model(self, shareable: Shareable, fl_ctx: FLContext) -> Shareable:
        best_model = self.learner.get_best_model(fl_ctx)
        return model_learnable_to_dxo(best_model).to_shareable()

    def validate(self, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        self.logger.info(f"medl validate abort_signal {abort_signal.triggered}")

        incoming_dxo = from_shareable(shareable)
        model_weights = incoming_dxo.data
        metrics = self.learner.validate(model_weights, fl_ctx)

        return DXO(data_kind=DataKind.METRICS, data=metrics, meta={}).to_shareable()

    def finalize(self, fl_ctx: FLContext):
        if self.learner:
            self.learner.finalize(fl_ctx)
