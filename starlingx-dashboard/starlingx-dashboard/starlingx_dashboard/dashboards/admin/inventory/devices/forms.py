#
# Copyright (c) 2014-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class UpdateDevice(forms.SelfHandlingForm):

    host_id = forms.CharField(label=_("host_id"),
                              required=False,
                              widget=forms.widgets.HiddenInput)

    uuid = forms.CharField(label=_("uuid"),
                           required=False,
                           widget=forms.widgets.HiddenInput)

    device_name = forms.CharField(label=_("Device Name"),
                                  required=False,
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))

    pciaddr = forms.CharField(label=_("Device Address"),
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))

    name = forms.CharField(label=_("Name"),
                           required=False,
                           widget=forms.TextInput())

    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 widget=forms.CheckboxInput())

    failure_url = 'horizon:admin:inventory:detail'

    def clean(self):
        data = super(UpdateDevice, self).clean()
        if isinstance(data['enabled'], bool):
            data['enabled'] = 'True' if data['enabled'] else 'False'
        return data

    def handle(self, request, data):
        name = data['name']
        uuid = data['uuid']

        try:
            p = {}
            p['name'] = name
            p['enabled'] = str(data['enabled'])
            device = stx_api.sysinv.host_device_update(request, uuid, **p)
            msg = _('device "%s" was successfully updated.') % name
            LOG.debug(msg)
            messages.success(request, msg)
            return device
        except Exception as exc:
            msg = _('Failed to update device "%(n)s" (%(e)s).') % ({'n': name,
                                                                    'e': exc})
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)
