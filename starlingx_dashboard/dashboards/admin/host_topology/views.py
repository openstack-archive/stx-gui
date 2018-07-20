#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import json
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View  # noqa

from horizon import exceptions
from horizon import tabs
from horizon.utils import settings as utils_settings
from horizon import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.host_topology import\
    tabs as topology_tabs
from openstack_dashboard.dashboards.admin.inventory import\
    views as i_views
from openstack_dashboard.usage import quotas

LOG = logging.getLogger(__name__)


class HostDetailView(i_views.DetailView):
    tab_group_class = topology_tabs.HostDetailTabs
    template_name = 'admin/host_topology/detail/tabbed_detail.html'

    def get_data(self):
        if not hasattr(self, "_host"):
            try:
                host = super(HostDetailView, self).get_data()

                alarms = []
                try:
                    alarms = api.sysinv.alarm_list(self.request)
                except Exception as ex:
                    exceptions.handle(ex)
                # Filter out unrelated alarms
                host.alarms = topology_tabs.get_alarms_for_entity(
                    alarms, host.hostname)
                # Sort alarms by severity
                host.alarms.sort(key=lambda a: (a.severity))

            except Exception as ex:
                LOG.exception(ex)
                raise
            self._host = host
        return self._host


class ProvidernetDetailView(tabs.TabbedTableView):
    tab_group_class = topology_tabs.ProvidernetDetailTabs
    template_name = 'admin/host_topology/detail/tabbed_detail.html'
    failure_url = reverse_lazy('horizon:admin:host_topology:index')

    def get_context_data(self, **kwargs):
        context = super(ProvidernetDetailView, self).get_context_data(**kwargs)
        context["providernet"] = self.get_data()
        context["nova_providernet"] = self.get_nova_data()
        return context

    def get_data(self):
        if not hasattr(self, "_providernet"):
            try:
                providernet_id = self.kwargs['providernet_id']
                providernet = api.neutron.provider_network_get(
                    self.request, providernet_id)
                providernet.set_id_as_name_if_empty(length=0)

                alarms = api.sysinv.alarm_list(self.request)
                # Filter out unrelated alarms
                providernet.alarms = \
                    topology_tabs.get_alarms_for_entity(alarms,
                                                        providernet.id) + \
                    topology_tabs.get_alarms_for_entity(alarms,
                                                        providernet.name)
                # Sort alarms by severity
                providernet.alarms.sort(key=lambda a: (a.severity))

            except Exception:
                redirect = self.failure_url
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'provider network "%s".') % providernet_id,
                                  redirect=redirect)
            self._providernet = providernet
        return self._providernet

    def get_nova_data(self):
        if not hasattr(self, "_providernet_nova"):
            try:
                providernet_id = self.kwargs['providernet_id']
                providernet_nova = api.nova.provider_network_get(
                    self.request, providernet_id)
            except Exception:
                redirect = self.failure_url
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'provider network "%s".') % providernet_id,
                                  redirect=redirect)

            self._providernet_nova = providernet_nova
        return self._providernet_nova

    def get_tabs(self, request, *args, **kwargs):
        providernet = self.get_data()
        nova_providernet = self.get_nova_data()
        return self.tab_group_class(
            request, providernet=providernet,
            nova_providernet=nova_providernet, **kwargs)


class HostTopologyView(views.HorizonTemplateView):
    template_name = 'admin/host_topology/index.html'
    page_title = _("Provider Network Topology")

    def _has_permission(self, policy):
        has_permission = True
        # policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)
        policy_check = utils_settings.import_setting("POLICY_CHECK_FUNCTION")

        if policy_check:
            has_permission = policy_check(policy, self.request)

        return has_permission

    def _quota_exceeded(self, quota):
        usages = quotas.tenant_quota_usages(self.request)
        available = usages[quota]['available']
        return available <= 0

    def get_context_data(self, **kwargs):
        context = super(HostTopologyView, self).get_context_data(**kwargs)

        context['launch_instance_allowed'] = self._has_permission(
            (("compute", "compute:create"),))
        context['instance_quota_exceeded'] = self._quota_exceeded('instances')
        return context


class JSONView(View):

    @property
    def is_router_enabled(self):
        network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
        return network_config.get('enable_router', True)

    def add_resource_url(self, view, resources):
        tenant_id = self.request.user.tenant_id
        for resource in resources:
            if (resource.get('tenant_id')
                    and tenant_id != resource.get('tenant_id')):
                continue
            resource['url'] = reverse(view, None, [str(resource['id'])])

    def _check_router_external_port(self, ports, router_id, network_id):
        for port in ports:
            if (port['network_id'] == network_id
                    and port['device_id'] == router_id):
                return True
        return False

    def _get_alarms(self, request):
        alarms = []
        try:
            alarms = api.sysinv.alarm_list(request)
        except Exception as ex:
            exceptions.handle(ex)

        data = [a.to_dict() for a in alarms]
        return data

    def _get_hosts(self, request):
        hosts = []
        try:
            hosts = api.sysinv.host_list(request)
        except Exception as ex:
            exceptions.handle(ex)

        data = []
        for host in hosts:
            host_data = host.to_dict()
            try:
                host_data['ports'] = [
                    p.to_dict() for p in
                    api.sysinv.host_port_list(request, host.uuid)]

                host_data['interfaces'] = [
                    i.to_dict() for i in
                    api.sysinv.host_interface_list(request, host.uuid)]

                host_data['lldpneighbours'] = [
                    n.to_dict() for n in
                    api.sysinv.host_lldpneighbour_list(request, host.uuid)]

                # Set the value for neighbours field for each port in the host.
                # This will be referenced in Interfaces table
                for p in host_data['ports']:
                    p['neighbours'] = \
                        [n['port_identifier'] for n in
                         host_data['lldpneighbours']
                         if n['port_uuid'] == p['uuid']]

            except Exception as ex:
                exceptions.handle(ex)

            data.append(host_data)
        return data

    def _get_pnets(self, request):
        pnets = []
        try:
            pnets = api.neutron.provider_network_list(request)
        except Exception as ex:
            exceptions.handle(ex)
        data = [p.to_dict() for p in pnets]
        return data

    def get(self, request, *args, **kwargs):
        data = {'hosts': self._get_hosts(request),
                'networks': self._get_pnets(request),
                'alarms': self._get_alarms(request), }
        json_string = json.dumps(data, ensure_ascii=False)
        return HttpResponse(json_string, content_type='text/json')
