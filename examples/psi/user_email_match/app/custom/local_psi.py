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
from typing import List

import pandas as pd

from nvflare.app_common.psi.psi_spec import PSI


class LocalPSI(PSI):

    def __init__(self, psi_writer_id: str):
        super().__init__(psi_writer_id)
        self.data_root_dir = "/tmp/nvflare/data"
        self.data = {}

    def load_items(self) -> List[str]:
        site = self.fl_ctx.get_identity_name()
        df = pd.read_csv(f'{self.data_root_dir}/{site}/data.csv')

        # important the PSI algorithms requires the items are unique
        items = list(set(df[df.columns[0]].to_list()))
        return items
