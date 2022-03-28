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

import logging
from collections import OrderedDict

import torch
import torch.nn as nn

from nvflare.apis.dxo import MetaKey
from nvflare.app_common.abstract.model import (
    ModelLearnable,
    ModelLearnableKey,
    make_model_learnable,
    validate_model_learnable,
)
from nvflare.app_common.app_constant import ModelFormat


class PTModelPersistenceFormatManagerPersonalized(object):

    PERSISTENCE_KEY_PER_MODELS = "personalized_models"
    PERSISTENCE_KEY_TRAIN_CONF = "train_conf"
    PERSISTENCE_KEY_META_PROPS = "meta_props"

    def __init__(self, data: dict, default_train_conf=None):
        """Manage the format for model persistence.

        Args:
            data (dict): a dict of dict.
            default_train_conf (dict, optional): configuration for train. Defaults to None.

        Raises:
            TypeError: when data is not a dictionary
        """
        if not isinstance(data, dict):
            raise TypeError("data must be a dict but got {}".format(type(data)))

        self.var_dict = None
        self.model_dict = None
        self.meta = None
        self.train_conf = None
        self.other_props = {}  # other props from the original data that need to be kept

        # dict of dicts
        self.model_dict = data[self.PERSISTENCE_KEY_PER_MODELS]
        self.meta = data.get(self.PERSISTENCE_KEY_META_PROPS, None)
        self.train_conf = data.get(self.PERSISTENCE_KEY_TRAIN_CONF, None)

        # we need to keep other props, if any, so they can be kept when persisted
        for k, v in data.items():
            if k not in [
                self.PERSISTENCE_KEY_PER_MODELS,
                self.PERSISTENCE_KEY_META_PROPS,
                self.PERSISTENCE_KEY_TRAIN_CONF,
            ]:
                self.other_props[k] = v

        if not self.train_conf:
            self.train_conf = default_train_conf

    def _get_processed_vars(self) -> dict:
        if self.meta:
            return self.meta.get(MetaKey.PROCESSED_KEYS, {})
        else:
            return {}

    def to_model_learnable(self, exclude_vars) -> dict:
        processed_vars = self._get_processed_vars()
        models = {}
        for client_id in self.model_dict.keys():
            weights = OrderedDict()
            var_dict = self.model_dict[client_id]
            for k, v in var_dict.items():
                if exclude_vars and exclude_vars.search(k):
                    continue

                is_processed = processed_vars.get(k, False)
                if is_processed:
                    weights[k] = v
                else:
                    weights[k] = v.cpu().numpy()
            models[client_id] = make_model_learnable(weights, self.meta)
        return models

    def to_persistence_dict(self) -> dict:
        processed_vars = self._get_processed_vars()
        models = {}
        for client_id in self.model_dict.keys():
            weights_dict = OrderedDict()
            var_dict = self.model_dict[client_id]
            for k, v in var_dict.items():
                is_processed = processed_vars.get(k, False)
                if is_processed:
                    weights_dict[k] = v
                else:
                    weights_dict[k] = torch.as_tensor(v)
            models[client_id] = weights_dict

        # always use complex format for saving
        persistence_dict = OrderedDict()
        persistence_dict[self.PERSISTENCE_KEY_PER_MODELS] = models
        if self.meta:
            persistence_dict[self.PERSISTENCE_KEY_META_PROPS] = self.meta
        if self.train_conf:
            persistence_dict[self.PERSISTENCE_KEY_TRAIN_CONF] = self.train_conf
        if self.other_props:
            for k, v in self.other_props.items():
                persistence_dict[k] = v
        return persistence_dict

    def update(self, ml_dict: dict):
        """Update the persistence data with the learned values.

        Args:
            ml_dict (Dict of ModelLearnable): updated information to be merged into existing Dict of ModelLearnable
        """
        for client_id in ml_dict.keys():
            if client_id != "meta":
                ml = ml_dict[client_id]
                # update with value of the model learnable
                # note that the original weights that are not learned are still kept!
                learned_weights = ml[ModelLearnableKey.WEIGHTS]
                for k, v in learned_weights.items():
                    self.model_dict[client_id][k] = v

    def get_persist_model_format(self):
        return ModelFormat.PT_CHECKPOINT
