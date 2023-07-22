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

import copy
import json

import pytorch_lightning as pl

import nvflare.client as flare


def init():
    config_file = "nvf_lightning.json"
    config = {"exchange_path": "./", "exchange_format": "pytorch", "params_type": "FULL"}
    with open(config_file, "w") as f:
        json.dump(config, f)
    flare.init(config=config_file)


def patch(cls: pl.LightningModule) -> None:
    if not issubclass(cls, pl.LightningModule):
        raise RuntimeError("only support LightningModule")

    if hasattr(cls, "on_train_start"):
        cls.on_train_start = train_start(cls.on_train_start)
    else:
        cls.on_train_start = _fl_train_start

    if hasattr(cls, "on_train_end"):
        cls.on_train_end = train_end(cls.on_train_end)
    else:
        cls.on_train_end = _fl_train_end

    cls.get_fl_model = get_fl_model


def _fl_train_start(self):
    model, metadata = flare.receive_model()
    if model:
        weights = model
        self.fl_model = weights
        self.load_state_dict(weights)


def _fl_train_end(self):
    weights = self.state_dict()
    flare.submit_model(weights)


def get_fl_model(self):
    # make new copy of self, and then load fl_model
    new_module = copy.copy(self)
    if self.fl_model is not None:
        new_module.load_state_dict(self.fl_model)
    return new_module


def train_start(func):
    """Decorator factory."""

    def wrapper(self, *args, **kwargs):
        _fl_train_start(self)
        return func(self, *args, **kwargs)

    return wrapper


def train_end(func):
    """Decorator factory."""

    def wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        _fl_train_end(self)
        return r

    return wrapper
