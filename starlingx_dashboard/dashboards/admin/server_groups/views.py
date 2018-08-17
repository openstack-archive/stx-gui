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
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#

"""
Views for managing server groups.
"""

from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.usage import quotas

from starlingx_dashboard.dashboards.admin.server_groups \
    import forms as admin_forms

from starlingx_dashboard.dashboards.admin.server_groups \
    import tables as admin_tables
from starlingx_dashboard.dashboards.admin.server_groups \
    import tabs as admin_tabs


# server groups don't currently support pagination
class IndexView(tables.DataTableView):
    table_class = admin_tables.ServerGroupsTable
    template_name = 'admin/server_groups/index.html'
    page_title = _("Server Groups")

    def get_data(self):
        try:
            server_groups = api.nova.server_group_list(
                self.request, all_projects=True)
        except Exception:
            server_groups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve server groups.'))
        return server_groups


class DetailView(tabs.TabView):
    tab_group_class = admin_tabs.ServerGroupDetailTabs
    template_name = 'admin/server_groups/detail.html'
    page_title = 'Server Group Details'


class CreateView(forms.ModalFormView):
    form_class = admin_forms.CreateForm
    template_name = 'admin/server_groups/create.html'
    success_url = reverse_lazy("horizon:admin:server_groups:index")

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = quotas.tenant_limit_usages(self.request)
        except Exception:
            exceptions.handle(self.request)
        return context


class EditAttachmentsView(tables.DataTableView, forms.ModalFormView):
    table_class = admin_tables.AttachmentsTable
    form_class = admin_forms.AttachForm
    template_name = 'admin/server_groups/attach.html'
    success_url = reverse_lazy("horizon:admin:server_groups:index")

    def get_object(self):
        if not hasattr(self, "_object"):
            volume_id = self.kwargs['volume_id']
            try:
                self._object = api.cinder.volume_get(self.request, volume_id)
            except Exception:
                self._object = None
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume information.'))
        return self._object

    def get_data(self):
        try:
            volumes = self.get_object()
            attachments = [att for att in volumes.attachments if att]
        except Exception:
            attachments = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return attachments

    def get_initial(self):
        try:
            instances, has_more = api.nova.server_list(self.request)
        except Exception:
            instances = []
            exceptions.handle(self.request,
                              _("Unable to retrieve attachment information."))
        return {'volume': self.get_object(),
                'instances': instances}

    def get_form(self):
        if not hasattr(self, "_form"):
            form_class = self.get_form_class()
            self._form = super(EditAttachmentsView, self).get_form(form_class)
        return self._form

    def get_context_data(self, **kwargs):
        context = super(EditAttachmentsView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        volume = self.get_object()
        if volume and volume.status == 'available':
            context['show_attach'] = True
        else:
            context['show_attach'] = False
        context['volume'] = volume
        if self.request.is_ajax():
            context['hide'] = True
        return context

    def get(self, request, *args, **kwargs):
        # Table action handling
        handled = self.construct_tables()
        if handled:
            return handled
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)
