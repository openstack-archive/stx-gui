#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.api import fm


@urls.register
class AlarmSummary(generic.View):
    """API for retrieving alarm summaries."""
    url_regex = r'fm/alarm_summary/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get an alarm summary for the system"""
        include_suppress = request.GET.get('include_suppress', False)
        result = fm.alarm_summary_get(request, include_suppress)
        return result.to_dict()
