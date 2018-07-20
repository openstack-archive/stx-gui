#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


import logging

from dcmanagerclient.api.v1 import client

from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


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
