#
# Copyright (c) 2018 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0
#

from openstack_dashboard.api.nova import novaclient


def server_group_list(request, all_projects=False):
    return novaclient(request).server_groups.list(all_projects)


def server_group_get(request, server_group_id):
    return novaclient(request).server_groups.get(server_group_id)


def server_group_create(request, name, project_id, metadata, policies):
    return novaclient(request).server_groups.create(
        name, project_id, metadata, policies)


def server_group_delete(request, server_group_id):
    return novaclient(request).server_groups.delete(server_group_id)
