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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from cgtsclient import exc as sysinv_exceptions

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class CreateDataNetwork(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    mtu = forms.IntegerField(
        label=_("MTU"),
        required=True,
        initial=1500,
        min_value=576,
        max_value=9216,
        help_text=(
            _("Specifies the maximum MTU value of any associated tenant "
              "network.  Worker node data interface MTU values must be large "
              "enough to support the tenant MTU plus any additional provider "
              "encapsulation headers.  For example, VXLAN provider MTU of "
              "1500 requires a minimum data interface MTU of 1574 bytes (1600 "
              "bytes is recommended.")))

    network_type = forms.ChoiceField(label=_("Type"),
                                     required=True,
                                     widget=forms.Select(
                                     attrs={
                                         'class': 'switchable',
                                         'data-slug': 'dn_type'}))

    # VXLAN specific fields
    mode_choices = [('dynamic', _('Multicast VXLAN')),
                    ('static', _('Static VXLAN'))]
    mode = forms.ChoiceField(label=_("Mode"),
                             initial='dynamic',
                             required=False,
                             choices=mode_choices,
                             widget=forms.Select(
                                 attrs={
                                     'class': 'switchable switched',
                                     'data-switch-on': 'dn_type',
                                     'data-dn_type-vxlan': 'Mode',
                                     'data-slug': 'vxlan_mode'}))

    multicast_group_help = (_("Specify the IPv4 or IPv6 multicast address "
                              "for these VXLAN instances"))
    multicast_group = forms.CharField(
        max_length=255,
        label=_("Multicast Group Address"),
        initial="239.0.0.1",
        required=False,
        help_text=multicast_group_help,
        widget=forms.TextInput(
            attrs={
                'class': 'switchable switched',
                'data-slug': 'vxlan_multicast_group',
                'data-switch-on': 'vxlan_mode',
                'data-vxlan_mode-dynamic': 'Multicast Group Address'})
    )

    port_num_choices = [('4789', _('IANA Assigned VXLAN UDP port (4789)')),
                        ('4790', _('IANA Assigned VXLAN-GPE UDP port (4790)')),
                        ('8472', _('Legacy VXLAN UDP port (8472)'))]
    port_num = forms.ChoiceField(label=_("UDP Port"),
                                 required=True,
                                 choices=port_num_choices,
                                 widget=forms.Select(
                                     attrs={
                                         'class': 'switchable switched',
                                         'data-switch-on': 'dn_type',
                                         'data-dn_type-vxlan': 'UDP Port',
                                         'data-slug': 'port_num_slug'}))

    ttl = forms.IntegerField(label=_("TTL"),
                             required=False,
                             initial=1,
                             min_value=1,
                             max_value=255,
                             widget=forms.TextInput(
                                 attrs={
                                     'class': 'switchable switched',
                                     'data-switch-on': 'dn_type',
                                     'data-dn_type-vxlan': 'TTL',
                                     'data-slug': 'ttl_slug'}),
                             help_text=(
        _("Specify the time-to-live value for these VXLAN instances")))

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def __init__(self, request, *args, **kwargs):
        super(CreateDataNetwork, self).__init__(request, *args, **kwargs)

        datanet_type_choices = [('', _("Select a network type"))]
        datanet_choices_list = stx_api.sysinv.data_network_type_choices()
        for datanet_choices_tuple in datanet_choices_list:
            datanet_type_choices.append(datanet_choices_tuple)

        self.fields['network_type'].choices = datanet_type_choices

    def clean(self):
        cleaned_data = super(CreateDataNetwork, self).clean()
        if len(cleaned_data['name'].lstrip()) == 0:
            raise forms.ValidationError('invalid data network name')

        return cleaned_data

    def handle(self, request, data):
        try:
            params = {'name': data['name'],
                      'network_type': data['network_type'],
                      'description': data['description'],
                      'mtu': data['mtu']}

            if data['network_type'] == stx_api.sysinv.DATANETWORK_TYPE_VXLAN:
                params.update({'mode': data['mode'],
                               'port_num': data['port_num'],
                               'ttl': data['ttl']})
                if data['mode'] == 'dynamic':
                    params.update({'multicast_group': data['multicast_group']})
            network = stx_api.sysinv.data_network_create(request,
                                                         **params)
            msg = (_('Data network %s was successfully created.') %
                   data['name'])
            LOG.info(msg)
            messages.success(request, msg)
            return network
        except sysinv_exceptions.CgtsclientException as e:
            redirect = reverse('horizon:admin:datanets:index')
            exceptions.handle(request, str(e), redirect=redirect)
        except Exception:
            redirect = reverse('horizon:admin:datanets:index')
            msg = _('Failed to create data network %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)


class UpdateDataNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False,
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    network_type = forms.CharField(label=_("Type"), required=False,
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
                             help_text=(_("Specifies the minimum interface "
                                          "MTU required to support this "
                                          "data network ")))

    failure_url = 'horizon:admin:datanets:index'

    def handle(self, request, data):
        try:
            if not data['description']:
                data['description'] = '_'
            params = {'description': data['description'],
                      'mtu': data['mtu']}

            datanet = stx_api.sysinv.data_network_modify(
                request, data['id'], **params)
            msg = (_('Data network %s was successfully updated.') %
                   data['name'])
            LOG.info(msg)
            messages.success(request, msg)
            return datanet
        except sysinv_exceptions.CgtsclientException as e:
            msg = _('Failed to update data network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, str(e), redirect=redirect)
        except Exception:
            msg = _('Failed to update data network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
