# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#


from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.fault_management import tables

ALARMS_SUPPRESSION_FILTER_GROUP = 0
EVENT_SUPPRESSION_FILTER_GROUP = 1


class ActiveAlarmsTab(tabs.TableTab):
    table_classes = (tables.AlarmsTable,)
    name = _("Active Alarms")
    slug = "alarms"
    template_name = 'admin/fault_management/_active_alarms.html'

    def has_more_data(self, table):
        return self._more

    def get_limit_count(self, table):
        return self._limit

    def getTableFromName(self, tableName):
        table = self._tables[tableName]
        return table

    def set_suppression_filter(self, disabled_status):
        alarmsTable = self.getTableFromName('alarms')
        filter_action = alarmsTable._meta._filter_action
        filter_action.set_disabled_filter_field_for_group(
            ALARMS_SUPPRESSION_FILTER_GROUP, disabled_status)
        filter_action.updateFromRequestDataToSession(self.request)

    def get_context_data(self, request):
        context = super(ActiveAlarmsTab, self).get_context_data(request)

        summary = stx_api.fm.alarm_summary_get(
            self.request, include_suppress=False)
        context["total"] = summary.critical + summary.major + summary.minor \
            + summary.warnings
        context["summary"] = summary

        events_types = self.get_event_suppression_data()
        suppressed_events_types = len([etype for etype
                                       in events_types
                                       if etype.suppression_status ==
                                       'suppressed'])

        alarms_table = self.getTableFromName('alarms')

        suppress_filter = self.get_filters()
        suppress_filter_state = suppress_filter.get('suppression')

        hidden_found = 'hidden' in alarms_table.columns["suppression_status"].\
            classes

        if not hidden_found:
            if suppressed_events_types == 0:
                self.set_suppression_filter('disabled')
                alarms_table.columns["suppression_status"]\
                    .classes.append('hidden')
            elif suppress_filter_state == stx_api.fm.FM_SUPPRESS_HIDE:
                self.set_suppression_filter('enabled')
                alarms_table.columns["suppression_status"].classes\
                    .append('hidden')
        else:
            if suppressed_events_types == 0:
                self.set_suppression_filter('disabled')
            else:
                self.set_suppression_filter('enabled')
                if suppress_filter_state == stx_api.fm.FM_SUPPRESS_SHOW:
                    alarms_table.columns["suppression_status"].classes\
                        .remove('hidden')

        return context

    def get_filters(self, filters=None):

        filters = filters or {}
        alarmsTable = self.getTableFromName('alarms')
        filter_action = alarmsTable._meta._filter_action
        filter_action.updateFromRequestDataToSession(self.request)
        filter_field = filter_action.get_filter_field(self.request)

        if filter_field:
            suppression = filter_action.get_filter_field_for_group(0)
            filters["suppression"] = suppression

        return filters

    def get_alarms_data(self):
        search_opts = {}
        # get retrieve parameters from request/session env
        limit = \
            self.request.GET.get(tables.AlarmsTable.Meta.limit_param,
                                 None)

        search_opts = self.get_filters()
        search_opts.update({
                           'paginate': True,
                           'sort_key': 'severity,entity_instance_id',
                           'sort_dir': 'asc'})

        alarms = []
        try:
            if 'paginate' in search_opts:
                alarms, self._more = stx_api.fm.alarm_list(
                    self.request, search_opts=search_opts)
            else:
                alarms = stx_api.fm.alarm_list(
                    self.request, search_opts=search_opts)
            self._limit = limit
        except Exception:
            self._more = False
            self._limit = None
            exceptions.handle(self.request,
                              _('Unable to retrieve alarms list.'))
        return alarms

    def get_event_suppression_data(self):
        event_types = []

        try:
            if 'suppression_list' not in self.tab_group.kwargs:
                self.tab_group.kwargs['suppression_list'] = \
                    stx_api.fm.event_suppression_list(self.request)
            event_types = self.tab_group.kwargs['suppression_list']
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve event suppression table'
                                ' list.'))
        return event_types


