from openstack_dashboard.api.nova import *


def server_group_create(request, **kwargs):
    return novaclient(request).server_groups.create(**kwargs)