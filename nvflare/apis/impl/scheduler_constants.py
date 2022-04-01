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


class AuxChannelTopic:
    CHECK_RESOURCE = "_check_resource"
    CANCEL_RESOURCE = "_cancel_resource"
    ALLOCATE_RESOURCE = "_allocate_resource"
    FREE_RESOURCE = "_free_resource"

    DISPATCH_APP = "_dispatch_app"
    STOP_APP = "_stop_app"


class ShareableHeader:
    CHECK_RESOURCE_RESULT = "_check_resource_result"
    RESOURCE_RESERVE_TOKEN = "_resource_reserve_token"
    RESOURCE_SPEC = "_resource_spec"
    ALLOCATED_RESOURCES = "_allocated_resources"

    APP_NAME = "_app_name"
    APP_BYTES = "_app_bytes"
    DISPATCH_STATUS = "_dispatch_status"


class FLContextKey:
    RESOURCE_MANAGER = "_resource_manager"
    JOB_MANAGER = "_job_manager"


class GPUConstants:
    GPU_COUNT = "_gpu_count"
    GPU_DEVICE_PREFIX = "_gpu_device_"
