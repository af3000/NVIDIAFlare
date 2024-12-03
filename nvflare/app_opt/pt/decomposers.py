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

from io import BytesIO
from typing import Any

import numpy as np
import torch

from nvflare.fuel.utils import fobs
from nvflare.fuel.utils.fobs.datum import DatumManager

# Create a module
class TensorModule(torch.nn.Module):
    def __init__(self, tensor):
        super().__init__()
        self.tensor = tensor

    def forward(self):
        return self.tensor

class TensorJitDecomposer(fobs.Decomposer):
    def supported_type(self):
        return torch.Tensor

    def decompose(self, target: torch.Tensor, manager: DatumManager = None) -> Any:
        stream = BytesIO()

        # Use JIT serialization to avoid Pickle
        scripted_module = torch.jit.script(TensorModule(target))
        torch.jit.save(scripted_module, stream)
        stream.seek(0)

        return stream.getvalue()

    def recompose(self, data: Any, manager: DatumManager = None) -> torch.Tensor:
        stream = BytesIO(data)
        loaded_module = torch.jit.load(stream)
        return loaded_module()


class TensorNumpyDecomposer(fobs.Decomposer):
    def supported_type(self):
        return torch.Tensor

    def decompose(self, target: torch.Tensor, manager: DatumManager = None) -> Any:
        stream = BytesIO()

        # torch.save uses Pickle so converting Tensor to ndarray first
        array = target.detach().cpu().numpy()
        np.save(stream, array, allow_pickle=False)
        return stream.getvalue()

    def recompose(self, data: Any, manager: DatumManager = None) -> torch.Tensor:
        stream = BytesIO(data)
        array = np.load(stream, allow_pickle=False)
        return torch.from_numpy(array)