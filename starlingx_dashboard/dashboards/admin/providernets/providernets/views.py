# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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


from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.providernets.providernets import \
    forms as providernet_forms
from openstack_dashboard.dashboards.admin.providernets.providernets.ranges \
    import tables as range_tables
from openstack_dashboard.dashboards.admin.providernets.providernets.ranges \
    import views as range_views
from openstack_dashboard.dashboards.admin.providernets.providernets import \
    tables as providernet_tables

LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = providernet_forms.CreateProviderNetwork
    template_name = 'admin/providernets/providernets/create.html'
    success_url = reverse_lazy('horizon:admin:providernets:index')


class DetailView(tables.MultiTableView):
    table_classes = (range_tables.ProviderNetworkRangeTable,
                     providernet_tables.ProviderNetworkTenantNetworkTable)
    template_name = 'admin/providernets/providernets/detail.html'
    failure_url = reverse_lazy('horizon:admin:providernets:index')
    page_title = '{{ "Provider Network Detail: "|add:providernet.name }}'

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
            providernet_id = self.kwargs['providernet_id']
            # self.table.kwargs['providernet'] = self._get_data()
            networks = api.neutron.provider_network_list_tenant_networks(
                self.request, providernet_id=providernet_id)
        except Exception:
            networks = []
            msg = _('Tenant network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return networks

    def get_provider_network_ranges_data(self):
        try:
            providernet_id = self.kwargs['providernet_id']
            # self.table.kwargs['providernet'] = self._get_data()
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

    def _get_data(self):
        if not hasattr(self, "_providernet"):
            try:
                providernet_id = self.kwargs['providernet_id']
                providernet = api.neutron.provider_network_get(
                    self.request, providernet_id)
                providernet.set_id_as_name_if_empty(length=0)
            except Exception:
                redirect = self.failure_url
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'provider network "%s".') % providernet_id,
                                  redirect=redirect)
            self._providernet = providernet
        return self._providernet

    def _get_nova_data(self):
        if not hasattr(self, "_providernet_nova"):
            try:
                providernet_id = self.kwargs['providernet_id']
                providernet_nova = api.nova.provider_network_get(
                    self.request, providernet_id)
            except Exception as ex:
                # redirect = self.failure_url
                # exceptions.handle(self.request,
                #                 _('Unable to retrieve details for '
                #                   'provider network "%s".') % providernet_id,
                #                   redirect=redirect)
                LOG.error(ex)
                providernet_nova = None

            self._providernet_nova = providernet_nova
        return self._providernet_nova

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["providernet"] = self._get_data()
        context["nova_providernet"] = self._get_nova_data()
        return context


class UpdateView(forms.ModalFormView):
    form_class = providernet_forms.UpdateProviderNetwork
    template_name = 'admin/providernets/providernets/update.html'
    success_url = reverse_lazy('horizon:admin:providernets:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["providernet_id"] = self.kwargs['providernet_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            providernet_id = self.kwargs['providernet_id']
            try:
                self._object = api.neutron.provider_network_get(
                    self.request, providernet_id)
            except Exception:
                redirect = self.success_url
                msg = _('Unable to retrieve provider network details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        providernet = self._get_object()
        return {'id': providernet['id'],
                'name': providernet['name'],
                'description': providernet['description'],
                'type': providernet['type'],
                'mtu': providernet['mtu'],
                'vlan_transparent': providernet['vlan_transparent']}


class CreateRangeView(range_views.CreateView):
    template_name = 'admin/providernets/providernets/add_range.html'
    success_url = 'horizon:admin:providernets:index'
    failure_url = 'horizon:admin:providernets:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_failure_url(self):
        return reverse(self.failure_url)
