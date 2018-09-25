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
from django.conf import settings
from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard.api import neutron
from starlingx_dashboard.api import sysinv

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


def _get_network_choices(networks):
    PLATFORM_NETWORK_TYPES = ['pxeboot',
                              'mgmt',
                              'infra',
                              'oam']
    choices = []
    for n in networks:
        if n.type in PLATFORM_NETWORK_TYPES:
            choices.append((n.uuid, "{} (type={})".format(n.name, n.type)))
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
            interfaceProfile = sysinv.host_interfaceprofile_create(request,
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
    INTERFACE_CLASS_CHOICES = (
        ('none', _("none")),
        ('platform', _("platform")),
        ('data', _("data")),
        ('pci-sriov', _("pci-sriov")),
        ('pci-passthrough', _("pci-passthrough")),
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

    ifclass = forms.ChoiceField(
        label=_("Interface Class"),
        required=True,
        choices=INTERFACE_CLASS_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'ifclass'}))

    iftype = forms.ChoiceField(
        label=_("Interface Type"),
        required=True,
        choices=INTERFACE_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
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

    networks = forms.MultipleChoiceField(
        label=_("Platform Network(s)"),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ifclass',
                'data-ifclass-platform': 'Platform Network(s)'}))

    providernetworks_data = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ifclass',
                'data-ifclass-data': ''},
            empty_value=_("No provider networks available "
                          "for this interface class.")))

    providernetworks_pci = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ifclass',
                'data-ifclass-pci-passthrough': ''},
            empty_value=_("No provider networks available "
                          "for this interface class.")))

    providernetworks_sriov = MultipleChoiceField(
        label=_("Provider Network(s)"),
        required=False,
        widget=CheckboxSelectMultiple(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ifclass',
                'data-ifclass-pci-sriov': ''},
            empty_value=_("No provider networks available "
                          "for this interface class.")))

    imtu = forms.IntegerField(
        label=_("MTU"),
        initial=1500,
        min_value=576,
        max_value=9216,
        required=False,
        help_text=_("Maximum Transmit Unit."),
        error_messages={'invalid': _('MTU must be '
                                     'between 576 and 9216 bytes.')},
        widget=forms.TextInput())

    ipv4_mode = forms.ChoiceField(
        label=_("IPv4 Addressing Mode"),
        required=False,
        initial='disabled',
        choices=IPV4_MODE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-slug': 'ipv4_mode',
                'data-switch-on': 'ifclass',
                'data-ifclass-data': 'IPv4 Addressing Mode'}))

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
                'data-switch-on': 'ifclass',
                'data-ifclass-data': 'IPv6 Addressing Mode',
                'data-ifclass-control': 'IPv6 Addressing Mode'}))

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
            current_interface = sysinv.host_interface_get(
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
        pools = sysinv.address_pool_list(self.request)
        self.fields['ipv4_pool'].choices = _get_ipv4_pool_choices(pools)
        self.fields['ipv6_pool'].choices = _get_ipv6_pool_choices(pools)

        # Populate Network Choices
        networks = sysinv.network_list(self.request)
        network_choices = _get_network_choices(networks)
        self.fields['networks'].choices = network_choices

        # Populate Provider Network Choices by querying Neutron
        self.extras = {}
        interfaces = sysinv.host_interface_list(self.request, host_uuid)

        used_providernets = []
        for i in interfaces:
            if i.ifclass == 'data' and \
                    i.providernetworks and \
                            i.uuid != this_interface_id:
                used_providernets = used_providernets + \
                    i.providernetworks.split(",")

        providernet_choices = []
        providernet_filtered = []
        if getattr(self.request.user, 'services_region', None) == 'RegionOne' \
                and getattr(settings, 'DC_MODE', False):
            nt_choices = self.fields['ifclass'].choices
            self.fields['ifclass'].choices = [i for i in nt_choices if
                                              i[0] != 'data']
        else:
            providernets = neutron.provider_network_list(self.request)
            for provider in providernets:
                label = "{} (mtu={})".format(provider.name, provider.mtu)
                providernet = (str(provider.name), label)
                providernet_choices.append(providernet)
                if provider.name not in used_providernets:
                    providernet_filtered.append(providernet)

        self.fields['providernetworks_data'].choices = providernet_filtered
        if (type(self) is UpdateInterface):
            self.fields['providernetworks_pci'].choices = providernet_choices
            self.fields['providernetworks_sriov'].choices = providernet_choices

        if current_interface:
            # update operation
            if not current_interface.uses:
                # update default interfaces
                self.fields['uses'].widget = forms.widgets.HiddenInput()
                avail_port_list = sysinv.host_port_list(
                    self.request, host_uuid)
                for p in avail_port_list:
                    if p.interface_uuid == this_interface_id:
                        self.fields['ports'].initial = p.uuid
            else:
                # update non default interfaces
                avail_interface_list = sysinv.host_interface_list(
                    self.request, host_uuid)
                interface_tuple_list = []
                for i in avail_interface_list:
                    if i.uuid != current_interface.uuid:
                        interface_tuple_list.append(
                            (i.uuid, "%s (%s, %s)" %
                             (i.ifname, i.imac, i.ifclass)))

                uses_initial = [i.uuid for i in avail_interface_list if
                                i.ifname in current_interface.uses]

                self.fields['uses'].initial = uses_initial
                self.fields['uses'].choices = interface_tuple_list

            if current_interface.vlan_id:
                self.fields['vlan_id'].initial = current_interface.vlan_id

        else:
            # add operation
            avail_interface_list = sysinv.host_interface_list(
                self.request, host_uuid)
            interface_tuple_list = []
            for i in avail_interface_list:
                interface_tuple_list.append(
                    (i.uuid, "%s (%s, %s)" %
                     (i.ifname, i.imac, i.ifclass)))
            self.fields['uses'].choices = interface_tuple_list
            self.fields['ifclass'].initial = ('none', 'none')

    def clean(self):
        cleaned_data = super(AddInterface, self).clean()
        ifclass = cleaned_data.get('ifclass', 'none')

        if ifclass != 'platform':
            cleaned_data['networks'] = []

        if ifclass != 'data':
            cleaned_data.pop('ipv4_mode', None)
            cleaned_data.pop('ipv6_mode', None)

        if cleaned_data.get('ipv4_mode') != 'pool':
            cleaned_data.pop('ipv4_pool', None)

        if cleaned_data.get('ipv6_mode') != 'pool':
            cleaned_data.pop('ipv6_pool', None)

        if ifclass == 'data':
            providernetworks = filter(
                None, cleaned_data.get('providernetworks_data', []))
        elif ifclass == 'pci-passthrough':
            providernetworks = filter(None, cleaned_data.get(
                'providernetworks_pci', []))
        elif ifclass == 'pci-sriov':
            providernetworks = filter(
                None,
                cleaned_data.get('providernetworks_sriov', []))
        else:
            providernetworks = []

        # providernetwork selection is required for 'data', 'pci-passthrough'
        # and 'pci-sriov'. It is NOT required for any other interface class
        if not providernetworks:

            # Note that 1 of 3 different controls may be used to select
            # provider network, make sure to set the error on the appropriate
            # control
            if ifclass in ['data', 'pci-passthrough', 'pci-sriov']:
                raise forms.ValidationError(_(
                    "You must specify a Provider Network"))

        cleaned_data['providernetworks'] = ",".join(providernetworks)
        if 'providernetworks_data' in cleaned_data:
            del cleaned_data['providernetworks_data']
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

            network_ids = []
            network_types = []
            if data['networks']:
                for n in data['networks']:
                    network = sysinv.network_get(request, n)
                    network_ids.append(str(network.id))
                    network_types.append(network.type)
                data['networks'] = network_ids

            if any(network_type in ['mgmt', 'infra', 'oam']
                   for network_type in network_types):
                del data['imtu']
            else:
                data['imtu'] = unicode(data['imtu'])

            if data['iftype'] != 'ae':
                del data['txhashpolicy']
                del data['aemode']
            elif data['aemode'] == 'active_standby':
                del data['txhashpolicy']

            interface = sysinv.host_interface_create(request, **data)
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

    sriov_numvfs = forms.IntegerField(
        label=_("Virtual Functions"),
        required=False,
        min_value=0,
        help_text=_("Virtual Functions for pci-sriov."),
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'ifclass',
                'data-slug': 'num_vfs',
                'data-ifclass-pci-sriov': 'Num VFs'}))

    sriov_totalvfs = forms.IntegerField(
        label=_("Maximum Virtual Functions"),
        required=False,
        widget=forms.widgets.TextInput(
            attrs={
                'class': 'switched',
                'readonly': 'readonly',
                'data-switch-on': 'ifclass',
                'data-ifclass-pci-sriov': 'Max VFs'}))

    iftypedata = forms.ChoiceField(
        label=_("Interface Type"),
        choices=INTERFACE_TYPE_CHOICES,
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(UpdateInterface, self).__init__(*args, **kwargs)
        ifclass_val = kwargs['initial']['ifclass']
        host_uuid = kwargs['initial']['ihost_uuid']

        # Get the SDN configuration
        sdn_enabled = kwargs['initial']['sdn_enabled']
        sdn_l3_mode = kwargs['initial']['sdn_l3_mode_enabled']

        this_interface_id = kwargs['initial']['id']

        iftype_val = kwargs['initial']['iftype']

        interface_networks = sysinv.interface_network_list_by_interface(self.request,
                                                                        this_interface_id)
        if ifclass_val == 'platform':
            # Load the networks associated with this interface
            network_choices = self.fields['networks'].choices
            network_choice_dict = dict(network_choices)
            initial_networks = []
            for i in interface_networks:
                for uuid, name in network_choice_dict.items():
                    if i.network_uuid == uuid:
                        initial_networks.append(uuid)

            self.fields['networks'].initial = initial_networks
        for i in interface_networks:
            if i.network_type == 'mgmt':
                self.fields['aemode'].choices = self.MGMT_AE_MODE_CHOICES
                break
        else:
            self.fields['aemode'].choices = self.AE_MODE_CHOICES

        # Populate Address Pool selections
        pools = sysinv.address_pool_list(self.request)
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

        # Load the ifclass choices
        ifclass_choices = []
        used_choices = []
        if ifclass_val:
            label = "{}".format(ifclass_val)
            choice = (str(ifclass_val), label)
            used_choices.append(str(ifclass_val))
            ifclass_choices.append(choice)
        else:
            label = "{}".format("none")
            val = ("none", label)
            used_choices.append("none")
            ifclass_choices.append(val)

        if iftype_val == 'ethernet':
            choices_list = ['none', 'platform', 'data', 'pci-sriov',
                            'pci-passthrough']
        elif iftype_val == 'ae':
            choices_list = ['none', 'platform', 'data']
        else:
            choices_list = ['platform', 'data']

        choices_list = flatten(choices_list)

        if getattr(self.request.user, 'services_region', None) == 'RegionOne' \
                and getattr(settings, 'DC_MODE', False):
            # Data is not available when in RegionOne of SystemController
            choices_list.remove('data')

        for choice in choices_list:
            if choice not in used_choices:
                label = "{}".format(choice)
                val = (str(choice), label)
                ifclass_choices.append(val)

        self.fields['ifclass'].choices = ifclass_choices
        if not ifclass_val:
            del kwargs['initial']['ifclass']
            self.fields['ifclass'].initial = ('none', 'none')

        # Get the total possible number of VFs for SRIOV interface class
        port_list = sysinv.host_port_list(self.request,
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

        ifclass = cleaned_data.get('ifclass')
        interface_id = cleaned_data.get('id')
        networks = cleaned_data.pop('networks', [])
        interface_networks = sysinv.interface_network_list_by_interface(self.request, interface_id)
        network_ids = []
        networks_to_add = []
        networks_to_remove = []
        interface_networks_to_remove = []
        if ifclass == 'platform' and networks:
            for i in interface_networks:
                networks_to_remove.append(i.network_id)
            for n in networks:
                network = sysinv.network_get(self.request, n)
                network_ids.append(str(network.id))
                if network.id in networks_to_remove:
                    networks_to_remove.remove(network.id)
                else:
                    networks_to_add.append(str(network.id))
            for i in interface_networks:
                if i.network_id in networks_to_remove:
                    interface_networks_to_remove.append(i.uuid)
        else:
            for i in interface_networks:
                interface_networks_to_remove.append(i.uuid)
        cleaned_data['networks'] = network_ids
        cleaned_data['networks_to_add'] = networks_to_add
        cleaned_data['interface_networks_to_remove'] = interface_networks_to_remove
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

            if not data['ifclass'] or data['ifclass'] == 'none':
                avail_port_list = sysinv.host_port_list(
                    self.request, host_uuid)
                current_interface = sysinv.host_interface_get(
                    self.request, interface_id)
                if data['iftype'] != 'ae' or data['iftype'] != 'vlan':
                    for p in avail_port_list:
                        if p.interface_uuid == current_interface.uuid:
                            data['ifname'] = p.get_port_display_name()
                            break

                if current_interface.ifclass == 'data':
                    data['providernetworks'] = 'none'

            if not data['providernetworks']:
                del data['providernetworks']

            if 'sriov_numvfs' in data:
                data['sriov_numvfs'] = unicode(data['sriov_numvfs'])

            # Explicitly set iftype when user selects pci-pt or pci-sriov
            ifclass = \
                flatten(list(nt) for nt in self.fields['ifclass'].choices)
            if 'pci-passthrough' in ifclass or \
                    ('pci-sriov' in ifclass and data['sriov_numvfs']):
                current_interface = sysinv.host_interface_get(
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
            if data['ifclass'] != 'pci-sriov':
                del data['sriov_numvfs']

            if data['networks']:
                data['networks'] = unicode(",".join(data['networks']))
            else:
                del data['networks']
            if data['networks_to_add']:
                data['networks_to_add'] = unicode(",".join(data['networks_to_add']))
            else:
                del data['networks_to_add']
            if data['interface_networks_to_remove']:
                data['interface_networks_to_remove'] = unicode(
                    ",".join(data['interface_networks_to_remove']))
            else:
                del data['interface_networks_to_remove']

            interface = sysinv.host_interface_update(request,
                                                     interface_id,
                                                     **data)

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
