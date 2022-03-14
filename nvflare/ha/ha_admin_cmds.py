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

from nvflare.fuel.hci.client.api_status import APIStatus

from nvflare.fuel.hci.reg import CommandModule, CommandModuleSpec, CommandSpec


class HACommandModule(CommandModule):
    """Command module with commands for management in relation to the high availability framework."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_spec(self):
        return CommandModuleSpec(
            name="ha_mgmt",
            cmd_specs=[
                CommandSpec(
                    name="list_sp",
                    description="list service providers",
                    usage="list_sp...",
                    handler_func=self.list_sp,
                ),
                CommandSpec(
                    name="get_active_sp",
                    description="get active service provider",
                    usage="get_active_sp",
                    handler_func=self.get_active_sp,
                ),
                CommandSpec(
                    name="promote_sp",
                    description="promote active service provider to specified",
                    usage="promote_sp sp_end_point",
                    handler_func=self.promote_sp,
                ),
                CommandSpec(
                    name="_end_overseer_agent",
                    description="end the overseer agent thread",
                    usage="_end_overseer_agent",
                    handler_func=self._end_overseer_agent
                )
            ],
        )

    def list_sp(self, args, api):
        return {"status": APIStatus.SUCCESS, "details": str(api.overseer_agent._overseer_info)}

    def get_active_sp(self, args, api):
        return {"status": APIStatus.SUCCESS, "details": str(api.overseer_agent.get_primary_sp())}

    def promote_sp(self, args, api):
        if len(args) != 2:
            return {"status": APIStatus.ERROR_SYNTAX, "details": "usage: promote_sp example1.com:8002:8003"}

        sp_end_point = args[1]

        print("PROMOTING SP: {}".format(sp_end_point))
        api.overseer_agent.promote_sp(sp_end_point, headers={"username": api.user_name})
        return {"status": APIStatus.SUCCESS, "details": "Promoted endpoint. Synchronizing with overseer..."}

    def _end_overseer_agent(self, args, api):
        api.overseer_agent.end()
