#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4


import logging

from compiler.ast import flatten
import netaddr

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


def _get_ipv4_pool_choices(pools):
    choices = []
    for p in pools:
        address = netaddr.IPAddress(p.network)
        if address.version == 4:
            choices.append((p.uuid, p.name))
    return choices


def _get_ipv6_pool_choices(pools):
    choices = []
    for p in pools:
        address = netaddr.IPAddress(p.network)
        if address.version == 6:
            choices.append((p.uuid, p.name))
    return choices


class CheckboxSelectMultiple(forms.widgets.CheckboxSelectMultiple):
    """Custom checkbox select widget that will render a text string

    with an hidden input if there are no choices.

    """

    def __init__(self, attrs=None, choices=(), empty_value=''):
        super(CheckboxSelectMultiple, self).__init__(attrs, choices)
        self.empty_value = empty_value

    def render(self, name, value, attrs=None, choices=()):
        if self.choices:
            return super(CheckboxSelectMultiple, self).render(name, value,
                                                              attrs, choices)
        else:
            hi = forms.HiddenInput(self.attrs)
            hi.is_hidden = False  # ensure text is rendered
            return mark_safe(self.empty_value + hi.render(name, None, attrs))


class MultipleChoiceField(forms.MultipleChoiceField):
    """Custom multiple choice field that only validates

    if a value was provided.

    """

    def valid_value(self, value):
        if not self.required and not value:
            return True
        return super(MultipleChoiceField, self).valid_value(value)


class AddInterfaceProfile(forms.SelfHandlingForm):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)
    profilename = forms.CharField(label=_("Interface Profile Name"),
                                  required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddInterfaceProfile, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddInterfaceProfile, self).clean()
        # host_id = cleaned_data.get('host_id')
        # interfaceProfileName = cleaned_data.get('hostname')

        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']
        interfaceProfileName = data['profilename']
        try:
            interfaceProfile = api.sysinv.host_interfaceprofile_create(request,
                                                                       **data)
            msg = _(
                'Interface Profile "%s" was '
                'successfully created.') % interfaceProfileName
            LOG.debug(msg)
            messages.success(request, msg)
            return interfaceProfile
        except exc.ClientException as ce:
            # Allow REST API error message to appear on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _(
                'Failed to create interface'
                ' profile "%s".') % interfaceProfileName
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)


