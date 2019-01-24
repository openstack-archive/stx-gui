# Copyright 2012 NEC Corporation
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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from neutronclient.common import exceptions as neutron_exceptions

from openstack_dashboard import api

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class CreateProviderNetworkRange(forms.SelfHandlingForm):
    providernet_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    shared = forms.BooleanField(label=_("Shared"),
                                initial=False, required=False,
                                widget=forms.CheckboxInput(attrs={
                                    'class': 'switchable',
                                    'data-hide-on-checked': 'true',
                                    'data-slug': 'is_shared'}))

    tenant_id = forms.ChoiceField(label=_("Project"), required=False,
                                  widget=forms.Select(attrs={
                                      'class': 'switched',
                                      'data-switch-on': 'is_shared'}))

    minimum = forms.IntegerField(label=_("Minimum"),
                                 min_value=1)
    maximum = forms.IntegerField(label=_("Maximum"),
                                 min_value=1)
    # VXLAN specific fields
    mode_choices = [('dynamic', _('Multicast VXLAN')),
                    ('static', _('Static VXLAN'))]
    mode = forms.ChoiceField(label=_("Mode"),
                             initial='dynamic',
                             required=False,
                             choices=mode_choices,
                             widget=forms.Select(
                                 attrs={
                                     'class': 'switchable',
                                     'data-slug': 'vxlan_mode'}))
    group_help = (_("Specify the IPv4 or IPv6 multicast address for these "
                    "VXLAN instances"))
    group = forms.CharField(max_length=255,
                            label=_("Multicast Group Address"),
                            initial="239.0.0.1",
                            required=False,
                            help_text=group_help,
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'switchable switched',
                                    'data-slug': 'vxlan_group',
                                    'data-switch-on': 'vxlan_mode',
                                    'data-vxlan_mode-dynamic':
                                        'Multicast Group Address'}))
    port_choices = [('4789', _('IANA Assigned VXLAN UDP port (4789)')),
                    ('4790', _('IANA Assigned VXLAN-GPE UDP port (4790)')),
                    ('8472', _('Legacy VXLAN UDP port (8472)'))]
    port = forms.ChoiceField(label=_("UDP Port"),
                             required=True,
                             widget=forms.RadioSelect(),
                             choices=port_choices)
    ttl = forms.IntegerField(label=_("TTL"),
                             required=False,
                             initial=1,
                             min_value=1,
                             max_value=255,
                             help_text=(
        _("Specify the time-to-live value for these VXLAN instances")))

    def __init__(self, request, *args, **kwargs):
        super(CreateProviderNetworkRange, self).__init__(request, *args,
                                                         **kwargs)

        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)  # noqa pylint: disable=unused-variable
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices
        initial = kwargs['initial']
        if 'providernet_type' in initial:
            providernet_type = initial['providernet_type']
            if providernet_type != "vxlan":
                del self.fields["mode"]
                del self.fields["group"]
                del self.fields["port"]
                del self.fields["ttl"]

    def handle(self, request, data):
        try:
            params = {'providernet_id': data['providernet_id'],
                      'name': data['name'],
                      'description': data['description'],
                      'minimum': data['minimum'],
                      'maximum': data['maximum'],
                      'shared': data['shared'],
                      'tenant_id': data['tenant_id']}

            if not data['tenant_id']:
                params['shared'] = True

            if self.initial['providernet_type'] == "vxlan":
                params['mode'] = data['mode']
                if params['mode'] == 'dynamic':
                    params['group'] = data['group']
                params['port'] = int(data['port'])
                params['ttl'] = int(data['ttl'])

            providernet_range = stx_api.neutron.provider_network_range_create(
                request, **params)
            msg = (_('Provider network range %s was successfully created.') %
                   providernet_range['id'])
            LOG.debug(msg)
            messages.success(request, msg)
            return providernet_range
        except neutron_exceptions.NeutronClientException as e:
            LOG.info(str(e))
            redirect = reverse('horizon:admin:datanets:datanets:'
                               'detail',
                               args=(data['providernet_id'],))
            exceptions.handle(request, str(e), redirect=redirect)
        except Exception:
            msg = _('Failed to create a provider'
                    ' network range for network %s') \
                % data['providernet_id']
            LOG.info(msg)
            redirect = reverse('horizon:admin:datanets:datanets:'
                               'detail',
                               args=(data['providernet_id'],))
            exceptions.handle(request, msg, redirect=redirect)

    def clean(self):
        cleaned_data = super(CreateProviderNetworkRange, self).clean()
        if not cleaned_data["shared"] and not cleaned_data["tenant_id"]:
            msg = "Project must be specified for non-shared Segmentation Range"
            raise forms.ValidationError(msg)
        if cleaned_data["shared"]:
            cleaned_data["tenant_id"] = ""


class UpdateProviderNetworkRange(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:datanets:datanets:detail'
    providernet_id = forms.CharField(widget=forms.HiddenInput())
    providernet_range_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False,
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    minimum = forms.IntegerField(label=_("Minimum"), min_value=1)
    maximum = forms.IntegerField(label=_("Maximum"), min_value=1)
    shared = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    tenant_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    # VXLAN specific fields
    mode_widget = forms.TextInput(attrs={'readonly': 'readonly'})
    mode = forms.CharField(label=_("mode"),
                           required=False,
                           widget=mode_widget)
    group_widget = forms.TextInput(attrs={'readonly': 'readonly'})
    group = forms.CharField(max_length=255,
                            label=_("Multicast Group Address"),
                            required=False,
                            widget=group_widget)
    port_widget = forms.RadioSelect(attrs={'disabled': 'disabled'})
    port_choices = [('4789', _('IANA Assigned VXLAN UDP port (4789)')),
                    ('4790', _('IANA Assigned VXLAN-GPE UDP port (4790)')),
                    ('8472', _('Legacy VXLAN UDP port (8472)'))]
    port = forms.ChoiceField(label=_("UDP Port"),
                             required=False,
                             widget=port_widget,
                             choices=port_choices)
    ttl_widget = forms.TextInput(attrs={'readonly': 'readonly'})
    ttl = forms.IntegerField(label=_("TTL"),
                             required=False,
                             widget=ttl_widget)

    def __init__(self, request, *args, **kwargs):
        super(UpdateProviderNetworkRange, self).__init__(
            request, *args, **kwargs)
        initial = kwargs['initial']
        if 'mode' not in initial:
            del self.fields["mode"]
        if 'group' not in initial or initial.get('mode') == 'static':
            del self.fields["group"]
        if 'port' not in initial:
            del self.fields["port"]
        if 'ttl' not in initial:
            del self.fields["ttl"]

    def handle(self, request, data):
        try:
            params = {'description': data['description'],
                      'minimum': data['minimum'],
                      'maximum': data['maximum']}

            providernet_range = stx_api.neutron.provider_network_range_modify(
                request, data['providernet_range_id'], **params)
            msg = (_('Provider network range %s was successfully updated.') %
                   data['providernet_range_id'])
            LOG.debug(msg)
            messages.success(request, msg)
            return providernet_range
        except neutron_exceptions.NeutronClientException as e:
            LOG.info(str(e))
            redirect = reverse('horizon:admin:datanets:datanets:'
                               'detail',
                               args=(data['providernet_id'],))
            exceptions.handle(request, str(e), redirect=redirect)
        except Exception:
            msg = (_('Failed to update provider network range %s') %
                   data['providernet_range_id'])
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['providernet_id']])
            exceptions.handle(request, msg, redirect=redirect)
