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
from horizon.utils import memoized
from horizon import views

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.ports.forms import \
    UpdatePort

LOG = logging.getLogger(__name__)


class UpdateView(forms.ModalFormView):
    form_class = UpdatePort
    template_name = 'admin/inventory/ports/update.html'
    context_object_name = 'port'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            port_id = self.kwargs['port_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_port_get(self.request,
                                                            port_id)
                self._object.host_id = host_id
            except Exception:
                redirect = reverse("horizon:project:networks:detail",
                                   args=(host_id))
                msg = _('Unable to retrieve port details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        port = self._get_object()
        context['port_id'] = port.uuid
        context['host_id'] = port.host_id
        return context

    def get_initial(self):
        port = self._get_object()
        name = port.get_port_display_name()
        if port.autoneg:
            autonegbool = (port.autoneg.lower() == 'yes')
            autoneg = port.autoneg.lower()
        else:
            autonegbool = False
            autoneg = 'na'
        return {'host_uuid': port.host_uuid,
                'host_id': port.host_id,
                'id': port.uuid,
                'name': port.name,
                'newname': name,
                'oldname': name,
                # 'speed': port.speed,  # to be added in future
                'autoneg': autoneg,
                'autonegbool': autonegbool}


class DetailView(views.HorizonTemplateView):
    template_name = 'admin/inventory/ports/detail.html'
    page_title = '{% if port.name %} {{ port.name }}' \
                 '{% else %}{{ port.namedisplay }}' \
                 '{% endif %}'

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            port_id = self.kwargs['port_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_port_get(self.request,
                                                            port_id)
                self._object.host_id = host_id

            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve port details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = stx_api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        port = self._get_object()

        hostname = self.get_hostname(port.host_id)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(port.host_id,))),
            (_("Ports"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context['port_id'] = port.uuid
        context['host_id'] = port.host_id
        context['port'] = port
        return context
