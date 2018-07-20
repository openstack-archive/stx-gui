# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.host_topology import \
    tables as tables
from openstack_dashboard.dashboards.admin.inventory import \
    tabs as i_tabs
from openstack_dashboard.dashboards.admin.providernets.providernets import \
    tables as pn_tables

LOG = logging.getLogger(__name__)


def get_alarms_for_entity(alarms, entity_str):
    matched = []
    for alarm in alarms:
        for id in alarm.entity_instance_id.split('.'):
            try:
                if entity_str == id.split('=')[1]:
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
            entity = self.tab_group.kwargs.get('providernet')
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
    template_name = 'admin/host_topology/detail/providernet.html'
    name = "Provider Network Detail"
    slug = 'providernet_details_overview'
    failure_url = reverse_lazy('horizon:admin:host_topology:index')

    def _get_tenant_list(self):
        if not hasattr(self, "_tenants"):
            try:
                tenants, has_more = api.keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve instance project information.')
                exceptions.handle(self.request, msg)
            tenant_dict = OrderedDict([(t.id, t) for t in tenants])
            self._tenants = tenant_dict
        return self._tenants

    def get_tenant_networks_data(self):
        try:
            providernet_id = self.tab_group.kwargs['providernet_id']
            networks = api.neutron.provider_network_list_tenant_networks(
                self.request, providernet_id=providernet_id)
        except Exception:
            networks = []
            msg = _('Tenant network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return networks

    def get_provider_network_ranges_data(self):
        try:
            providernet_id = self.tab_group.kwargs['providernet_id']
            ranges = api.neutron.provider_network_range_list(
                self.request, providernet_id=providernet_id)
        except Exception:
            ranges = []
            msg = _('Segmentation id range list can not be retrieved.')
            exceptions.handle(self.request, msg)
        tenant_dict = self._get_tenant_list()
        for r in ranges:
            r.set_id_as_name_if_empty()
            # Set tenant name
            tenant = tenant_dict.get(r.tenant_id, None)
            r.tenant_name = getattr(tenant, 'name', None)
        return ranges

    def get_context_data(self, request):
        context = super(OverviewTab, self).get_context_data(request)
        try:
            context['providernet'] = self.tab_group.kwargs['providernet']
            context['nova_providernet'] = \
                self.tab_group.kwargs['nova_providernet']
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve providernet details.'))
        return context


class ProvidernetDetailTabs(tabs.TabGroup):
    slug = "pnet_details"
    tabs = (OverviewTab, AlarmsTab)
    sticky = True
