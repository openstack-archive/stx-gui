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
# Copyright (c) 2017-2018 Wind River Systems, Inc.
#

import logging

from dcmanagerclient.api.v1 import client
from dcmanagerclient.exceptions import APIException

from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


DEFAULT_CONFIG_NAME = "all clouds default"


@memoized
def dcmanagerclient(request):
    endpoint = base.url_for(request, 'dcmanager', 'adminURL')
    c = client.Client(project_id=request.user.project_id,
                      user_id=request.user.id,
                      auth_token=request.user.token.id,
                      dcmanager_url=endpoint)
    return c


class Summary(base.APIResourceWrapper):
    _attrs = ['name', 'critical', 'major', 'minor', 'warnings', 'status']


def alarm_summary_list(request):
    summaries = dcmanagerclient(request).alarm_manager.list_alarms()
    return [Summary(summary) for summary in summaries]


class Subcloud(base.APIResourceWrapper):
    _attrs = ['subcloud_id', 'name', 'description', 'location',
              'software_version', 'management_subnet', 'management_state',
              'availability_status', 'management_start_ip',
              'management_end_ip', 'management_gateway_ip',
              'systemcontroller_gateway_ip', 'created_at', 'updated_at',
              'sync_status', 'endpoint_sync_status', ]


def subcloud_list(request):
    subclouds = dcmanagerclient(request).subcloud_manager.list_subclouds()
    return [Subcloud(subcloud) for subcloud in subclouds]


def subcloud_create(request, data):
    return dcmanagerclient(request).subcloud_manager.add_subcloud(
        **data.get('data'))


def subcloud_update(request, subcloud_id, changes):
    response = dcmanagerclient(request).subcloud_manager.update_subcloud(
        subcloud_id, **changes.get('updated'))
    # Updating returns a list of subclouds for some reason
    return [Subcloud(subcloud) for subcloud in response]


def subcloud_delete(request, subcloud_id):
    return dcmanagerclient(request).subcloud_manager.delete_subcloud(
        subcloud_id)


def subcloud_generate_config(request, subcloud_id, data):
    return dcmanagerclient(request).subcloud_manager.generate_config_subcloud(
        subcloud_id, **data)


class Strategy(base.APIResourceWrapper):
    _attrs = ['subcloud_apply_type', 'max_parallel_subclouds',
              'stop_on_failure', 'state', 'created_at', 'updated_at']


def get_strategy(request):
    try:
        response = dcmanagerclient(request).sw_update_manager.\
            patch_strategy_detail()
    except APIException as e:
        if e.error_code == 404:
            return None
        else:
            raise e

    if response and len(response):
        return Strategy(response[0])


def strategy_create(request, data):
    response = dcmanagerclient(request).sw_update_manager.\
        create_patch_strategy(**data)
    return Strategy(response)


def strategy_apply(request):
    return dcmanagerclient(request).sw_update_manager.apply_patch_strategy()


def strategy_abort(request):
    return dcmanagerclient(request).sw_update_manager.abort_patch_strategy()


def strategy_delete(request):
    return dcmanagerclient(request).sw_update_manager.delete_patch_strategy()


class Step(base.APIResourceWrapper):
    _attrs = ['cloud', 'stage', 'state', 'details', 'started_at',
              'finished_at']


def step_list(request):
    response = dcmanagerclient(request).strategy_step_manager.\
        list_strategy_steps()
    return [Step(step) for step in response]


class Config(base.APIResourceWrapper):
    _attrs = ['cloud', 'storage_apply_type', 'compute_apply_type',
              'max_parallel_computes', 'alarm_restriction_type',
              'default_instance_action']


def config_list(request):
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_list()
    return [Config(config) for config in response]


def config_update(request, subcloud, data):
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_update(subcloud, **data)
    return Config(response)


def config_delete(request, subcloud):
    return dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_delete(subcloud)


def config_get(request, subcloud):
    if subcloud == DEFAULT_CONFIG_NAME:
        subcloud = None
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_detail(subcloud)
    if response and len(response):
        return Config(response[0])