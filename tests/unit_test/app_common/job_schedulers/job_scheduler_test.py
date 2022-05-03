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

from typing import Dict, List, Optional, Tuple

import pytest

from nvflare.apis.client import Client
from nvflare.apis.fl_context import FLContext, FLContextManager
from nvflare.apis.job_def import Job
from nvflare.apis.job_scheduler_spec import DispatchInfo
from nvflare.apis.resource_manager_spec import ResourceManagerSpec
from nvflare.apis.server_engine_spec import ServerEngineSpec
from nvflare.app_common.job_schedulers.job_scheduler import DefaultJobScheduler
from nvflare.app_common.resource_managers.list_resource_manager import ListResourceManager


class DummyResourceManager(ResourceManagerSpec):
    def __init__(self, name, resources):
        self.name = name
        self.resources = resources

    def check_resources(self, resource_requirement: dict, fl_ctx: FLContext) -> (bool, Optional[str]):
        print(f"{self.name}: checking resources with requirements {resource_requirement}")
        for k in resource_requirement:
            if k in self.resources:
                if self.resources[k] < resource_requirement[k]:
                    return False, None
        return True, None

    def cancel_resources(self, resource_requirement: dict, token: str, fl_ctx: FLContext):
        print(f"{self.name}: cancelling resources {resource_requirement}")

    def allocate_resources(self, resource_requirement: dict, token: str, fl_ctx: FLContext) -> dict:
        print(f"{self.name}: allocating resources {resource_requirement}")
        result = {}
        for k in resource_requirement:
            if k in self.resources:
                self.resources[k] -= resource_requirement[k]
                result[k] = resource_requirement[k]
        return result

    def free_resources(self, resources: dict, token: str, fl_ctx: FLContext):
        print(f"{self.name}: freeing resources {resources}")
        for k in resources:
            self.resources[k] += resources[k]


class Site:
    def __init__(self, name, resources, resource_manager=None):
        self.name = name
        if resource_manager:
            self.resource_manager = resource_manager
        else:
            self.resource_manager = DummyResourceManager(name=name, resources=resources)


class MockServerEngine(ServerEngineSpec):
    def __init__(self, clients: Dict[str, Site], run_name="exp1"):
        self.fl_ctx_mgr = FLContextManager(
            engine=self,
            identity_name="__mock_engine",
            run_num=run_name,
            public_stickers={},
            private_stickers={},
        )
        self.clients = clients

    def fire_event(self, event_type: str, fl_ctx: FLContext):
        pass

    def get_clients(self):
        return [Client(name=x, token="") for x in self.clients]

    def sync_clients_from_main_process(self):
        pass

    def validate_clients(self, client_names: List[str]):
        pass

    def new_context(self):
        return self.fl_ctx_mgr.new_context()

    def get_workspace(self):
        pass

    def get_component(self, component_id: str) -> object:
        pass

    def register_aux_message_handler(self, topic: str, message_handle_func):
        pass

    def send_aux_request(self, targets: [], topic: str, request, timeout: float, fl_ctx: FLContext) -> dict:
        pass

    def get_widget(self, widget_id: str):
        pass

    def persist_components(self, fl_ctx: FLContext, completed: bool):
        pass

    def restore_components(self, snapshot, fl_ctx: FLContext):
        pass

    def start_client_job(self, run_number, client_sites):
        pass

    def check_client_resources(self, resource_reqs: Dict[str, dict]) -> Dict[str, Tuple[bool, Optional[str]]]:
        result = {}
        with self.new_context() as fl_ctx:
            for site_name, requirements in resource_reqs.items():
                result[site_name] = self.clients[site_name].resource_manager.check_resources(requirements, fl_ctx)
        return result

    def get_client_name_from_token(self, token):
        return self.clients.get(token)

    def cancel_client_resources(
        self, resource_check_results: Dict[str, Tuple[bool, str]], resource_reqs: Dict[str, dict]
    ):
        with self.new_context() as fl_ctx:
            for site_name, result in resource_check_results.items():
                check_result, token = result
                if check_result:
                    self.clients[site_name].resource_manager.cancel_resources(
                        resource_requirement=resource_reqs[site_name], token=token, fl_ctx=fl_ctx
                    )


