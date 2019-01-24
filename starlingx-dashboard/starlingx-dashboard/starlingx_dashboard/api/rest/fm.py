#
# Copyright (c) 2018-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from starlingx_dashboard.api import fm


LOG = logging.getLogger(__name__)


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


@urls.register
class Alarms(generic.View):
    """API for retrieving alarms."""
    url_regex = r'fm/alarm_list/$'

    @rest_utils.ajax()
    def get(self, request):
        search_opts = {'suppression': 'SUPPRESS_SHOW', 'expand': True}

        result = fm.alarm_list(request, search_opts=search_opts)

        return {'items': [sc.to_dict() for sc in result]}


@urls.register
class Alarm(generic.View):
    """API for retrieving one alarm."""
    url_regex = r'fm/alarm_get/(?P<uuid>[^/]+|default)/$'

    @rest_utils.ajax()
    def get(self, request, uuid):
        result = fm.alarm_get(request, uuid)
        return result.to_dict()


@urls.register
class Events(generic.View):
    """API for retrieving events."""
    url_regex = r'fm/event_log_list/$'

    @rest_utils.ajax()
    def get(self, request):
        search_opts = {'suppression': 'SUPPRESS_SHOW', 'expand': True}

        result, _more = fm.event_log_list(request, search_opts=search_opts)

        return {'items': [sc.to_dict() for sc in result]}


@urls.register
class Event(generic.View):
    """API for retrieving one event."""
    url_regex = r'fm/event_log_get/(?P<uuid>[^/]+|default)/$'

    @rest_utils.ajax()
    def get(self, request, uuid):
        result = fm.event_log_get(request, uuid)
        return result.to_dict()


@urls.register
class EventsSuppression(generic.View):
    """API for retrieving events suppression."""
    url_regex = r'fm/events_suppression_list/$'

    @rest_utils.ajax()
    def get(self, request):

        if 'include_unsuppressed' in request.GET:
            include_unsuppressed = True
        else:
            include_unsuppressed = False

        result = fm.event_suppression_list(
            request, include_unsuppressed=include_unsuppressed)
        return {'items': [sc.to_dict() for sc in result]}


@urls.register
class EventSuppression(generic.View):
    """API for updating the event suppression."""
    url_regex = r'fm/event_suppression/(?P<uuid>[^/]+)$'

    @rest_utils.ajax(data_required=True)
    def patch(self, request, uuid):

        result = fm.event_suppression_update(request, uuid, **(request.DATA))
        return result.to_dict()
