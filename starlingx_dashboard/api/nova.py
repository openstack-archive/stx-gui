from openstack_dashboard.api.nova import *


def server_group_create(request, **kwargs):
    import pdb; pdb.set_trace()
    return novaclient(request).server_groups.create(**kwargs)