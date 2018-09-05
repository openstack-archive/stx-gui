# Copyright 2015 Wind River Systems, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.system_config.address_pools import \
    forms as address_pool_forms
from starlingx_dashboard.dashboards.admin.system_config.address_pools import \
    tables as address_pool_tables

LOG = logging.getLogger(__name__)


class CreateAddressPoolView(forms.ModalFormView):
    form_class = address_pool_forms.CreateAddressPool
    template_name = 'admin/system_config/address_pools/create.html'
    success_url = 'horizon:admin:system_config:index'
    failure_url = 'horizon:admin:system_config:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_failure_url(self):
        return reverse(self.failure_url)


class UpdateAddressPoolView(forms.ModalFormView):
    form_class = address_pool_forms.UpdateAddressPool
    template_name = 'admin/system_config/address_pools/update.html'
    success_url = 'horizon:admin:system_config:index'
    failure_url = 'horizon:admin:system_config:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_failure_url(self):
        return reverse(self.failure_url)

    def get_context_data(self, **kwargs):
        context = super(UpdateAddressPoolView, self).get_context_data(**kwargs)
        context["address_pool_uuid"] = self.kwargs['address_pool_uuid']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            address_pool_uuid = self.kwargs['address_pool_uuid']
            try:
                self._object = stx_api.sysinv.address_pool_get(
                    self.request, address_pool_uuid)
            except Exception:
                redirect = self.success_url
                msg = _('Unable to retrieve address pool details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        pool = self._get_object()
        return {'id': pool.uuid,
                'name': pool.name,
                'network': pool.network + "/" + str(pool.prefix),
                'order': pool.order,
                'ranges': address_pool_tables.get_ranges_column(pool)}
