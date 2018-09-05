#
# Copyright (c) 2013-2014 Wind River Systems, Inc.
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


class UpdatePort(forms.SelfHandlingForm):
    SPEED_CHOICES = (
        ('10', _("   10baseT")),
        ('100', _("  100baseT")),
        ('1000', _(" 1000baseT")),
        ('10000', _("10000baseT")),
    )

    AUTO_NEG_CHOICES = (
        ('yes', _("yes")),
        ('no', _("no")),
        ('na', _("na")),
    )

    host_uuid = forms.CharField(label=_("host_uuid"),
                                required=False,
                                widget=forms.widgets.HiddenInput)
    host_id = forms.CharField(label=_("host_id"),
                              required=False,
                              widget=forms.widgets.HiddenInput)
    id = forms.CharField(label=_("id"),
                         required=False,
                         widget=forms.widgets.HiddenInput)

    name = forms.CharField(label=_("Name"),
                           required=False,
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    newname = forms.CharField(label=_("Name"),
                              required=False)
    oldname = forms.CharField(label=_("Name"),
                              required=False,
                              widget=forms.widgets.HiddenInput)

    autoneg = forms.ChoiceField(label=_("Hidden Auto Neg"),
                                required=False,
                                choices=AUTO_NEG_CHOICES,
                                widget=forms.widgets.HiddenInput)
    autonegbool = forms.BooleanField(label=_("Auto Negotiation"),
                                     required=False)

    # Configurable Speed will be added later
    #
    # speed = forms.ChoiceField(label=_("Speed"),
    # initial='speed',
    # choices=SPEED_CHOICES,
    # required=False)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(UpdatePort, self).__init__(*args, **kwargs)

        name = kwargs['initial']['name']
        if name:
            self.fields['newname'].widget = forms.widgets.HiddenInput()
        else:
            self.fields['name'].widget = forms.widgets.HiddenInput()

        autoneg = kwargs['initial']['autoneg']
        if autoneg.lower() == 'na':
            self.fields['autonegbool'].widget = forms.widgets.HiddenInput()

    def clean(self):
        cleaned_data = super(UpdatePort, self).clean()
        return cleaned_data

    def handle(self, request, data):
        deviceName = data['newname']
        if data['name']:
            deviceName = data['name']
        elif data['newname'] != data['oldname']:
            data['namedisplay'] = data['newname']
        del data['newname']
        del data['oldname']

        if data['autoneg'] != 'na':
            if data['autonegbool']:
                data['autoneg'] = 'Yes'
            else:
                data['autoneg'] = 'No'
        del data['autonegbool']

        host_id = data['host_id']
        del data['host_id']

        port_id = data['id']
        del data['id']

        try:
            port = stx_api.sysinv.host_port_update(request, port_id, **data)
            msg = _('Port "%s" was successfully updated.') % deviceName
            LOG.debug(msg)
            messages.success(request, msg)
            return port
        except Exception:
            msg = _('Failed to update port "%s".') % deviceName
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)
