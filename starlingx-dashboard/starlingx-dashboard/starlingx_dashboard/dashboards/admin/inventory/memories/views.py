#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.memories.forms import \
    AddMemoryProfile
from starlingx_dashboard.dashboards.admin.inventory.memories.forms import \
    UpdateMemory

LOG = logging.getLogger(__name__)


class UpdateMemoryView(forms.ModalFormView):
    form_class = UpdateMemory
    template_name = 'admin/inventory/memorys/edit_hp_memory.html'
    success_url = 'horizon:admin:inventory:detail'
    context_object_name = "memorys"

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            host_id = self.kwargs['host_id']
            try:
                host = stx_api.sysinv.host_get(self.request, host_id)
                host.memorys = stx_api.sysinv.host_memory_list(self.request,
                                                               host.uuid)
                host.nodes = \
                    stx_api.sysinv.host_node_list(self.request, host.uuid)
                self._object = host
                self._object.host_id = host_id
            except Exception as e:
                LOG.exception(e)
                redirect = reverse("horizon:project:networks:detail",
                                   args=(host_id))
                msg = _('Unable to retrieve memory details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateMemoryView, self).get_context_data(
            **kwargs)
        host = self._get_object()
        context['host_id'] = host.host_id
        return context

    def get_initial(self):
        host = self._get_object()

        return {'host': host,
                'host_id': host.host_id, }


class AddMemoryProfileView(forms.ModalFormView):
    form_class = AddMemoryProfile
    template_name = 'admin/inventory/memorys/createprofile.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_myhost_data(self):
        if not hasattr(self, "_host"):
            host_id = self.kwargs['host_id']
            try:
                host = stx_api.sysinv.host_get(self.request, host_id)
                host.nodes = stx_api.sysinv.host_node_list(self.request,
                                                           host.uuid)
                host.memory = \
                    stx_api.sysinv.host_memory_list(self.request, host.uuid)

                numa_node_tuple_list = []
                for m in host.memory:
                    node = stx_api.sysinv.host_node_get(self.request,
                                                        m.inode_uuid)
                    numa_node_tuple_list.append((node.numa_node, m))

                host.numa_nodes = numa_node_tuple_list
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'host "%s".') % host_id,
                                  redirect=redirect)
            self._host = host
        return self._host

    def get_context_data(self, **kwargs):
        context = super(AddMemoryProfileView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        context['host'] = self.get_myhost_data()
        return context

    def get_initial(self):
        initial = super(AddMemoryProfileView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        return initial
