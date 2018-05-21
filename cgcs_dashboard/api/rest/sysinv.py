#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.api import sysinv


@urls.register
class AlarmSummary(generic.View):
    """API for retrieving alarm summaries."""
    url_regex = r'sysinv/alarm_summary/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get an alarm summary for the system"""
        include_suppress = request.GET.get('include_suppress', False)
        result = sysinv.alarm_summary_get(request, include_suppress)
        return result.to_dict()


@urls.register
class System(generic.View):
    """API for retrieving the system."""
    url_regex = r'sysinv/system/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get the system entity"""
        result = sysinv.system_get(request)
        return result.to_dict()
