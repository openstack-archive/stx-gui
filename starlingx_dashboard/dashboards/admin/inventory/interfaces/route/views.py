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

from horizon import forms

from starlingx_dashboard.dashboards.admin.inventory.interfaces.route import \
    forms as route_forms

LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = route_forms.CreateRoute
    template_name = 'admin/inventory/interfaces/route/create.html'
    success_url = 'horizon:admin:inventory:viewinterface'
    failure_url = 'horizon:admin:inventory:viewinterface'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],
                             self.kwargs['interface_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],
                             self.kwargs['interface_id'],))

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['interface_id'] = self.kwargs['interface_id']
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        return {'interface_id': self.kwargs['interface_id'],
                'host_id': self.kwargs['host_id']}
