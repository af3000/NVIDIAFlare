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


import traceback
from enum import Enum

import pytorch_lightning as pl
from pytorch_lightning.trainer.states import TrainerFn

import nvflare.client as flare
from nvflare.app_common.abstract.fl_model import FLModel
from nvflare.client.config import ConfigKey
from nvflare.client.constants import ModelExchangeFormat


class SendTrigger(Enum):
    AFTER_TRAIN_AND_TEST = 1
    AFTER_TRAIN = 2
    AFTER_TEST = 3


class FLCallback(pl.callbacks.Callback):
    def __init__(self, send_trigger: SendTrigger = SendTrigger.AFTER_TRAIN_AND_TEST):
        super(FLCallback, self).__init__()
        flare.init(
            config={
                ConfigKey.EXCHANGE_PATH: "./",
                ConfigKey.EXCHANGE_FORMAT: ModelExchangeFormat.PYTORCH,
                ConfigKey.TRANSFER_TYPE: "FULL",
            }
        )
        self.send_mode = send_trigger
        self.input_fl_model = None
        self.output_fl_model = None
        self.metrics_captured = False
        self.prev_loop_run = None

    def setup(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule", stage: str) -> None:
        loop = trainer.test_loop
        self.prev_loop_run = loop.run
        loop.run = test_loop_run_decorator(loop, self)

    def on_fit_start(self, trainer, pl_module):
        # receive the global model and update the local model with global model
        # the 1st time test() or fit() is called.
        self._receive_update_model(pl_module)

    def on_train_end(self, trainer, pl_module):
        if self.output_fl_model:
            self.output_fl_model.params = pl_module.cpu().state_dict()
        else:
            self.output_fl_model = flare.FLModel(params=pl_module.cpu().state_dict())

    def on_test_start(self, trainer, pl_module):
        # receive the global model and update the local model with global model
        # the 1st time test() or train() is called.
        # expect user will validate the global model first (i.e. test()), once that's done.
        # the metrics_captured will be set to True.
        # The subsequence test() calls will not trigger the receive update model.
        # Hence the test() will be validating the local model.
        if pl_module and not self.metrics_captured:
            self._receive_update_model(pl_module)

    def on_test_end(self, trainer, pl_module):
        self._check_and_send()

    def teardown(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule", stage: str) -> None:
        if self.prev_loop_run:
            trainer.test_loop.run = self.prev_loop_run

    def _receive_update_model(self, pl_module):
        if not self.input_fl_model:
            model = self._receive_model()
            if model and model.params:
                pl_module.load_state_dict(model.params)

    def _receive_model(self) -> FLModel:
        model = flare.receive()
        if model:
            self.input_fl_model = model
        return model

    def _check_and_send(self):
        if self.output_fl_model:
            if self.send_mode == SendTrigger.AFTER_TRAIN_AND_TEST:
                if self.output_fl_model.metrics and self.output_fl_model.params:
                    self.send()
            elif self.send_mode == SendTrigger.AFTER_TRAIN and self.output_fl_model.params:
                self.send()
            elif self.send_mode == SendTrigger.AFTER_TEST and self.output_fl_model.metrics:
                self.send()

    def send(self):
        try:
            flare.send(self.output_fl_model)
        except Exception as e:
            raise RuntimeError("failed to send FL model", e)


def test_loop_run_decorator(loop, cb):
    func = loop.run

    def wrapper(*args, **kwargs):
        if cb.metrics_captured:
            try:
                return func(*args, **kwargs)
            except BaseException as e:
                print(traceback.format_exc())
                raise e
        else:
            metrics = func(*args, **kwargs)
            _capture_metrics(metrics)
            cb.metrics_captured = True
            return metrics

    def _capture_metrics(metrics):
        result_metrics = _extract_metrics_from_tensor(metrics[0])
        if loop.trainer.state.fn == TrainerFn.TESTING and metrics:
            if cb.output_fl_model is None:
                cb.output_fl_model = flare.FLModel(metrics=result_metrics)
            elif not cb.output_fl_model.metrics:
                cb.output_fl_model.metrics = result_metrics

    def _extract_metrics_from_tensor(metrics):
        result_metrics = {}
        for key, t in metrics.items():
            result_metrics[key] = t.item()
        return result_metrics

    return wrapper
