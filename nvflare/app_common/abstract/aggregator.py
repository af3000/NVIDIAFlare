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

from abc import ABC, abstractmethod

from nvflare.apis.fl_component import FLComponent
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable


class Aggregator(FLComponent, ABC):
    def __init__(self) -> None:
        """Abstract class for Aggregators used in ScatterAndGather workflow."""
        super().__init__()

    @abstractmethod
    def accept(self, shareable: Shareable, fl_ctx: FLContext) -> bool:
        """Accept the shareable submitted by the client.

        Args:
            shareable (Shareable): Shareable object containing contribution.
            fl_ctx (FLContext): FL Context used to pass data.

        Returns:
            Bool to indicate if contribution is accepted.

        """
        pass

    @abstractmethod
    def aggregate(self, fl_ctx: FLContext) -> Shareable:
        """Perform the aggregation for all the received Shareable from the clients.

        Args:
            fl_ctx (FLContext): FL Context used to pass data.

        Returns:
            shareable (Shareable): Shareable containing aggregated model.

        """
        pass
