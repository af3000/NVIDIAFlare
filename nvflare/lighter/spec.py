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

import os
import shutil
from abc import ABC
from typing import List

from nvflare.apis.utils.format_check import name_check
from nvflare.security.logging import secure_log_traceback


class Participant(object):
    def __init__(self, type: str, name: str, org: str, enable_byoc: bool = False, *args, **kwargs):
        """Class to represent a participant.

        Each participant communicates to other participant.  Therefore, each participant has its
        own name, type, organization it belongs to, rules and other information.

        Args:
            type (str): server, client, admin or other string that builders can handle
            name (str): system-wide unique name
            org (str): system-wide unique organization
            enable_byoc (bool, optional): whether this participant allows byoc codes to be loaded. Defaults to False.

        Raises:
            ValueError: if name or org is not compliant with characters or format specification.
        """
        err, reason = name_check(name, type)
        if err:
            raise ValueError(reason)
        err, reason = name_check(org, "org")
        if err:
            raise ValueError(reason)
        self.type = type
        self.name = name
        self.org = org
        self.subject = name
        self.enable_byoc = enable_byoc
        self.props = kwargs


class Study(object):
    def __init__(self, name: str, description: str, participants: List[Participant]):
        """A container class to hold information about this FL study.

        This class only holds information.  It does not drive the workflow.

        Args:
            name (str): the study name
            description (str): brief description on this name
            participants (List[Participant]): All the participants that will join this study

        Raises:
            ValueError: when duplicate name found in participants list
        """
        self.name = name
        all_names = list()
        for p in participants:
            if p.name in all_names:
                raise ValueError(f"Unable to add a duplicate name {p.name} into this study.")
            else:
                all_names.append(p.name)
        self.description = description
        self.participants = participants

    def get_participants_by_type(self, type, first_only=True):
        found = list()
        for p in self.participants:
            if p.type == type:
                if first_only:
                    return p
                else:
                    found.append(p)
        return found


class Builder(ABC):
    def initialize(self, ctx: dict):
        pass

    def build(self, study: Study, ctx: dict):
        pass

    def finalize(self, ctx: dict):
        pass

    def get_wip_dir(self, ctx: dict):
        return ctx.get("wip_dir")

    def get_kit_dir(self, participate: Participant, ctx: dict):
        return os.path.join(self.get_wip_dir(ctx), participate.name, "startup")

    def get_state_dir(self, ctx: dict):
        return ctx.get("state_dir")

    def get_resources_dir(self, ctx: dict):
        return ctx.get("resources_dir")


class Provisioner(object):
    def __init__(self, root_dir: str, builders: List[Builder]):
        """Workflow class that drive the provision process.

        Provisioner's tasks:

            - Maintain the provision workspace folder structure;
            - Invoke Builders to generate the content of each startup kit

        ROOT_WORKSPACE Folder Structure::

            root_workspace_dir_name: this is the root of the workspace
                study_dir_name: the root dir of the study, could be named after the study
                    resources: stores resource files (templates, configs, etc.) of the Provisioner and Builders
                    prod: stores the current set of startup kits (production)
                        participate_dir: stores content files generated by builders
                    wip: stores the set of startup kits to be created (WIP)
                        participate_dir: stores content files generated by builders
                    state: stores the persistent state of the Builders

        Args:
            root_dir (str): the directory path to hold all generated or intermediate folders
            builders (List[Builder]): all builders that will be called to build the content
        """
        self.root_dir = root_dir
        self.builders = builders
        self.ctx = None

    def _make_dir(self, dirs):
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

    def _prepare_workspace(self, ctx):
        workspace = ctx.get("workspace")
        wip_dir = os.path.join(workspace, "wip")
        state_dir = os.path.join(workspace, "state")
        resources_dir = os.path.join(workspace, "resources")
        ctx.update(dict(wip_dir=wip_dir, state_dir=state_dir, resources_dir=resources_dir))
        dirs = [workspace, resources_dir, wip_dir, state_dir]
        self._make_dir(dirs)

    def provision(self, study: Study):
        # ctx = {"workspace": os.path.join(self.root_dir, study.name), "study": study}
        workspace = os.path.join(self.root_dir, study.name)
        ctx = {"workspace": workspace}  # study is more static information while ctx is dynamic
        self._prepare_workspace(ctx)
        try:
            for b in self.builders:
                b.initialize(ctx)

            # call builders!
            for b in self.builders:
                b.build(study, ctx)

            for b in self.builders[::-1]:
                b.finalize(ctx)

        except BaseException:
            prod_dir = ctx.get("current_prod_dir")
            if prod_dir:
                shutil.rmtree(prod_dir)
            print("Exception raised during provision.  Incomplete prod_n folder removed.")
            secure_log_traceback()
        finally:
            wip_dir = ctx.get("wip_dir")
            if wip_dir:
                shutil.rmtree(wip_dir)
