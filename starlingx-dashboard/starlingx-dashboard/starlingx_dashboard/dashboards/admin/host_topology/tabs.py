# Copyright (c) 2016-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api as api

from starlingx_dashboard.dashboards.admin.datanets.datanets import \
    tables as pn_tables
from starlingx_dashboard.dashboards.admin.host_topology import \
    tables as tables
from starlingx_dashboard.dashboards.admin.inventory import \
    tabs as i_tabs

LOG = logging.getLogger(__name__)


def get_alarms_for_entity(alarms, entity_str):
    matched = []
    for alarm in alarms:
        for _id in alarm.entity_instance_id.split('.'):
            try:
                if entity_str == _id.split('=')[1]:
                    matched.append(alarm)
            except Exception:
                # malformed entity_instance_id
                pass
    return matched


class AlarmsTab(tabs.TableTab):
    table_classes = (tables.AlarmsTable,)
    name = _("Related Alarms")
    slug = "alarm_tab"
    template_name = ("admin/host_topology/detail/_detail_alarms.html")

    def get_alarms_data(self):
        entity = self.tab_group.kwargs.get('host')
        if not entity:
            entity = self.tab_group.kwargs.get('datanet')
        return entity.alarms


class InterfacesTab(i_tabs.InterfacesTab):
    table_classes = (tables.InterfacesTable, )


class HostDetailTabs(tabs.TabGroup):
    slug = "host_details"
    tabs = (i_tabs.OverviewTab, AlarmsTab, InterfacesTab,
            i_tabs.LldpTab)
    sticky = True


class OverviewTab(tabs.TableTab):
    table_classes = (tables.ProviderNetworkRangeTable,
                     pn_tables.ProviderNetworkTenantNetworkTable)
    template_name = 'admin/host_topology/detail/datanet.html'
    name = "Data Network Detail"
    slug = 'datanet_details_overview'
    failure_url = reverse_lazy('horizon:admin:host_topology:index')

    def _get_tenant_list(self):
        if not hasattr(self, "_tenants"):
            try:
                tenants, has_more = api.keystone.tenant_list(self.request)  # noqa pylint: disable=unused-variable
            except Exception:
                tenants = []
                msg = _('Unable to retrieve instance project information.')
                exceptions.handle(self.request, msg)
            tenant_dict = OrderedDict([(t.id, t) for t in tenants])
            self._tenants = tenant_dict
        return self._tenants

    def get_tenant_networks_data(self):
        # TODO(datanetworks): need to refactor for Stein
        networks = []
        return networks

    def get_provider_network_ranges_data(self):
        ranges = []
        return ranges

    def get_context_data(self, request):
        context = super(OverviewTab, self).get_context_data(request)
        try:
            context['datanet'] = self.tab_group.kwargs['datanet']
            context['nova_datanet'] = \
                self.tab_group.kwargs['nova_datanet']
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve datanet details.'))
        return context


class ProvidernetDetailTabs(tabs.TabGroup):
    slug = "pnet_details"
    tabs = (OverviewTab, AlarmsTab)
    sticky = True
