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
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.generic import TemplateView

from horizon import exceptions
from horizon import tabs
from horizon import views
from openstack_dashboard.api.base import is_service_enabled
from starlingx_dashboard.api import fm
from starlingx_dashboard.api import dc_manager

from starlingx_dashboard.dashboards.admin.fault_management import \
    tabs as project_tabs

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.AlarmsTabs
    template_name = 'admin/fault_management/index.html'
    page_title = _("Fault Management")


class DetailView(views.HorizonTemplateView):
    template_name = 'admin/fault_management/_detail_overview.html'
    page_title = 'Alarm Details'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["alarm"] = self.get_data()
        return context

    def get_data(self):
        if not hasattr(self, "_alarm"):
            alarm_uuid = self.kwargs['id']
            try:
                alarm = fm.alarm_get(self.request, alarm_uuid)

            except Exception:
                redirect = reverse('horizon:admin:fault_management:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'alarm "%s".') % alarm_uuid,
                                  redirect=redirect)

            self._alarm = alarm
        return self._alarm


class EventLogDetailView(views.HorizonTemplateView):
    # Strategy behind this event log detail view is to
    # first retrieve the event_log data, then examine the event's
    # state property, and from that, determine if it should use
    # the _detail_history.html (alarmhistory) template or
    # or use the _detail_log.html (customer log) template

    def get_template_names(self):
        if self.type == "alarmhistory":
            template_name = 'admin/fault_management/_detail_history.html'
        else:
            template_name = 'admin/fault_management/_detail_log.html'
        return template_name

    def _detectEventLogType(self):
        if hasattr(self, "type"):
            return self.type
        if not self._eventlog:
            raise Exception("Cannot determine Event Log type for "
                            "EventLogDetailView.  First retrieve "
                            "Eventlog data")
        if self._eventlog.state == "log":
            self.type = "log"
        elif self._eventlog.state in ["set", "clear"]:
            self.type = "alarmhistory"
        else:
            raise Exception("Invalid state = '{}'.  Cannot "
                            "determine Event log type for "
                            "event log".format(self._eventlog.state))
        return self.type

    def get_context_data(self, **kwargs):
        context = super(EventLogDetailView, self).get_context_data(**kwargs)
        data = self.get_data()
        if self.type == "alarmhistory":
            self.page_title = 'Historical Alarm Details'
            self.template_name = 'admin/fault_management/_detail_history.html'
            context["history"] = data
        else:
            self.page_title = 'Customer Log Detail'
            self.template_name = 'admin/fault_management/_detail_log.html'
            context["log"] = data

        return context

    def get_data(self):
        if not hasattr(self, "_eventlog"):
            uuid = self.kwargs['id']
            try:
                self._eventlog = fm.event_log_get(self.request, uuid)
                self._detectEventLogType()
            except Exception:
                redirect = reverse('horizon:admin:fault_management:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'event log "%s".') % uuid,
                                  redirect=redirect)
        return self._eventlog


class BannerView(TemplateView):
    template_name = 'header/_alarm_banner.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        if not self.request.is_ajax():
            raise exceptions.NotFound()

        if (not self.request.user.is_authenticated() or
                not self.request.user.is_superuser):
            context["alarmbanner"] = False
        elif 'dc_admin' in self.request.META.get('HTTP_REFERER'):
            summaries = self.get_subcloud_data()
            central_summary = self.get_data()
            summaries.append(central_summary)
            context["dc_admin"] = True
            context["alarmbanner"] = True
            context["OK"] = len(
                [s for s in summaries if s.status == 'OK'])
            context["degraded"] = len(
                [s for s in summaries if s.status == 'degraded'])
            context["critical"] = len(
                [s for s in summaries if s.status == 'critical'])
            context["disabled"] = len(
                [s for s in summaries if s.status == 'disabled'])
        elif is_service_enabled(self.request, 'platform'):
            context["summary"] = self.get_data()
            context["alarmbanner"] = True
        return context

    def get_data(self):
        summary = None
        try:
            summary = fm.alarm_summary_get(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve alarm summary.'))
        return summary

    def get_subcloud_data(self):
        return dc_manager.alarm_summary_list(self.request)