class AddInterface(forms.SelfHandlingForm):
    NETWORK_TYPE_CHOICES = (
        ('none', _("none")),
        ('mgmt', _("mgmt")),
        ('oam', _("oam")),
        ('data', _("data")),
        ('data-external', _("data-external")),
        ('control', _("control")),
        ('infra', _("infra")),
        ('pxeboot', _("pxeboot")),
    )

    INTERFACE_TYPE_CHOICES = (
        (None, _("<Select interface type>")),
        ('ae', _("aggregated ethernet")),
        ('vlan', _("vlan")),
    )

    AE_MODE_CHOICES = (
        ('active_standby', _("active/standby")),
        ('balanced', _("balanced")),
        ('802.3ad', _("802.3ad")),
    )

    AE_XMIT_HASH_POLICY_CHOICES = (
        ('layer3+4', _("layer3+4")),
        ('layer2+3', _("layer2+3")),
        ('layer2', _("layer2")),
    )

    IPV4_MODE_CHOICES = (
        ('disabled', _("Disabled")),
        ('static', _("Static")),
        ('pool', _("Pool")),
    )

    IPV6_MODE_CHOICES = (
        ('disabled', _("Disabled")),
        ('static', _("Static")),
        ('pool', _("Pool")),
        ('auto', _("Automatic Assignment")),
        ('link-local', _("Link Local")),
    )

    ihost_uuid = forms.CharField(
        label=_("ihost_uuid"),
        initial='ihost_uuid',
        required=False,
        widget=forms.widgets.HiddenInput)

    host_id = forms.CharField(
        label=_("host_id"),
        initial='host_id',
        required=False,
        widget=forms.widgets.HiddenInput)

    # don't enforce a max length in ifname form field as
    # this will be validated by the SysInv REST call.
    # This ensures that both cgsclient and Dashboard
    # have the same length constraints.
    ifname = forms.RegexField(
        label=_("Interface Name"),
        required=True,
        regex=r'^[\w\.\-]+$',
        error_messages={
            'invalid':
            _('Name may only contain letters, numbers, underscores, '
              'periods and hyphens.')})

    networktype = forms.MultipleChoiceField(
        label=_("Network Type"),
        required=True,
        choices=NETWORK_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'switchable',
                'data-slug': 'network_type'}))

    iftype = forms.ChoiceField(
        label=_("Interface Type"),
        required=True,
        choices=INTERFACE_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-switch-on': 'network_type',
                'data-network_type-none': 'Interface Type',
                'data-network_type-infra': 'Interface Type',
                'data-network_type-data': 'Interface Type',
                'data-network_type-data-external': 'Interface Type',
                'data-network_type-control': 'Interface Type',
                'data-network_type-mgmt': 'Interface Type',
                'data-network_type-oam': 'Interface Type',
                'data-network_type-pxeboot': 'Interface Type',
                'data-slug': 'interface_type'}))

    aemode = forms.ChoiceField(
        label=_("Aggregated Ethernet - Mode"),
        required=False,
        choices=AE_MODE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-slug': 'ae_mode',
                'data-switch-on': 'interface_type',
                'data-interface_type-ae': 'Aggregated Ethernet - Mode'}))

    txhashpolicy = forms.ChoiceField(
        label=_("Aggregated Ethernet - Tx Policy"),
        required=False,
        choices=AE_XMIT_HASH_POLICY_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ae_mode',
                'data-ae_mode-balanced': 'Aggregated Ethernet - Tx Policy',
                'data-ae_mode-802.3ad': 'Aggregated Ethernet - Tx Policy'}))

    vlan_id = forms.IntegerField(
        label=_("Vlan ID"),
        initial=1,
        min_value=1,
        max_value=4094,
        required=False,
        help_text=_("Virtual LAN tag."),
        error_messages={'invalid': _('Vlan ID must be '
                                     'between 1 and 4094.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'interface_type',
                'data-slug': 'vlanid',
                'data-interface_type-vlan': 'Vlan ID'}))

    uses = forms.MultipleChoiceField(
        label=_("Interface(s)"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Interface(s) of Interface."))

    ports = forms.CharField(
        label=_("Port(s)"),
        required=False,
        widget=forms.widgets.HiddenInput)

    providernetworks_data = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'network_type',
                'data-network_type-data': ''},
            empty_value=_("No provider networks available for network type.")))

    providernetworks_data_external = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'network_type',
                'data-network_type-data-external': ''},
            empty_value=_("No provider networks available for network type.")))

    providernetworks_pci = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'network_type',
                'data-network_type-pci-passthrough': ''},
            empty_value=_("No provider networks available for network type.")))

    providernetworks_sriov = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'network_type',
                'data-network_type-pci-sriov': ''},
            empty_value=_("No provider networks available for network type.")))

    imtu = forms.IntegerField(
        label=_("MTU"),
        initial=1500,
        min_value=576,
        max_value=9216,
        required=False,
        help_text=_("Maximum Transmit Unit."),
        error_messages={'invalid': _('MTU must be '
                                     'between 576 and 9216 bytes.')},
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'network_type',
            'data-network_type-none': _('MTU'),
            'data-network_type-data': _('MTU'),
            'data-network_type-data-external': _('MTU'),
            'data-network_type-control': _('MTU'),
            'data-network_type-mgmt': _('MTU'),
            'data-network_type-infra': _('MTU'),
            'data-network_type-pci-passthrough': _('MTU'),
            'data-network_type-pci-sriov': _('MTU'),
            'data-network_type-oam': _('MTU'),
            'data-network_type-pxeboot': _('MTU')}))

    ipv4_mode = forms.ChoiceField(
        label=_("IPv4 Addressing Mode"),
        required=False,
        initial='disabled',
        choices=IPV4_MODE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-slug': 'ipv4_mode',
                'data-switch-on': 'network_type',
                'data-network_type-data': 'IPv4 Addressing Mode',
                'data-network_type-control': 'IPv4 Addressing Mode'}))

    ipv4_pool = forms.ChoiceField(
        label=_("IPv4 Address Pool"),
        required=False,
        initial='',
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ipv4_mode',
                'data-ipv4_mode-pool': 'IPv4 Address Pool'}))

    ipv6_mode = forms.ChoiceField(
        label=_("IPv6 Addressing Mode"),
        required=False,
        initial='disabled',
        choices=IPV6_MODE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-slug': 'ipv6_mode',
                'data-switch-on': 'network_type',
                'data-network_type-data': 'IPv6 Addressing Mode',
                'data-network_type-control': 'IPv6 Addressing Mode'}))

    ipv6_pool = forms.ChoiceField(
        label=_("IPv6 Address Pool"),
        required=False,
        initial='',
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ipv6_mode',
                'data-ipv6_mode-pool': 'IPv6 Address Pool'}))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddInterface, self).__init__(*args, **kwargs)

        # Populate Available Port Choices
        # Only include ports that are not already part of other interfaces
        this_interface_id = 0

        current_interface = None
        if (type(self) is UpdateInterface):
            this_interface_id = kwargs['initial']['id']
            current_interface = api.sysinv.host_interface_get(
                self.request, this_interface_id)
        else:
            self.fields['providernetworks_sriov'].widget = \
                forms.widgets.HiddenInput()
            self.fields['providernetworks_pci'].widget = \
                forms.widgets.HiddenInput()

        host_uuid = kwargs['initial']['ihost_uuid']

        # Retrieve SDN configuration
        sdn_enabled = kwargs['initial']['sdn_enabled']
        sdn_l3_mode = kwargs['initial']['sdn_l3_mode_enabled']

        # Populate Address Pool selections
        pools = api.sysinv.address_pool_list(self.request)
        self.fields['ipv4_pool'].choices = _get_ipv4_pool_choices(pools)
        self.fields['ipv6_pool'].choices = _get_ipv6_pool_choices(pools)

        # Populate Provider Network Choices by querying Neutron
        self.extras = {}
        interfaces = api.sysinv.host_interface_list(self.request, host_uuid)

        used_providernets = []
        for i in interfaces:
            networktypelist = []
            if i.networktype:
                networktypelist = [i.networktype.split(",")]
            if 'data' in networktypelist and \
                    i.providernetworks and \
                    i.uuid != this_interface_id:
                used_providernets = used_providernets + \
                    i.providernetworks.split(",")

        providernet_choices = []
        providernet_filtered = []
        providernet_flat = None
        providernets = api.neutron.provider_network_list(self.request)
        for provider in providernets:
            label = "{} (mtu={})".format(provider.name, provider.mtu)
            providernet = (str(provider.name), label)
            providernet_choices.append(providernet)
            if provider.name not in used_providernets:
                providernet_filtered.append(providernet)
            if provider.type == 'flat':
                providernet_flat = providernet

        self.fields['providernetworks_data'].choices = providernet_filtered
        if (type(self) is UpdateInterface):
            self.fields['providernetworks_pci'].choices = providernet_choices
            self.fields['providernetworks_sriov'].choices = providernet_choices

        if not (sdn_enabled and sdn_l3_mode):
            self.fields['providernetworks_data_external'].widget = \
                forms.widgets.HiddenInput()
            nt_choices = self.fields['networktype'].choices
            self.fields['networktype'].choices = [i for i in nt_choices
                                                  if i[0] != 'data-external']
        else:
            # Support a 'data-external' network type and allow
            # its Provider Network configuration (FLAT only)
            self.fields['providernetworks_data_external'].choices = \
                [providernet_flat]

        if current_interface:
            # update operation
            if not current_interface.uses:
                # update default interfaces
                self.fields['uses'].widget = forms.widgets.HiddenInput()
                avail_port_list = api.sysinv.host_port_list(
                    self.request, host_uuid)
                for p in avail_port_list:
                    if p.interface_uuid == this_interface_id:
                        self.fields['ports'].initial = p.uuid
            else:
                # update non default interfaces
                avail_interface_list = api.sysinv.host_interface_list(
                    self.request, host_uuid)
                interface_tuple_list = []
                for i in avail_interface_list:
                    if i.uuid != current_interface.uuid:
                        interface_tuple_list.append(
                            (i.uuid, "%s (%s, %s)" %
                             (i.ifname, i.imac, i.networktype)))

                uses_initial = [i.uuid for i in avail_interface_list if
                                i.ifname in current_interface.uses]

                self.fields['uses'].initial = uses_initial
                self.fields['uses'].choices = interface_tuple_list

            if current_interface.vlan_id:
                self.fields['vlan_id'].initial = current_interface.vlan_id

        else:
            # add operation
            avail_interface_list = api.sysinv.host_interface_list(
                self.request, host_uuid)
            interface_tuple_list = []
            for i in avail_interface_list:
                interface_tuple_list.append(
                    (i.uuid, "%s (%s, %s)" %
                     (i.ifname, i.imac, i.networktype)))
            self.fields['uses'].choices = interface_tuple_list
            self.fields['networktype'].initial = ('none', 'none')

    def clean(self):
        cleaned_data = super(AddInterface, self).clean()

        networktype = cleaned_data.get('networktype', 'none')

        if ('data' not in networktype and
           'control' not in networktype):
            cleaned_data.pop('ipv4_mode', None)
            cleaned_data.pop('ipv6_mode', None)

        if cleaned_data.get('ipv4_mode') != 'pool':
            cleaned_data.pop('ipv4_pool', None)

        if cleaned_data.get('ipv6_mode') != 'pool':
            cleaned_data.pop('ipv6_pool', None)

        if 'data' in networktype:
            providernetworks = filter(
                None, cleaned_data.get('providernetworks_data', []))
        elif 'data-external' in networktype:
            # 'data' and 'data-external' nts cannot be consolidated
            # on same interface
            providernetworks = filter(
                None, cleaned_data.get('providernetworks_data_external', []))
        elif 'pci-passthrough' in networktype:
            providernetworks = filter(None, cleaned_data.get(
                'providernetworks_pci', []))
        elif 'pci-sriov' in networktype:
            providernetworks = filter(
                None,
                cleaned_data.get('providernetworks_sriov', []))
        else:
            providernetworks = []

        # providernetwork selection is required for 'data', 'pci-passthrough'
        # and 'pci-sriov'. It is NOT required for any other network type
        if not providernetworks:

            # Note that 1 of 3 different controls may be used to select
            # provider network, make sure to set the error on the appropriate
            # control
            if any(network in ['data', 'pci-passthrough', 'pci-sriov']
                    for network in networktype):
                raise forms.ValidationError(_(
                    "You must specify a Provider Network"))

        cleaned_data['providernetworks'] = ",".join(providernetworks)
        if 'providernetworks_data' in cleaned_data:
            del cleaned_data['providernetworks_data']
        if 'providernetworks_data_external' in cleaned_data:
            del cleaned_data['providernetworks_data_external']
        if 'providernetworks_pci' in cleaned_data:
            del cleaned_data['providernetworks_pci']
        if 'providernetworks_sriov' in cleaned_data:
            del cleaned_data['providernetworks_sriov']

        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']

        try:
            del data['host_id']

            if data['ports']:
                del data['uses']
            else:
                uses = data['uses'][:]
                data['uses'] = uses
                del data['ports']

            if not data['providernetworks']:
                del data['providernetworks']

            if not data['vlan_id'] or data['iftype'] != 'vlan':
                del data['vlan_id']
            else:
                data['vlan_id'] = unicode(data['vlan_id'])

            if any(network in data['networktype'] for network in
                   ['mgmt', 'infra', 'oam']):
                del data['imtu']
            else:
                data['imtu'] = unicode(data['imtu'])

            if data['networktype']:
                data['networktype'] = ",".join(data['networktype'])

            if data['iftype'] != 'ae':
                del data['txhashpolicy']
                del data['aemode']
            elif data['aemode'] == 'active_standby':
                del data['txhashpolicy']

            interface = api.sysinv.host_interface_create(request, **data)
            msg = _('Interface "%s" was successfully'
                    ' created.') % data['ifname']
            LOG.debug(msg)
            messages.success(request, msg)

            return interface
        except exc.ClientException as ce:
            # Allow REST API error message to appear on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure page
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _('Failed to create interface "%s".') % data['ifname']
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)


