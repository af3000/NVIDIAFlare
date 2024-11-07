# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

from typing import Union

import numpy as np
import torch
from bitsandbytes.functional import dequantize_blockwise

from nvflare.apis.dxo import DXO, DataKind, MetaKey
from nvflare.apis.dxo_filter import DXOFilter
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable
from nvflare.app_opt.compression.constant import COMPRESSION_TYPE, DATA_TYPE


class ModelExtractor(DXOFilter):
    def __init__(
        self,
        source_data_type="float32",
        compression_type="float16",
    ):
        """Filter to extract Shareable object to recover from compression

        Args:
            source_data_type: original data type of the model
            compression_type: method used for compression

        """

        # support weight and weight_diff data kinds
        data_kinds = [DataKind.WEIGHTS, DataKind.WEIGHT_DIFF]
        super().__init__(supported_data_kinds=data_kinds, data_kinds_to_filter=data_kinds)

        # assign data and compression types
        self.logger.info("Using model extractor.")
        # check if source data type is valid
        if source_data_type.upper() not in DATA_TYPE:
            raise ValueError(f"Invalid source data type: {source_data_type}")
        else:
            self.source_data_type = source_data_type
        # check if compression type is valid
        if compression_type.upper() not in COMPRESSION_TYPE:
            raise ValueError(f"Invalid compression type: {compression_type}")
        else:
            self.compression_type = compression_type

    def extraction(self, params: dict, quant_state: dict, fl_ctx: FLContext):
        n_params = len(params.keys())
        self.log_info(fl_ctx, f"Running extraction {n_params} variables")
        n_bytes_before = 0
        n_bytes_after = 0
        n_bytes_meta = 0
        for i, param_name in enumerate(params.keys()):
            if self.source_data_type == "float32":
                if self.compression_type == "float16":
                    # direct convert
                    values = params[param_name]
                    n_bytes_before += values.nbytes
                    values = values.astype(np.float32)
                    n_bytes_after += values.nbytes
                    params[param_name] = values
                elif self.compression_type == "blockwise8":
                    # extract necessary values
                    values = params[param_name]
                    n_bytes_before += values.nbytes
                    absmax = quant_state["absmax"][param_name]
                    n_bytes_meta += absmax.nbytes
                    codebook = quant_state["codebook"][param_name]
                    n_bytes_meta += codebook.nbytes
                    # de-quanitze
                    absmax = torch.as_tensor(absmax)
                    codebook = torch.as_tensor(codebook)
                    quantized = torch.as_tensor(values)
                    dequantized = dequantize_blockwise(
                        quantized, absmax=absmax, code=codebook, blocksize=4096, nested=False
                    )
                    n_bytes_after += dequantized.nbytes
                    params[param_name] = dequantized
        self.log_info(
            fl_ctx,
            f"Extracted all {n_params} params"
            f" Before extraction: {n_bytes_before} bytes with meta: {n_bytes_meta} bytes"
            f" After extraction: {n_bytes_after} bytes",
        )
        return params

    def process_dxo(self, dxo: DXO, shareable: Shareable, fl_ctx: FLContext) -> Union[None, DXO]:
        """Filter process apply to the Shareable object.

        Args:
            dxo: data to be processed
            shareable: that the dxo belongs to
            fl_ctx: FLContext

        Returns: DXO object with extracted weights

        """

        self.log_info(fl_ctx, "Running extraction...")

        # check config
        compression_type = dxo.get_meta_prop(key=MetaKey.PROCESSED_ALGORITHM, default=None)
        if compression_type != self.compression_type:
            self.log_error(
                fl_ctx, f"shareable compression mode misalign! dxo with {compression_type}, not {self.compression_type}"
            )
            return None

        extracted_params = self.extraction(params=dxo.data, quant_state=dxo.meta["quant_state"], fl_ctx=fl_ctx)
        # Compose new DXO with extracted data
        dxo.data = extracted_params
        dxo.remove_meta_props(MetaKey.PROCESSED_ALGORITHM)
        dxo.remove_meta_props("quant_state")
        dxo.update_shareable(shareable)
        self.log_info(fl_ctx, f"Extracted {self.compression_type} to {self.source_data_type}")

        return dxo