def create_servers(server_num, sites: List[Site]):
    servers = []
    for i in range(server_num):
        engine = MockServerEngine(clients={s.name: s for s in sites})
        servers.append(engine)
    return servers


def create_resource(cpu, gpu):
    return {"cpu": cpu, "gpu": gpu}


def create_job(job_id, study_name, resource_spec, deploy_map, min_sites, required_sites=None):
    return Job(
        job_id=job_id,
        study_name=study_name,
        resource_spec=resource_spec,
        deploy_map=deploy_map,
        min_sites=min_sites,
        required_sites=required_sites,
        meta={},
    )


def create_jobs(num_jobs, prefix="job", **kwargs):
    return [Job(job_id=f"{prefix}{i}", **kwargs) for i in range(num_jobs)]


job1 = create_job(
    job_id="job1",
    study_name="hello",
    resource_spec={"site1": create_resource(1, 4), "site2": create_resource(1, 4), "site3": create_resource(2, 1)},
    deploy_map={"app1": ["site1", "site2"], "app2": ["site3"]},
    min_sites=3,
)

job2 = create_job(
    job_id="job2",
    study_name="hello",
    resource_spec={"site1": create_resource(2, 4), "site2": create_resource(2, 4), "site3": create_resource(12, 4)},
    deploy_map={"app3": ["site1", "site2"], "app4": ["site3"]},
    min_sites=3,
)

job3 = create_job(
    job_id="job3",
    study_name="number3",
    resource_spec={},
    deploy_map={"app5": []},
    min_sites=3,
)


TEST_CASES = [
    (
        [job1],
        [
            Site(name="site1", resources=create_resource(16, 8)),
            Site(name="site2", resources=create_resource(16, 8)),
            Site(name="site3", resources=create_resource(32, 1)),
            Site(name="site4", resources=create_resource(2, 1)),
        ],
        job1,
        {
            "site1": DispatchInfo(resource_requirements=create_resource(1, 4), token=None),
            "site2": DispatchInfo(resource_requirements=create_resource(1, 4), token=None),
            "site3": DispatchInfo(resource_requirements=create_resource(2, 1), token=None),
        },
    ),
    (
        [job2, job1],
        [
            Site(name="site1", resources=create_resource(16, 8)),
            Site(name="site2", resources=create_resource(16, 8)),
            Site(name="site3", resources=create_resource(32, 1)),
            Site(name="site4", resources=create_resource(2, 1)),
        ],
        job1,
        {
            "site1": DispatchInfo(resource_requirements=create_resource(1, 4), token=None),
            "site2": DispatchInfo(resource_requirements=create_resource(1, 4), token=None),
            "site3": DispatchInfo(resource_requirements=create_resource(2, 1), token=None),
        },
    ),
    (
        [job3],
        [Site(name=f"site{i}", resources=create_resource(16, 8)) for i in range(8)],
        job3,
        {f"site{i}": DispatchInfo(resource_requirements={}, token=None) for i in range(8)},
    ),
]


