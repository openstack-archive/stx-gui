# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import forms as project_forms

LOG = logging.getLogger(__name__)


class EditView(forms.ModalFormView):
    form_class = project_forms.EditParam
    template_name = 'admin/inventory/storages/lvg/edit.html'
    success_url = 'horizon:admin:inventory:localvolumegroupdetail'

    def get_form(self, form_class):
        self.form = super(self.__class__, self).get_form(form_class)
        return self.form

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        context['key'] = self.kwargs['key']
        context.update(self.form.get_lvg_lvm_info(self.kwargs['lvg_id']))
        return context

    def get_initial(self):
        lvg_id = self.kwargs['lvg_id']
        key = self.kwargs['key']
        try:
            params = api.sysinv.host_lvg_get_params(
                self.request, lvg_id, raw=True)
        except Exception:
            params = {}
            exceptions.handle(self.request,
                              _("Unable to retrieve lvg parameter data."))

        return {'lvg_id': lvg_id,
                'key': key,
                'value': params.get(key, '')}

    def get_success_url(self):
        return reverse(self.__class__.success_url,
                       args=(self.kwargs['lvg_id'],))
