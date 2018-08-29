# Copyright 2015 Wind River Systems, Inc
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
# Copyright (c) 2015 Wind River Systems, Inc.
#

import logging

from django.core.urlresolvers import reverse
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages

import netaddr

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)

ALLOCATION_ORDER_CHOICES = (
    ('sequential', _("Sequential")),
    ('random', _("Random")),
)


class CreateAddressPool(forms.SelfHandlingForm):
    success_url = 'horizon:admin:system_config:index'
    failure_url = 'horizon:admin:system_config:index'

    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True,
                           min_length=1)

    network = forms.IPField(
        label=_("Network Address"),
        required=True,
        initial="",
        help_text=_("Network IP interface address in CIDR format "
                    "(e.g. 192.168.0.0/24, 2001:DB8::/48"),
        version=forms.IPv4 | forms.IPv6,
        mask=True)

    order = forms.ChoiceField(
        label=_("Allocation Order"),
        required=True,
        initial='random',
        choices=ALLOCATION_ORDER_CHOICES)

    ranges = forms.CharField(
        label=_("Address Ranges"),
        required=False,
        help_text=(_("Enter a comma separated list of <start>-<end> "
                     "IP address ranges.")))

    def _parse_ranges(self, range_str):
        result = []
        for r in range_str.replace(' ', '').split(','):
            start, end = r.split('-')
            result.append([start, end])
        return result

    def clean_ranges(self):
        try:
            ranges = self.cleaned_data.get('ranges')
            return self._parse_ranges(ranges) if ranges else None
        except Exception:
            msg = (_("Expecting a comma separated list "
                     "of <start>-<end> IP address ranges"))
            raise forms.ValidationError(msg)

    def handle(self, request, data):
        try:
            ip_address = netaddr.IPNetwork(data['network'])
            body = {'name': data['name'],
                    'network': str(ip_address.ip),
                    'prefix': ip_address.prefixlen,
                    'order': data['order']}
            if data.get('ranges'):
                body['ranges'] = data.get('ranges')
            pool = stx_api.sysinv.address_pool_create(request, **body)
            msg = (_('Address pool was successfully created'))
            messages.success(request, msg)
            return pool
        except Exception as e:
            # Allow REST API error message to appear on UI
            messages.error(request, e)
            LOG.error(e)
            # Redirect to failure page
            redirect = reverse(self.failure_url)
            return shortcuts.redirect(redirect)


class UpdateAddressPool(CreateAddressPool):

    id = forms.CharField(widget=forms.HiddenInput)

    network = forms.IPField(
        label=_("Network Address"),
        required=True,
        version=forms.IPv4 | forms.IPv6,
        mask=True,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}))

    def handle(self, request, data):
        try:
            updates = {}
            if 'name' in data:
                updates['name'] = data['name']
            if 'order' in data:
                updates['order'] = data['order']
            if data.get('ranges'):
                updates['ranges'] = data['ranges']
            pool = stx_api.sysinv.address_pool_update(request, data['id'],
                                                      **updates)
            msg = (_('Address pool was successfully updated'))
            messages.success(request, msg)
            return pool
        except Exception as e:
            # Allow REST API error message to appear on UI
            messages.error(request, e)
            LOG.error(e)
            # Redirect to failure page
            redirect = reverse(self.failure_url)
            return shortcuts.redirect(redirect)