class UpdateInterface(AddInterface):
    MGMT_AE_MODE_CHOICES = (
        ('active_standby', _("active/standby")),
        ('802.3ad', _("802.3ad")),
    )

    INTERFACE_TYPE_CHOICES = (
        (None, _("<Select interface type>")),
        ('ethernet', _("ethernet")),
        ('ae', _("aggregated ethernet")),
        ('vlan', _("vlan")),
    )

    id = forms.CharField(widget=forms.widgets.HiddenInput)

    networktype = forms.MultipleChoiceField(
        label=_("Network Type"),
        help_text=_("Note: The network type of an interface cannot be changed "
                    "without first being reset back to 'none'"),
        required=True,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'switchable',
                'data-slug': 'network_type'}))

    sriov_numvfs = forms.IntegerField(
        label=_("Virtual Functions"),
        required=False,
        min_value=0,
        help_text=_("Virtual Functions for pci-sriov."),
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'network_type',
                'data-slug': 'num_vfs',
                'data-network_type-pci-sriov': 'Num VFs'}))

    sriov_totalvfs = forms.IntegerField(
        label=_("Maximum Virtual Functions"),
        required=False,
        widget=forms.widgets.TextInput(
            attrs={
                'class': 'switched',
                'readonly': 'readonly',
                'data-switch-on': 'network_type',
                'data-network_type-pci-sriov': 'Max VFs'}))

    iftypedata = forms.ChoiceField(
        label=_("Interface Type"),
        choices=INTERFACE_TYPE_CHOICES,
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(UpdateInterface, self).__init__(*args, **kwargs)

        networktype_val = kwargs['initial']['networktype']
        host_uuid = kwargs['initial']['ihost_uuid']

        # Get the SDN configuration
        sdn_enabled = kwargs['initial']['sdn_enabled']
        sdn_l3_mode = kwargs['initial']['sdn_l3_mode_enabled']

        this_interface_id = kwargs['initial']['id']

        iftype_val = kwargs['initial']['iftype']
        if 'mgmt' in networktype_val:
            self.fields['aemode'].choices = self.MGMT_AE_MODE_CHOICES

        else:
            self.fields['aemode'].choices = self.AE_MODE_CHOICES

        # Populate Address Pool selections
        pools = api.sysinv.address_pool_list(self.request)
        self.fields['ipv4_pool'].choices = _get_ipv4_pool_choices(pools)
        self.fields['ipv6_pool'].choices = _get_ipv6_pool_choices(pools)
        self.fields['ipv4_pool'].initial = kwargs['initial'].get('ipv4_pool')
        self.fields['ipv6_pool'].initial = kwargs['initial'].get('ipv6_pool')

        # Setting field to read-only doesn't actually work so we're making
        # it disabled.  This has the effect of not allowing the data through
        # to the form submission, so we require a hidden field to carry the
        # actual value through (iftype data)
        self.fields['iftype'].widget.attrs['disabled'] = 'disabled'
        self.fields['iftype'].required = False
        self.fields['iftype'].choices = self.INTERFACE_TYPE_CHOICES
        self.fields['iftypedata'].initial = kwargs['initial'].get('iftype')
        self.fields['iftype'].initial = kwargs['initial'].get('iftype')

        # Load the networktype choices
        networktype_choices = []
        used_choices = []
        if networktype_val:
            for network in networktype_val:
                label = "{}".format(network)
                net_type = (str(network), label)
                used_choices.append(str(network))
                networktype_choices.append(net_type)
        else:
            label = "{}".format("none")
            net_type = ("none", label)
            networktype_choices.append(net_type)
            used_choices.append("none")

        # if SDN L3 mode is enabled, then we may allow
        # updating an interface network type to 'data-external'
        data_choices = ['data', 'control']
        if (sdn_enabled and sdn_l3_mode):
            data_choices.append('data-external')

        if iftype_val == 'ethernet':
            choices_list = ['none', 'infra', 'oam', 'mgmt', 'pci-passthrough',
                            data_choices, 'pci-sriov', 'pxeboot']
        elif iftype_val == 'ae':
            choices_list = ['none', 'infra', 'oam', 'mgmt',
                            data_choices, 'pxeboot']
        else:
            choices_list = ['infra', 'oam', 'mgmt', data_choices]

        choices_list = flatten(choices_list)

        for choice in choices_list:
            if choice not in used_choices:
                label = "{}".format(choice)
                net_type = (str(choice), label)
                networktype_choices.append(net_type)

        self.fields['networktype'].choices = networktype_choices
        if not networktype_val:
            del kwargs['initial']['networktype']
            self.fields['networktype'].initial = ('none', 'none')

        # Get the total possible number of VFs for SRIOV network type
        port_list = api.sysinv.host_port_list(self.request,
                                              host_uuid)
        for p in port_list:
            if p.interface_uuid == this_interface_id:
                if p.sriov_totalvfs:
                    self.fields['sriov_totalvfs'].initial = p.sriov_totalvfs
                else:
                    self.fields['sriov_totalvfs'].initial = 0
                break

        initial_numvfs = kwargs['initial']['sriov_numvfs']
        if initial_numvfs:
            self.fields['sriov_numvfs'].initial = initial_numvfs
        else:
            self.fields['sriov_numvfs'].initial = 0

    def clean(self):
        cleaned_data = super(UpdateInterface, self).clean()

        cleaned_data['iftype'] = cleaned_data.get('iftypedata')
        cleaned_data.pop('iftypedata', None)

        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']
        interface_id = data['id']
        host_uuid = data['ihost_uuid']

        try:
            if data['ports']:
                del data['uses']
            else:
                uses = data['uses'][:]
                data['usesmodify'] = ','.join(uses)
                del data['ports']
                del data['uses']

            del data['id']
            del data['host_id']
            del data['ihost_uuid']

            if not data['vlan_id'] or data['iftype'] != 'vlan':
                del data['vlan_id']
            else:
                data['vlan_id'] = unicode(data['vlan_id'])

            data['imtu'] = unicode(data['imtu'])

            if data['iftype'] != 'ae':
                del data['txhashpolicy']
                del data['aemode']
            elif data['aemode'] == 'active_standby':
                del data['txhashpolicy']

            if 'none' in data['networktype']:
                avail_port_list = api.sysinv.host_port_list(
                    self.request, host_uuid)
                current_interface = api.sysinv.host_interface_get(
                    self.request, interface_id)
                if data['iftype'] != 'ae' or data['iftype'] != 'vlan':
                    for p in avail_port_list:
                        if p.interface_uuid == current_interface.uuid:
                            data['ifname'] = p.get_port_display_name()
                            break

                if any(nt in ['data', 'data-external'] for nt in
                        [str(current_interface.networktype).split(",")]):
                    data['providernetworks'] = 'none'

            if not data['providernetworks']:
                del data['providernetworks']

            if 'sriov_numvfs' in data:
                data['sriov_numvfs'] = unicode(data['sriov_numvfs'])

            # Explicitly set iftype when user selects pci-pt or pci-sriov
            network_type = \
                flatten(list(nt) for nt in self.fields['networktype'].choices)
            if 'pci-passthrough' in network_type or \
               ('pci-sriov' in network_type and data['sriov_numvfs']):
                current_interface = api.sysinv.host_interface_get(
                    self.request, interface_id)
                if current_interface.iftype != 'ethernet':
                    # Only ethernet interfaces can be pci-sriov
                    msg = _('pci-passthrough or pci-sriov can only'
                            ' be set on ethernet interfaces')
                    messages.error(request, msg)
                    LOG.error(msg)
                    # Redirect to failure pg
                    redirect = reverse(self.failure_url, args=[host_id])
                    return shortcuts.redirect(redirect)
                else:
                    data['iftype'] = current_interface.iftype

            del data['sriov_totalvfs']
            if 'pci-sriov' not in data['networktype']:
                del data['sriov_numvfs']

            if data['networktype']:
                data['networktype'] = ",".join(data['networktype'])

            interface = api.sysinv.host_interface_update(request, interface_id,
                                                         **data)

            # FIXME: this should be done under
            #  the interface update API of sysinv
            # Update Ports' iinterface_uuid attribute
            # port_list = api.sysinv.host_port_list(request, host_uuid)
            # for p in port_list:
            # if p.uuid in ports:
            #        pdata = { 'interface_uuid' : interface.uuid }
            #        api.sysinv.host_port_update(request, p.uuid, **pdata)
            #    elif p.interface_uuid == interface.uuid:
            #        pdata = { 'interface_uuid' : '0' }
            #        api.sysinv.host_port_update(request, p.uuid, **pdata)

            msg = _('Interface "%s" was'
                    ' successfully updated.') % data['ifname']
            LOG.debug(msg)
            messages.success(request, msg)
            return interface

        except exc.ClientException as ce:
            # Allow REST API error message to appear on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure page
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)

        except Exception:
            msg = _('Failed to update interface "%s".') % data['ifname']
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)
