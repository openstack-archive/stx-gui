# Copyright (c) 2013-2015,2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging
import netaddr

from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import memoized
from openstack_dashboard import api

LOG = logging.getLogger(__name__)

PROTOCOL_CHOICES = [("tcp", "TCP"),
                    ("udp", "UDP"),
                    ("udp-lite", "UDP-Lite"),
                    ("sctp", "SCTP"),
                    ("dccp", "DCCP")]


class AddPortForwardingRule(forms.SelfHandlingForm):
    inside_addr = forms.ChoiceField(
        label=_("IP Address"),
        required=True,
        initial="Select an IP address",
        help_text=_("Specify a private IP address which will be the "
                    "destination of the forwarding rule "
                    "(e.g., 192.168.0.254)."))
    inside_port = forms.IntegerField(
        label=_("Private Port"), required=True, initial="",
        min_value=1, max_value=65535,
        help_text=_("Specify a private layer4 protocol port number"))
    outside_port = forms.IntegerField(
        label=_("Public Port"), required=True, initial="",
        min_value=1, max_value=65535,
        help_text=_("Specify a public layer4 protocol port number"))
    protocol = forms.ChoiceField(
        label=_("Protocol"), required=True, initial="Select a protocol")
    description = forms.CharField(label=_("Description"), required=False)
    router_name = forms.CharField(label=_("Router Name"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    router_id = forms.CharField(label=_("Router ID"),
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))
    failure_url = 'horizon:project:routers:detail'

    def __init__(self, request, *args, **kwargs):
        super(AddPortForwardingRule, self).__init__(request, *args, **kwargs)
        self.router_id = kwargs['initial']['router_id']
        self.tenant_id = kwargs['initial']['tenant_id']
        address_choices = self.populate_inside_addr_choices(request)
        self.fields['inside_addr'].choices = address_choices
        self.fields['protocol'].choices = PROTOCOL_CHOICES

    @memoized.memoized_method
    def _get_connected_ipv4_networks(self, request, router_id):
        networks = set()
        subnets = set()
        ports = api.neutron.port_list(request, device_id=router_id)
        for p in ports:
            if p.device_owner not in api.neutron.ROUTER_INTERFACE_OWNERS:
                continue
            if not p.fixed_ips:
                continue
            networks.add(p.network_id)
            for ip in p.fixed_ips:
                if netaddr.valid_ipv4(ip['ip_address']):
                    subnets.add(ip['subnet_id'])
        return (list(networks), list(subnets))

    @memoized.memoized_method
    def _get_available_addresses(self, request, network_ids, subnet_ids):
        address_list = []
        for network_id in network_ids:
            ports = api.neutron.port_list(request, network_id=network_id)
            for p in ports:
                if p.device_owner.startswith('network:'):
                    continue
                for ip in p.fixed_ips:
                    if ip['subnet_id'] in subnet_ids:
                        record = (ip['ip_address'], p.id, p.device_id)
                        address_list.append(record)
        return address_list

    @memoized.memoized_method
    def _get_servers(self, request):
        search_opts = {'project_id': self.tenant_id}
        servers, has_more = api.nova.server_list(
            self.request, search_opts=search_opts)
        server_dict = SortedDict([(s.id, s.name) for s in servers])
        return server_dict

    def populate_inside_addr_choices(self, request):
        network_ids, subnet_ids = self._get_connected_ipv4_networks(
            request, self.router_id)
        addresses = self._get_available_addresses(
            request, network_ids, subnet_ids)
        servers = self._get_servers(request)
        choices = []
        for ip_address, port_id, device_id in addresses:
            server = servers.get(device_id)
            display_name = ip_address
            if server:
                display_name += " : {}".format(server)
            choices.append((ip_address, display_name))
        choices.insert(0, ("", "Select an IP address"))
        return choices

    def handle(self, request, data):
        try:
            router_id = data['router_id']
            params = {'router_id': data['router_id'],
                      'inside_addr': data['inside_addr'],
                      'inside_port': data['inside_port'],
                      'outside_port': data['outside_port'],
                      'protocol': data['protocol'].lower()}
            if 'description' in data:
                params['description'] = data['description']
            api.neutron.portforwarding_create(request, **params)
        except Exception as e:
            self._handle_error(request, router_id, e)
        msg = _('Port forwarding rule added')
        LOG.debug(msg)
        messages.success(request, msg)
        return True

    def _handle_error(self, request, router_id, reason):
        msg = _('Failed to add port forwarding rule: %s') % reason
        LOG.info(msg)
        redirect = reverse(self.failure_url, args=[router_id])
        exceptions.handle(request, msg, redirect=redirect)


class UpdatePortForwardingRule(AddPortForwardingRule):

    portforwarding_id = forms.CharField(
        label=_("ID"), required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    def __init__(self, request, *args, **kwargs):
        super(UpdatePortForwardingRule, self).__init__(
            request, *args, **kwargs)

    def handle(self, request, data):
        try:
            portforwarding_id = data['portforwarding_id']
            router_id = data['router_id']
            params = {'inside_addr': data['inside_addr'],
                      'inside_port': data['inside_port'],
                      'outside_port': data['outside_port'],
                      'protocol': data['protocol'].lower()}
            if 'description' in data:
                params['description'] = data['description']
            api.neutron.portforwarding_update(request,
                                              portforwarding_id,
                                              **params)
        except Exception as e:
            self._handle_error(request, router_id, e)
        msg = _('Port forwarding rule updated')
        LOG.debug(msg)
        messages.success(request, msg)
        return True

    def _handle_error(self, request, router_id, reason):
        msg = _('Failed to update port forwarding rule: %s') % reason
        LOG.info(msg)
        redirect = reverse(self.failure_url, args=[router_id])
        exceptions.handle(request, msg, redirect=redirect)