class TestDefaultJobScheduler:
    @pytest.mark.parametrize("job_candidates,sites,expected_job,expected_dispatch_info", TEST_CASES)
    def test_normal_case(self, job_candidates, sites, expected_job, expected_dispatch_info):
        servers = create_servers(server_num=1, sites=sites)
        scheduler = DefaultJobScheduler(max_jobs=10)
        with servers[0].new_context() as fl_ctx:
            job, dispatch_info = scheduler.schedule_job(job_candidates=job_candidates, fl_ctx=fl_ctx)
        assert job == expected_job
        for k1, k2 in zip(dispatch_info, expected_dispatch_info):
            assert dispatch_info[k1] == expected_dispatch_info[k2]

    def test_less_active_than_min(self):
        sites = [Site(name=f"site{i}", resources=create_resource(1, 1)) for i in range(3)]
        servers = create_servers(server_num=1, sites=sites)
        scheduler = DefaultJobScheduler()
        candidate = create_job(
            job_id="job",
            study_name="test_study",
            resource_spec={},
            deploy_map={"app5": []},
            min_sites=5,
        )
        with servers[0].new_context() as fl_ctx:
            job, dispatch_info = scheduler.schedule_job(job_candidates=[candidate], fl_ctx=fl_ctx)
        assert job is None

    def test_require_sites_not_active(self):
        sites = [Site(name=f"site{i}", resources=create_resource(1, 1)) for i in range(3)]
        servers = create_servers(server_num=1, sites=sites)
        scheduler = DefaultJobScheduler()
        candidate = create_job(
            job_id="job",
            study_name="test_study",
            resource_spec={},
            deploy_map={"app5": []},
            min_sites=1,
            required_sites=["site4"],
        )
        with servers[0].new_context() as fl_ctx:
            job, dispatch_info = scheduler.schedule_job(job_candidates=[candidate], fl_ctx=fl_ctx)
        assert job is None

    def test_require_sites_not_enough_resource(self):
        sites = [Site(name=f"site{i}", resources=create_resource(1, 1)) for i in range(3)]
        servers = create_servers(server_num=1, sites=sites)
        scheduler = DefaultJobScheduler()
        candidate = create_job(
            job_id="job",
            study_name="test_study",
            resource_spec={"site3": create_resource(2, 2)},
            deploy_map={"app5": []},
            min_sites=1,
            required_sites=["site3"],
        )
        with servers[0].new_context() as fl_ctx:
            job, dispatch_info = scheduler.schedule_job(job_candidates=[candidate], fl_ctx=fl_ctx)
        assert job is None

    @pytest.mark.parametrize("add_first_job", [True, False])
    def test_a_list_of_jobs(self, add_first_job):
        num_sites = 8
        num_jobs = 5
        max_jobs_allow = 4
        resource_on_each_site = {"gpu": [0, 1]}

        sites: Dict[str, Site] = {
            f"site{i}": Site(
                name=f"site{i}",
                resources=resource_on_each_site,
                resource_manager=ListResourceManager(resources=resource_on_each_site),
            )
            for i in range(num_sites)
        }
        first_job = create_jobs(
            1,
            prefix="weird_job",
            study_name="hello",
            resource_spec={"site0": {"gpu": 1}},
            deploy_map={"app": ["server", "site0"]},
            min_sites=1,
            required_sites=["site0"],
            meta={},
        )
        jobs = create_jobs(
            num_jobs=num_jobs,
            study_name="hello",
            resource_spec={f"site{i}": {"gpu": 1} for i in range(num_sites)},
            deploy_map={"app": ["server"] + [f"site{i}" for i in range(num_sites)]},
            min_sites=num_sites,
            required_sites=[f"site{i}" for i in range(num_sites)],
            meta={},
        )
        if add_first_job:
            jobs = first_job + jobs
        servers = create_servers(server_num=1, sites=list(sites.values()))
        scheduler = DefaultJobScheduler(max_jobs=max_jobs_allow)
        submitted_jobs = list(jobs)
        results = []
        for i in range(10):
            with servers[0].new_context() as fl_ctx:
                job, dispatch_infos = scheduler.schedule_job(job_candidates=submitted_jobs, fl_ctx=fl_ctx)
                if job:
                    submitted_jobs.remove(job)
                    results.append(job)
                    for site_name, dispatch_info in dispatch_infos.items():
                        sites[site_name].resource_manager.allocate_resources(
                            dispatch_info.resource_requirements, token=dispatch_info.token, fl_ctx=fl_ctx
                        )
        assert results == [jobs[0], jobs[1]]
