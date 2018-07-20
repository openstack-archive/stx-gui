#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

import logging

from django.views import generic

from openstack_dashboard.api import dc_manager
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

LOG = logging.getLogger(__name__)


@urls.register
class Subcloud(generic.View):
    """API for manipulating a single subcloud"""

    url_regex = r'dc_manager/subclouds/(?P<subcloud_id>[^/]+|default)/$'

    @rest_utils.ajax(data_required=True)
    def patch(self, request, subcloud_id):
        """Update a specific subcloud

        PATCH http://localhost/api/dc_manager/subclouds/2
        """
        dc_manager.subcloud_update(request, subcloud_id, request.DATA)

    @rest_utils.ajax()
    def delete(self, request, subcloud_id):
        """Delete a specific subcloud

        DELETE http://localhost/api/dc_manager/subclouds/3
        """
        dc_manager.subcloud_delete(request, subcloud_id)


@urls.register
class SubcloudConfig(generic.View):
    """API for Subcloud configurations."""
    url_regex = \
        r'dc_manager/subclouds/(?P<subcloud_id>[^/]+)/generate-config/$'

    @rest_utils.ajax()
    def get(self, request, subcloud_id):
        """Generate a config for a specific subcloud."""

        response = dc_manager.subcloud_generate_config(request, subcloud_id,
                                                       request.GET.dict())
        response = {'config': response}
        return rest_utils.CreatedResponse('/api/dc_manager/subclouds/',
                                          response)


@urls.register
class SubClouds(generic.View):
    """API for Distributed Cloud Subclouds"""
    url_regex = r'dc_manager/subclouds/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of subclouds"""
        result = dc_manager.subcloud_list(request)
        return {'items': [sc.to_dict() for sc in result]}

    @rest_utils.ajax(data_required=True)
    def put(self, request):
        """Create a Subcloud.

        Create a subcloud using the parameters supplied in the POST
        application/json object.
        """
        dc_manager.subcloud_create(request, request.DATA)


@urls.register
class Summaries(generic.View):
    """API for Distributed Cloud Alarm Summaries"""
    url_regex = r'dc_manager/alarm_summaries/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of summaries"""
        result = dc_manager.alarm_summary_list(request)
        return {'items': [s.to_dict() for s in result]}
