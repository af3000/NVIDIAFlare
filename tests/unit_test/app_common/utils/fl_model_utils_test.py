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

import pytest

from nvflare.apis.dxo import DXO, DataKind, from_shareable
from nvflare.app_common.abstract.fl_model import FLModel, FLModelConst, ParamsType
from nvflare.app_common.app_constant import AppConstants
from nvflare.app_common.utils.fl_model_utils import FLModelUtils

TEST_CASES = [
    ({"hello": 123}, 100, 1),
    ({"cool": 123, "very": 4}, 10, 0),
]


class TestFLModelUtils:
    @pytest.mark.parametrize("weights,num_rounds,current_round", TEST_CASES)
    def test_from_shareable(self, weights, num_rounds, current_round):
        dxo = DXO(data_kind=DataKind.WEIGHTS, data=weights)
        shareable = dxo.to_shareable()
        shareable.set_header(AppConstants.NUM_ROUNDS, num_rounds)
        shareable.set_header(AppConstants.CURRENT_ROUND, current_round)
        shareable.set_header(AppConstants.VALIDATE_TYPE, "before_train_validate")
        fl_model = FLModelUtils.from_shareable(shareable=shareable)

        assert fl_model.params == weights
        assert fl_model.params_type == ParamsType.WEIGHTS
        assert fl_model.round == current_round
        assert fl_model.total_rounds == num_rounds

    @pytest.mark.parametrize("weights,num_rounds,current_round", TEST_CASES)
    def test_to_shareable(self, weights, num_rounds, current_round):
        fl_model = FLModel(params=weights, params_type=ParamsType.WEIGHTS, round=current_round, total_rounds=num_rounds)
        shareable = FLModelUtils.to_shareable(fl_model)
        dxo = from_shareable(shareable)
        assert shareable.get_header(AppConstants.CURRENT_ROUND) == current_round
        assert shareable.get_header(AppConstants.NUM_ROUNDS) == num_rounds
        assert dxo.data == weights
        assert dxo.data_kind == DataKind.WEIGHTS

    @pytest.mark.parametrize("weights,num_rounds,current_round", TEST_CASES)
    def test_from_to_shareable(self, weights, num_rounds, current_round):
        dxo = DXO(data_kind=DataKind.WEIGHTS, data=weights)
        shareable = dxo.to_shareable()
        shareable.set_header(AppConstants.NUM_ROUNDS, num_rounds)
        shareable.set_header(AppConstants.CURRENT_ROUND, current_round)
        shareable.set_header(AppConstants.VALIDATE_TYPE, "before_train_validate")
        fl_model = FLModelUtils.from_shareable(shareable=shareable)
        result_shareable = FLModelUtils.to_shareable(fl_model)
        result_dxo = from_shareable(result_shareable)
        assert shareable == result_shareable

    @pytest.mark.parametrize("weights,num_rounds,current_round", TEST_CASES)
    def test_from_dxo(self, weights, num_rounds, current_round):
        dxo = DXO(
            data_kind=DataKind.FL_MODEL,
            data={
                FLModelConst.PARAMS: weights,
                FLModelConst.PARAMS_TYPE: ParamsType.WEIGHTS,
                FLModelConst.TOTAL_ROUNDS: num_rounds,
                FLModelConst.ROUND: current_round,
            },
        )
        fl_model = FLModelUtils.from_dxo(dxo)
        assert fl_model.params == weights
        assert fl_model.params_type == ParamsType.WEIGHTS
        assert fl_model.round == current_round
        assert fl_model.total_rounds == num_rounds

    @pytest.mark.parametrize("weights,num_rounds,current_round", TEST_CASES)
    def test_to_dxo(self, weights, num_rounds, current_round):
        fl_model = FLModel(params=weights, params_type=ParamsType.WEIGHTS, round=current_round, total_rounds=num_rounds)
        dxo = FLModelUtils.to_dxo(fl_model)
        assert dxo.data_kind == DataKind.FL_MODEL
        assert dxo.data[FLModelConst.PARAMS] == weights
        assert dxo.data[FLModelConst.PARAMS_TYPE] == ParamsType.WEIGHTS
        assert dxo.data[FLModelConst.ROUND] == current_round
        assert dxo.data[FLModelConst.TOTAL_ROUNDS] == num_rounds
