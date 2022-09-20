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

from typing import Dict, Tuple

from nvflare.apis.fl_component import FLComponent
from nvflare.app_common.abstract.statistics_spec import Histogram
from nvflare.app_common.app_constant import StatisticsConstants as StC
from nvflare.app_common.statistics.metrics_privacy_cleanser import MetricsPrivacyCleanser


class HistogramBinsCleanser(FLComponent, MetricsPrivacyCleanser):
    def __init__(self, max_bins_percent):
        """
        max_bins_percent:   max number of bins allowed in terms of percent of local data size.
                            Set this number to avoid number of bins equal or close equal to the
                            data size, which can lead to data leak.
                            for example: max_bins_percent = 10, means 10%
                            number of bins < max_bins_percent /100 * local count
        """
        super().__init__()
        self.max_bins_percent = max_bins_percent
        self.validate_inputs()

    def validate_inputs(self):
        if self.max_bins_percent < 0 or self.max_bins_percent > 100:
            raise ValueError(f"max_bins_percent {self.max_bins_percent} is not within (0, 100) ")

    def hist_bins_validate(self, client_name: str, metrics: Dict) -> Dict[str, Dict[str, bool]]:
        result = {}
        if StC.STATS_HISTOGRAM in metrics:
            hist_metrics = metrics[StC.STATS_HISTOGRAM]
            for ds_name in hist_metrics:
                result[ds_name] = {}
                feature_item_counts = metrics[StC.STATS_COUNT][ds_name]
                feature_metrics = hist_metrics[ds_name]
                for feature in feature_metrics:
                    hist: Histogram = feature_metrics[feature]
                    num_of_bins: int = len(hist.bins)
                    item_count = feature_item_counts[feature]
                    result[ds_name][feature] = True
                    if num_of_bins >= item_count * self.max_bins_percent / 100:
                        result[ds_name][feature] = False
                        limit_count = round(item_count * self.max_bins_percent)
                        self.logger.info(
                            f"number of bins: '{num_of_bins}' needs to be smaller than: {limit_count}], which"
                            f" is '{self.max_bins_percent}' percent of item_count '{item_count}' for feature '{feature}'"
                            f" in dataset '{ds_name}' for client {client_name}"
                        )
        return result

    def apply(self, metrics: dict, client_name: str) -> Tuple[dict, bool]:
        self.logger.info(f"HistogramBinCheck for client {client_name}")
        if StC.STATS_HISTOGRAM in metrics:
            validation_result = self.hist_bins_validate(client_name, metrics)
            metric_keys = [StC.STATS_HISTOGRAM]
            return super().cleanse(metrics, metric_keys, validation_result)
        else:
            return metrics, False
