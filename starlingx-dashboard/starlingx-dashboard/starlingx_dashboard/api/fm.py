#
# Copyright (c) 2018-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from __future__ import absolute_import

import logging

import fmclient as fm_client

from django.conf import settings

from openstack_dashboard.api import base

from starlingx_dashboard.api import base as stx_base

# Fault management values
FM_ALL = 'ALL'
FM_ALARM = 'ALARM'
FM_LOG = 'LOG'
FM_SUPPRESS_SHOW = 'SUPPRESS_SHOW'
FM_SUPPRESS_HIDE = 'SUPPRESS_HIDE'
FM_ALL_SUPPRESS_HIDE = 'ALL|SUPPRESS_HIDE'
FM_SUPPRESSED = 'suppressed'
FM_UNSUPPRESSED = 'unsuppressed'
FM_CRITICAL = 'critical'
FM_MAJOR = 'major'
FM_MINOR = 'minor'
FM_WARNING = 'warning'
FM_NONE = 'none'


LOG = logging.getLogger(__name__)


def fmclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    # System Controller alarm summary is provided in RegionOne
    region = None
    if getattr(request.user, 'services_region', None) == 'SystemController' \
            and getattr(settings, 'DC_MODE', False):
        region = "RegionOne"

    endpoint = base.url_for(request, 'faultmanagement', region=region)

    version = 1

    LOG.debug('fmclient connection created using token "%s" and url "%s"',
              request.user.token.id, endpoint)
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s',
              {'user': request.user.id, 'tenant': request.user.tenant_id})

    return fm_client.Client(version, endpoint,
                            auth_token=request.user.token.id,
                            insecure=insecure, cacert=cacert)


class AlarmSummary(base.APIResourceWrapper):
    """Wrapper for Inventory Alarm Summaries"""

    _attrs = ['system_uuid',
              'warnings',
              'minor',
              'major',
              'critical',
              'status']

    def __init__(self, apiresource):
        super(AlarmSummary, self).__init__(apiresource)


def alarm_summary_get(request, include_suppress=False):
    summary = fmclient(request).alarm.summary(
        include_suppress=include_suppress)
    if len(summary) > 0:
        return AlarmSummary(summary[0])
    return None


class Alarm(base.APIResourceWrapper):
    """Wrapper for Inventory Alarms"""

    _attrs = ['uuid',
              'alarm_id',
              'alarm_state',
              'entity_type_id',
              'entity_instance_id',
              'timestamp',
              'severity',
              'reason_text',
              'alarm_type',
              'probable_cause',
              'proposed_repair_action',
              'service_affecting',
              'suppression_status',
              'mgmt_affecting']

    def __init__(self, apiresource):
        super(Alarm, self).__init__(apiresource)


def alarm_list(request, search_opts=None):
    paginate = False
    include_suppress = False

    # If expand is set to true then all the data of the alarm is returned not
    # just a subset.
    expand = False

    if search_opts is None:
        search_opts = {}

    limit = search_opts.get('limit', None)
    marker = search_opts.get('marker', None)
    sort_key = search_opts.get('sort_key', None)
    sort_dir = search_opts.get('sort_dir', None)
    page_size = stx_base.get_request_page_size(request, limit)

    if "suppression" in search_opts:
        suppression = search_opts.pop('suppression')

        if suppression == FM_SUPPRESS_SHOW:
            include_suppress = True
        elif suppression == FM_SUPPRESS_HIDE:
            include_suppress = False

    if "expand" in search_opts:
        expand = True

    if 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            limit = page_size + 1

    alarms = fmclient(request).alarm.list(
        limit=limit, marker=marker, sort_key=sort_key, sort_dir=sort_dir,
        include_suppress=include_suppress, expand=expand)

    has_more_data = False
    if paginate and len(alarms) > page_size:
        alarms.pop(-1)
        has_more_data = True
    elif paginate and len(alarms) > getattr(settings,
                                            'API_RESULT_LIMIT', 1000):
        has_more_data = True

    if paginate:
        return [Alarm(n) for n in alarms], has_more_data
    else:
        return [Alarm(n) for n in alarms]


def alarm_get(request, alarm_id):
    alarm = fmclient(request).alarm.get(alarm_id)
    if not alarm:
        raise ValueError('No match found for alarm_id "%s".' % alarm_id)
    return Alarm(alarm)


class EventLog(base.APIResourceWrapper):
    """Wrapper for Inventory Customer Logs"""

    _attrs = ['uuid',
              'event_log_id',
              'state',
              'entity_type_id',
              'entity_instance_id',
              'timestamp',
              'severity',
              'reason_text',
              'event_log_type',
              'probable_cause',
              'proposed_repair_action',
              'service_affecting',
              'suppression',
              'suppression_status']

    def __init__(self, apiresource):
        super(EventLog, self).__init__(apiresource)


def event_log_list(request, search_opts=None):
    paginate = False

    # If expand is set to true then all the data of the alarm is returned not
    # just a subset.
    expand = False

    if search_opts is None:
        search_opts = {}

    limit = search_opts.get('limit', None)
    marker = search_opts.get('marker', None)
    page_size = stx_base.get_request_page_size(request, limit)

    if 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            limit = page_size + 1

    query = None
    alarms = False
    logs = False
    include_suppress = False

    if "evtType" in search_opts:
        evtType = search_opts.pop('evtType')
        if evtType == FM_ALARM:
            alarms = True
        elif evtType == FM_LOG:
            logs = True

    if "suppression" in search_opts:
        suppression = search_opts.pop('suppression')

        if suppression == FM_SUPPRESS_SHOW:
            include_suppress = True
        elif suppression == FM_SUPPRESS_HIDE:
            include_suppress = False

    if "expand" in search_opts:
        expand = True

    logs = fmclient(request)\
        .event_log.list(q=query,
                        limit=limit,
                        marker=marker,
                        alarms=alarms,
                        logs=logs,
                        include_suppress=include_suppress,
                        expand=expand)

    has_more_data = False
    if paginate and len(logs) > page_size:
        logs.pop(-1)
        has_more_data = True
    elif paginate and len(logs) > getattr(settings, 'API_RESULT_LIMIT', 1000):
        has_more_data = True

    return [EventLog(n) for n in logs], has_more_data


def event_log_get(request, event_log_id):
    log = fmclient(request).event_log.get(event_log_id)
    if not log:
        raise ValueError('No match found for event_log_id "%s".' %
                         event_log_id)
    return EventLog(log)


class EventSuppression(base.APIResourceWrapper):
    """Wrapper for Inventory Alarm Suppression"""

    _attrs = ['uuid',
              'alarm_id',
              'description',
              'suppression_status']

    def __init__(self, apiresource):
        super(EventSuppression, self).__init__(apiresource)


def event_suppression_list(request, include_unsuppressed=False):
    q = []
    if not include_unsuppressed:
        q.append(
            dict(field='suppression_status', value='suppressed', op='eq',
                 type='string'))

    suppression_list = fmclient(request).event_suppression.list(q)

    return [EventSuppression(n) for n in suppression_list]


def event_suppression_update(request, event_suppression_uuid, **kwargs):
    patch = []
    for key, value in kwargs.items():
        patch.append(dict(path='/' + key, value=value, op='replace'))
    return fmclient(request)\
        .event_suppression.update(event_suppression_uuid, patch)
