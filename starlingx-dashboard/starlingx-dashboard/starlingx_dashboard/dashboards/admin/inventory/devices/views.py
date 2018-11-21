#
# Copyright (c) 2014-2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.devices.forms import \
    UpdateDevice
from starlingx_dashboard.dashboards.admin.inventory.devices.tables import \
    UsageTable

LOG = logging.getLogger(__name__)


class UpdateView(forms.ModalFormView):
    form_class = UpdateDevice
    template_name = 'admin/inventory/devices/update.html'
    context_object_name = 'device'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            device_uuid = self.kwargs['device_uuid']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_device_get(self.request,
                                                              device_uuid)
                self._object.host_id = host_id
            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(host_id))
                msg = _('Unable to retrieve device details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        device = self._get_object()
        context['device_uuid'] = device.uuid
        context['host_id'] = device.host_id
        return context

    def get_initial(self):
        device = self._get_object()
        enabled = device.enabled
        if isinstance(enabled, str):
            if enabled.lower() == 'false':
                enabled = False
            elif enabled.lower() == 'true':
                enabled = True
        return {'name': device.name,
                'enabled': enabled,
                'pciaddr': device.pciaddr,
                'device_id': device.pdevice_id,
                'device_name': device.pdevice,
                'host_id': device.host_id,
                'uuid': device.uuid}


class DetailView(views.HorizonTemplateView):
    template_name = 'admin/inventory/devices/detail.html'
    page_title = '{{ device.name }}'

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            device_uuid = self.kwargs['device_uuid']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_device_get(self.request,
                                                              device_uuid)
                self._object.host_id = host_id

            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve device details')
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
        device = self._get_object()

        hostname = self.get_hostname(device.host_id)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(device.host_id,))),
            (_("Devices"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context['device_uuid'] = device.uuid
        context['host_id'] = device.host_id
        context['device'] = device
        return context


class UsageView(tables.MultiTableView):
    table_classes = (UsageTable, )
    template_name = 'admin/inventory/devices/usage.html'

    def _handle_exception(self, device_id):
        redirect = reverse("horizon:admin:inventory:index")
        msg = _('Unable to retrieve device usage for %s') % device_id
        exceptions.handle(self.request, msg, redirect=redirect)

    def get_usage_data(self, *args, **kwargs):
        if not hasattr(self, "_detail_object"):
            dev_id = self.kwargs['device_id']
            try:
                _object = stx_api.nova.get_detail_usage(self.request, dev_id)
                _object.sort(key=lambda f: (f.host))
                _id = 0
                for u in _object:
                    _id += 1
                    u.id = _id
                self._detail_object = _object

            except Exception:
                self._handle_exception(dev_id)

        return self._detail_object

    def _get_device_usage(self, *args, **kwargs):
        if not hasattr(self, "_usage_object"):
            dev_id = self.kwargs['device_id']
            try:
                _object = stx_api.nova.get_device_usage(self.request, dev_id)
                self._usage_object = _object
            except Exception:
                self._handle_exception(dev_id)

        return self._usage_object

    def get_context_data(self, **kwargs):
        context = super(UsageView, self).get_context_data(**kwargs)
        context['device_usage'] = self._get_device_usage()
        return context
