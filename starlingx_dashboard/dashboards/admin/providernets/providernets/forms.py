# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from neutronclient.common import exceptions as neutron_exceptions

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateProviderNetwork(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    type = forms.ChoiceField(label=_("Type"),
                             required=True)
    mtu = forms.IntegerField(label=_("MTU"),
                             required=True,
                             initial=1500,
                             min_value=576,
                             max_value=9216,
                             help_text=(
        _("Specifies the maximum MTU value of any associated tenant "
          "network.  Compute node data interface MTU values must be large "
          "enough to support the tenant MTU plus any additional provider "
          "encapsulation headers.  For example, VXLAN provider MTU of "
          "1500 requires a minimum data interface MTU of 1574 bytes (1600 "
          "bytes is recommended.")))
    vlan_transparent = forms.BooleanField(
        label=_("VLAN Transparent"),
        initial=False, required=False,
        help_text=_("Allow tenant networks to be created that require "
                    "VLAN tagged packets to be transparently passed through "
                    "the provider network."))

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def __init__(self, request, *args, **kwargs):
        super(CreateProviderNetwork, self).__init__(request, *args, **kwargs)

        providernet_type_choices = [('', _("Select a network type"))]
        providernet_types = api.neutron.provider_network_type_list(request)
        for providernet_type in providernet_types:
            providernet_type_choices.append((providernet_type.type,
                                             providernet_type.type))
        self.fields['type'].choices = providernet_type_choices

    def clean(self):
        cleaned_data = super(CreateProviderNetwork, self).clean()
        if len(cleaned_data['name'].lstrip()) == 0:
            raise forms.ValidationError('invalid provider name')

        return cleaned_data

    def handle(self, request, data):
        try:
            params = {'name': data['name'],
                      'type': data['type'],
                      'description': data['description'],
                      'mtu': data['mtu'],
                      'vlan_transparent': data['vlan_transparent']}

            network = api.neutron.provider_network_create(request, **params)
            msg = (_('Provider network %s was successfully created.') %
                   data['name'])
            LOG.debug(msg)
            messages.success(request, msg)
            return network
        except neutron_exceptions.NeutronClientException as e:
            redirect = reverse('horizon:admin:providernets:index')
            exceptions.handle(request, e.message, redirect=redirect)
        except Exception:
            redirect = reverse('horizon:admin:providernets:index')
            msg = _('Failed to create provider network %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)


class UpdateProviderNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False,
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    type = forms.CharField(label=_("Type"), required=False,
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    id = forms.CharField(widget=forms.HiddenInput)
    # Mutable fields
    description = forms.CharField(label=_("Description"), required=False)
    mtu = forms.IntegerField(label=_("MTU"),
                             required=True,
                             initial=1500,
                             min_value=576,
                             max_value=9216,
                             help_text=(_("Specifies the minimum interface"
                                          " MTU required to support this"
                                          " provider network")))
    vlan_transparent = forms.BooleanField(
        label=_("VLAN Transparent"),
        initial=False, required=False,
        help_text=_("Allow tenant networks to be created that require "
                    "VLAN tagged packets to be transparently passed through "
                    "the provider network. "
                    "Changes will not impact existing networks."))
    failure_url = 'horizon:admin:providernets:index'

    def handle(self, request, data):
        try:
            params = {'description': data['description'],
                      'mtu': data['mtu'],
                      'vlan_transparent': data['vlan_transparent']}

            providernet = api.neutron.provider_network_modify(
                request, data['id'], **params)
            msg = (_('Provider network %s was successfully updated.') %
                   data['name'])
            LOG.debug(msg)
            messages.success(request, msg)
            return providernet
        except neutron_exceptions.NeutronClientException as e:
            msg = _('Failed to update provider network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, e.message, redirect=redirect)
        except Exception:
            msg = _('Failed to update provider network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
