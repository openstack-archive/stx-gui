#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2016-2018 Wind River Systems, Inc.
#

import logging

from six.moves.urllib.parse import urlparse

from openstack_dashboard.api import base

from nfv_client.openstack import sw_update

LOG = logging.getLogger(__name__)


STRATEGY_SW_PATCH = 'sw-patch'
STRATEGY_SW_UPGRADE = 'sw-upgrade'


class Client(object):
    def __init__(self, url, token_id):
        self.url = url
        self.token_id = token_id

    def get_strategy(self, strategy_name):
        return sw_update.get_strategies(self.token_id, self.url, strategy_name)

    def create_strategy(
            self, strategy_name, controller_apply_type, storage_apply_type,
            swift_apply_type, worker_apply_type, max_parallel_worker_hosts,
            default_instance_action, alarm_restrictions):
        return sw_update.create_strategy(
            self.token_id, self.url, strategy_name, controller_apply_type,
            storage_apply_type,
            swift_apply_type, worker_apply_type, max_parallel_worker_hosts,
            default_instance_action, alarm_restrictions)

    def delete_strategy(self, strategy_name, force):
        return sw_update.delete_strategy(self.token_id, self.url,
                                         strategy_name, force)

    def apply_strategy(self, strategy_name, stage_id):
        return sw_update.apply_strategy(self.token_id, self.url, strategy_name,
                                        stage_id)

    def abort_strategy(self, strategy_name, stage_id):
        return sw_update.abort_strategy(self.token_id, self.url, strategy_name,
                                        stage_id)


def _sw_update_client(request):
    o = urlparse(base.url_for(request, 'nfv'))
    url = "://".join((o.scheme, o.netloc))
    return Client(url, token_id=request.user.token.id)


def get_strategy(request, strategy_name):
    strategy = _sw_update_client(request).get_strategy(strategy_name)
    return strategy


def create_strategy(
        request, strategy_name, controller_apply_type, storage_apply_type,
        swift_apply_type, worker_apply_type, max_parallel_worker_hosts,
        default_instance_action, alarm_restrictions):
    strategy = _sw_update_client(request).create_strategy(
        strategy_name, controller_apply_type, storage_apply_type,
        swift_apply_type, worker_apply_type, max_parallel_worker_hosts,
        default_instance_action, alarm_restrictions)
    return strategy


def delete_strategy(request, strategy_name, force=False):
    response = _sw_update_client(request).delete_strategy(strategy_name, force)
    return response


def apply_strategy(request, strategy_name, stage_id=None):
    response = _sw_update_client(request).apply_strategy(strategy_name,
                                                         stage_id)
    return response


def abort_strategy(request, strategy_name, stage_id=None):
    response = _sw_update_client(request).abort_strategy(strategy_name,
                                                         stage_id)
    return response


def get_stages(request, strategy_name):
    strategy = _sw_update_client(request).get_strategy(strategy_name)
    if not strategy:
        return []
    stages = []
    for stage in strategy.build_phase.stages:
        phase = strategy.build_phase
        phase.stages = None
        stage.phase = phase
        stages.append(stage)
    for stage in strategy.apply_phase.stages:
        phase = strategy.apply_phase
        phase.stages = None
        stage.phase = phase
        stages.append(stage)
    for stage in strategy.abort_phase.stages:
        phase = strategy.abort_phase
        phase.stages = None
        stage.phase = phase
        stages.append(stage)

    return stages


def get_stage(request, strategy_name, phase_name, stage_id):
    stages = get_stages(request, strategy_name)
    for stage in stages:
        if stage.phase.phase_name == phase_name and \
                str(stage.stage_id) == str(stage_id):
            return stage


def get_step(request, strategy_name, phase_name, stage_id, step_id):
    stage = get_stage(request, strategy_name, phase_name, stage_id)
    for step in stage.steps:
        if str(step.step_id) == str(step_id):
            return step
