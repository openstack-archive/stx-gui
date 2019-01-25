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


from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.datanets.datanets.ranges \
    import forms as range_forms
from starlingx_dashboard.dashboards.admin.datanets.datanets.ranges \
    import tabs as range_tabs


class CreateView(forms.ModalFormView):
    form_class = range_forms.CreateProviderNetworkRange
    template_name = 'admin/datanets/datanets/ranges/create.html'
    success_url = 'horizon:admin:datanets:datanets:detail'
    failure_url = 'horizon:admin:datanets:datanets:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['providernet_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['providernet_id'],))

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                providernet_id = self.kwargs["providernet_id"]
                self._object = stx_api.neutron.provider_network_get(
                    self.request, providernet_id)
            except Exception:
                redirect = reverse(self.failure_url,
                                   args=(self.kwargs['providernet_id'],))
                msg = _("Unable to retrieve provider network.")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['providernet_id'] = self.kwargs["providernet_id"]
        context['providernet'] = self.get_object()
        return context

    def get_initial(self):
        providernet = self.get_object()
        return {"providernet_id": providernet.id,
                "providernet_name": providernet.name,
                "providernet_type": providernet.type}


class DetailView(tabs.TabView):
    tab_group_class = range_tabs.ProviderNetworkRangeDetailTabs
    template_name = 'admin/datanets/datanets/ranges/detail.html'
    page_title = '{{ providernet_range.name }}'

    def _get_object(self):
        if not hasattr(self, "_object"):
            providernet_range_id = \
                self.kwargs['providernet_range_id']
            try:
                self._object = stx_api.neutron.provider_network_range_get(
                    self.request, providernet_range_id)
            except Exception:
                redirect = \
                    reverse("horizon:admin:datanets:datanets:detail",
                            args=(
                                self.kwargs['providernet_id'],))
                msg = _('Unable to retrieve provider network range details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        providernet_range = self._get_object()

        pnet_name = self.get_providernet_name(providernet_range.providernet_id)
        breadcrumb = [
            (pnet_name,
             reverse('horizon:admin:datanets:datanets:detail',
                     args=(providernet_range.providernet_id,))),
            (_("Segmentation Ranges"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context["providernet_range"] = providernet_range
        return context

    @memoized.memoized_method
    def get_providernet_name(self, providernet_id):
        try:
            providernet = stx_api.neutron.provider_network_get(self.request,
                                                               providernet_id)
            providernet.set_id_as_name_if_empty(length=0)
        except Exception:
            providernet = {}
            msg = _('Unable to retrieve providernet details.')
            exceptions.handle(self.request, msg)
        return providernet.name

    def get_tabs(self, request, *args, **kwargs):
        providernet_range = self._get_object()
        return self.tab_group_class(
            request, providernet_range=providernet_range, **kwargs)


class UpdateView(forms.ModalFormView):
    form_class = range_forms.UpdateProviderNetworkRange
    template_name = 'admin/datanets/datanets/ranges/update.html'
    context_object_name = 'providernet_range'
    success_url = 'horizon:admin:datanets:datanets:detail'

    def get_success_url(self):
        value = reverse(self.success_url,
                        args=(self.kwargs['providernet_id'],))
        return value

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            providernet_range_id = self.kwargs['providernet_range_id']
            try:
                self._object = stx_api.neutron.provider_network_range_get(
                    self.request, providernet_range_id)
            except Exception:
                redirect = \
                    reverse("horizon:admin:datanets:datanets:detail",
                            args=(self.kwargs['providernet_id'],))
                msg = _('Unable to retrieve provider network range details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        providernet_range = self._get_object()
        context['providernet_range_id'] = providernet_range['id']
        context['providernet_id'] = providernet_range['providernet_id']
        context['providernet_range'] = providernet_range
        return context

    def get_initial(self):
        providernet_range = self._get_object()
        data = {'providernet_id': self.kwargs['providernet_id'],
                'providernet_range_id': self.kwargs['providernet_range_id'],
                'name': providernet_range['name'],
                'description': providernet_range['description'],
                'minimum': providernet_range['minimum'],
                'maximum': providernet_range['maximum'],
                'tenant_id': providernet_range['tenant_id'],
                'shared': providernet_range['shared']}
        if 'vxlan' in providernet_range:
            vxlan = providernet_range['vxlan']
            data['mode'] = vxlan['mode']
            data['group'] = vxlan['group']
            data['port'] = vxlan['port']
            data['ttl'] = vxlan['ttl']
        return data