class EventLogTab(tabs.TableTab):
    table_classes = (tables.EventLogsTable,)
    name = _("Events")
    slug = "eventLogs"
    template_name = 'admin/fault_management/_summary.html'
    preload = False

    def has_more_data(self, table):
        return self._more

    def get_limit_count(self, table):
        return self._limit

    def getTableFromName(self, tableName):
        table = self._tables[tableName]
        return table

    def set_suppression_filter(self, disabled_status):
        alarmsTable = self.getTableFromName('eventLogs')
        filter_action = alarmsTable._meta._filter_action
        filter_action.set_disabled_filter_field_for_group(
            EVENT_SUPPRESSION_FILTER_GROUP, disabled_status)
        filter_action.updateFromRequestDataToSession(self.request)

    def get_context_data(self, request):
        context = super(EventLogTab, self).get_context_data(request)

        events_types = self.get_event_suppression_data()
        suppressed_events_types = len([etype for etype in events_types
                                      if etype.suppression_status ==
                                       'suppressed'])

        event_log_table = self.getTableFromName('eventLogs')

        filters = self.get_filters({'marker': None,
                                    'limit': None,
                                    'paginate': True})

        suppress_filter_state = filters.get('suppression')

        hidden_found = 'hidden' in event_log_table\
            .columns["suppression_status"].classes

        if not hidden_found:
            if suppressed_events_types == 0:
                self.set_suppression_filter('disabled')
                event_log_table.columns["suppression_status"]\
                    .classes.append('hidden')
            elif suppress_filter_state == stx_api.fm.FM_SUPPRESS_HIDE:
                self.set_suppression_filter('enabled')
                event_log_table.columns["suppression_status"].\
                    classes.append('hidden')
        else:
            if suppressed_events_types == 0:
                self.set_suppression_filter('disabled')
            else:
                self.set_suppression_filter('enabled')
                if suppress_filter_state == stx_api.fm.FM_SUPPRESS_SHOW:
                    event_log_table.columns["suppression_status"]\
                        .classes.remove('hidden')

        return context

    def get_filters(self, filters):

        eventLogsTable = self.getTableFromName('eventLogs')
        filter_action = eventLogsTable._meta._filter_action
        filter_action.updateFromRequestDataToSession(self.request)
        filter_field = filter_action.get_filter_field(self.request)

        if filter_field:
            filters["evtType"] = filter_action.get_filter_field_for_group(0)
            filters["suppression"] = filter_action\
                .get_filter_field_for_group(1)

        return filters

    def get_eventLogs_data(self):

        # get retrieve parameters from request/session env
        marker = \
            self.request.GET.get(tables.EventLogsTable.Meta.pagination_param,
                                 None)
        limit = \
            self.request.GET.get(tables.EventLogsTable.Meta.limit_param,
                                 None)
        search_opts = self.get_filters({'marker': marker,
                                        'limit': limit,
                                        'paginate': True})
        events = []

        try:
            # now retrieve data from rest API
            events, self._more = \
                stx_api.fm.event_log_list(self.request,
                                          search_opts=search_opts)
            self._limit = limit
            return events

        except Exception:
            events = []
            self._more = False
            self._limit = None
            exceptions.handle(self.request,
                              _('Unable to retrieve Event Log list.'))

        return events

    def get_event_suppression_data(self):
        event_types = []

        try:
            if 'suppression_list' not in self.tab_group.kwargs:
                self.tab_group.kwargs['suppression_list'] = \
                    stx_api.fm.event_suppression_list(self.request)
            event_types = self.tab_group.kwargs['suppression_list']
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve event suppression \
                               table list.'))
        return event_types


class EventsSuppressionTab(tabs.TableTab):
    table_classes = (tables.EventsSuppressionTable,)
    name = _("Events Suppression")
    slug = "eventsSuppression"
    template_name = 'admin/fault_management/_summary.html'
    preload = False

    def get_eventsSuppression_data(self):
        event_suppression_list = []

        try:
            if 'suppression_list' not in self.tab_group.kwargs:
                self.tab_group.kwargs['suppression_list'] = \
                    stx_api.fm.event_suppression_list(self.request)
            event_suppression_list = self.tab_group.kwargs['suppression_list']
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve event suppression \
                              list\'s.'))

        event_suppression_list.sort(key=lambda a: (a.alarm_id))

        return event_suppression_list


class AlarmsTabs(tabs.TabGroup):
    slug = "alarms_tabs"
    tabs = (ActiveAlarmsTab, EventLogTab, EventsSuppressionTab)
    sticky = True
