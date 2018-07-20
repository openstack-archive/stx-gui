#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from ceilometerclient import client as ceilometer_client
from django.conf import settings
from openstack_dashboard.api import base

from horizon.utils.memoized import memoized  # noqa


class Pipeline(base.APIResourceWrapper):
    """Represents one Ceilometer pipeline entry."""

    _attrs = ['name', 'enabled', 'meters', 'location', 'max_bytes',
              'backup_count', 'compress']

    def __init__(self, apipipeline):
        super(Pipeline, self).__init__(apipipeline)


@memoized
def ceilometerclient(request):
    """Initialization of Ceilometer client."""

    endpoint = base.url_for(request, 'metering')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    return ceilometer_client.Client('2', endpoint,
                                    token=(lambda: request.user.token.id),
                                    insecure=insecure,
                                    cacert=cacert)


def pipeline_list(request):
    """List the configured pipeline."""
    pipeline_entries = ceilometerclient(request).pipelines.list()
    pipelines = [Pipeline(p) for p in pipeline_entries]
    return pipelines


def pipeline_update(request, pipeline_name, some_dict):
    pipeline = ceilometerclient(request).pipelines.update(pipeline_name,
                                                          **some_dict)
    if not pipeline:
        raise ValueError(
            'No match found for pipeline_name "%s".' % pipeline_name)
    return Pipeline(pipeline)
