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
"""Decomposers for Python builtin objects."""
from datetime import datetime
from typing import Any

from nvflare.fuel.utils.fobs.decomposer import Decomposer


class TupleDecomposer(Decomposer):
    @staticmethod
    def supported_type():
        return tuple

    def decompose(self, target: tuple) -> Any:
        return list(target)

    def recompose(self, data: Any) -> tuple:
        return tuple(data)


class SetDecomposer(Decomposer):
    @staticmethod
    def supported_type():
        return set

    def decompose(self, target: set) -> Any:
        return list(target)

    def recompose(self, data: Any) -> set:
        return set(data)


class DatetimeDecomposer(Decomposer):
    @staticmethod
    def supported_type():
        return datetime

    def decompose(self, target: datetime) -> Any:
        return target.isoformat()

    def recompose(self, data: Any) -> datetime:
        return datetime.fromisoformat(data)
