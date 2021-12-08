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

from nvflare.apis.event_type import EventType
from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import ReturnCode
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable, make_reply
from nvflare.apis.signal import Signal
from nvflare.app_common.abstract.learner_spec import Learner
from nvflare.app_common.app_constant import AppConstants


class LearnerExecutor(Executor):
    def __init__(
        self,
        learner_id,
        train_task=AppConstants.TASK_TRAIN,
        submit_model_task=AppConstants.TASK_SUBMIT_MODEL,
        validate_task=AppConstants.TASK_VALIDATION,
    ):
        super().__init__()
        self.learner_id = learner_id
        self.learner = None
        self.train_task = train_task
        self.submit_model_task = submit_model_task
        self.validate_task = validate_task

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
        self.log_info(fl_ctx, f"Client trainer got task: {task_name}")

        if task_name == self.train_task:
            return self.train(shareable, fl_ctx, abort_signal)
        elif task_name == self.submit_model_task:
            return self.submit_model(shareable, fl_ctx)
        elif task_name == self.validate_task:
            return self.validate(shareable, fl_ctx, abort_signal)
        else:
            self.log_error(fl_ctx, f"Could not handle task: {task_name}")
            return make_reply(ReturnCode.TASK_UNKNOWN)

    def train(self, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        self.log_info(fl_ctx, f"ClientTrainer abort signal: {abort_signal.triggered}")
        if abort_signal.triggered:
            self.finalize(fl_ctx)
            return make_reply(ReturnCode.TASK_ABORTED)

        current_round = shareable.get_header(AppConstants.CURRENT_ROUND, None)

        train_result = self.learner.train(shareable, fl_ctx)

        self.log_info(fl_ctx, f"Completed the training for round: {current_round}")
        return train_result

    def submit_model(self, shareable: Shareable, fl_ctx: FLContext) -> Shareable:
        return self.learner.get_model_for_validation(Learner.BEST_MODEL, fl_ctx)

    def validate(self, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        self.log_info(fl_ctx, f"validate abort_signal {abort_signal.triggered}")
        return self.learner.validate(shareable, fl_ctx)

    def finalize(self, fl_ctx: FLContext):
        if self.learner:
            self.learner.finalize(fl_ctx)
