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
import netaddr

from horizon import forms
from horizon import messages

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class CreateRoute(forms.SelfHandlingForm):

    host_id = forms.CharField(widget=forms.HiddenInput())
    interface_id = forms.CharField(widget=forms.HiddenInput())
    success_url = 'horizon:admin:inventory:viewinterface'
    failure_url = 'horizon:admin:inventory:viewinterface'

    network = forms.IPField(
        label=_("Network Address"),
        required=True,
        initial="",
        help_text=_("IP network address in CIDR format "
                    "(e.g. 192.168.0.0/24, 2001:DB8::/48"),
        version=forms.IPv4 | forms.IPv6,
        mask=True)

    gateway = forms.IPField(
        label=_("Gateway Address"),
        required=True,
        initial="",
        help_text=_("Gateway IP address "
                    "(e.g. 192.168.0.1/24, 2001:DB8::1/48"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    metric = forms.IntegerField(
        label=_("Route Metric"),
        initial="1",
        required=True)

    def handle(self, request, data):
        try:
            ip_network = netaddr.IPNetwork(data['network'])
            body = {'interface_uuid': data['interface_id'],
                    'network': str(ip_network.ip),
                    'prefix': ip_network.prefixlen,
                    'gateway': data['gateway'],
                    'metric': data['metric']}
            route = stx_api.sysinv.route_create(request, **body)
            msg = (_('Route to %(network)s/%(prefix)s via %(gateway)s was '
                     'successfully created') % body)
            messages.success(request, msg)
            return route
        except Exception as e:
            # Allow REST API error message to appear on UI
            messages.error(request, e)
            LOG.error(e)
            # Redirect to failure page
            redirect = reverse(self.failure_url,
                               args=(data['host_id'], data['interface_id']))
            return shortcuts.redirect(redirect)
