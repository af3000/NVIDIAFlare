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
from abc import ABC, abstractmethod

from nvflare.apis.signal import Signal
from nvflare.app_common.executors.init_final_component import InitFinalArgsComponent


class PsiControlHandler(InitFinalArgsComponent, ABC):
    """
    PSI handler is an interface for different PSI algorithms
    for example, DDH-Based PSI, Homomorphic-based PSI etc.
    for now, since we don't know the common features, we leave the interface blank for now
    This class handle the FL Server site (controller)'s logics
    """

    @abstractmethod
    def pre_workflow(self, abort_signal: Signal) -> bool:
        pass

    @abstractmethod
    def workflow(self, abort_signal: Signal) -> bool:
        pass

    @abstractmethod
    def post_workflow(self, abort_signal: Signal) -> bool:
        pass
