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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.datanets.datanets import \
    forms as datanet_forms
from starlingx_dashboard.dashboards.admin.datanets.datanets.ranges \
    import tables as range_tables
from starlingx_dashboard.dashboards.admin.datanets.datanets import \
    tables as providernet_tables

LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = datanet_forms.CreateDataNetwork
    template_name = 'admin/datanets/datanets/create.html'
    success_url = reverse_lazy('horizon:admin:datanets:index')


class DetailView(tables.MultiTableView):
    table_classes = (range_tables.ProviderNetworkRangeTable,
                     providernet_tables.ProviderNetworkTenantNetworkTable)
    template_name = 'admin/datanets/datanets/detail.html'
    failure_url = reverse_lazy('horizon:admin:datanets:index')
    page_title = '{{ "Data Network Detail: "|add:datanet.name }}'

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
        try:
            # TODO(datanets): get tenant networks when in upstream neutron
            networks = []
        except Exception:
            networks = []
            msg = _('Tenant network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return networks

    def get_provider_network_ranges_data(self):
        try:
            # TODO(datanetworks) force ranges to []
            ranges = []
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
                providernet = stx_api.sysinv.data_network_get(
                    self.request, providernet_id)
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
            # TODO(datanetworks): depends on upstream support
            self._providernet_nova = None
        return self._providernet_nova

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["datanet"] = self._get_data()
        context["nova_providernet"] = self._get_nova_data()
        return context


class UpdateView(forms.ModalFormView):
    form_class = datanet_forms.UpdateDataNetwork
    template_name = 'admin/datanets/datanets/update.html'
    success_url = reverse_lazy('horizon:admin:datanets:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["providernet_id"] = self.kwargs['providernet_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            providernet_id = self.kwargs['providernet_id']
            try:
                self._object = stx_api.sysinv.data_network_get(
                    self.request, providernet_id)
            except Exception:
                redirect = self.success_url
                msg = _('Unable to retrieve data network details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        datanet = self._get_object()
        return {'id': datanet.id,
                'name': datanet.name,
                'network_type': datanet.network_type,
                'mtu': datanet.mtu,
                'description': datanet.description,
                }
