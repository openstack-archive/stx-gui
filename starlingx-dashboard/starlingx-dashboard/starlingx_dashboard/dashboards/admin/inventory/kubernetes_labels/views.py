#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2019 Wind River Systems, Inc.
# Copyright (C) 2019 Intel Corporation
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.kubernetes_labels.forms \
    import AssignLabel

LOG = logging.getLogger(__name__)


class AssignLabelView(forms.ModalFormView):
    form_class = AssignLabel
    template_name = 'admin/inventory/kubelabels/assignkubelabel.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AssignLabelView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(AssignLabelView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = stx_api.sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['host_uuid'] = host.uuid
        return initial
