#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4


import logging

from collections import OrderedDict

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class UpdateSystem(forms.SelfHandlingForm):
    system_uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    name = forms.RegexField(
        label=_("Name"),
        max_length=255,
        required=False,
        regex=r'^[\w\.\-]+$',
        error_messages={
            'invalid': _('Name may only '
                         'contain letters, numbers, underscores, '
                         'periods and hyphens.')})

    description = forms.CharField(label=_("Description"),
                                  initial='location',
                                  required=False,
                                  help_text=_("Description of System."))

    failure_url = 'horizon:admin:system_config:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateSystem, self).__init__(request, *args, **kwargs)

    def clean(self):
        cleaned_data = super(UpdateSystem, self).clean()
        return cleaned_data

    def handle(self, request, data):

        try:
            system_name = data['name']
            system_uuid = data['system_uuid']
            del data['system_uuid']

            if not data['description']:
                data['description'] = " "

            system = api.sysinv.system_update(request, system_uuid, **data)
            msg = _('System "%s" was successfully updated.') % system_name
            LOG.debug(msg)
            messages.success(request, msg)
            return system
        except Exception:
            msg = _('Failed to update system "%s".') % system_name
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdatecDNS(forms.SelfHandlingForm):
    uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    FIELD_LABEL_DNS_NAMESERVER_1 = _("DNS Name Server 1")
    FIELD_LABEL_DNS_NAMESERVER_2 = _("DNS Name Server 2")

    NAMESERVER_1 = forms.IPField(
        label=_("DNS Server 1 IP"),
        required=False,
        initial='NAMESERVER_1',
        help_text=_("IP address of NameServer 1. "
                    "If you use no DNS NameServer 1, leave blank. "),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    NAMESERVER_2 = forms.IPField(
        label=_("DNS Server 2 IP"),
        required=False,
        initial='NAMESERVER_2',
        help_text=_("IP address of NameServer 2. "
                    "If you use no DNS NameServer 2, leave blank. "),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    NAMESERVER_3 = forms.IPField(
        label=_("DNS Server 3 IP"),
        required=False,
        initial='NAMESERVER_3',
        help_text=_("IP address of NameServer 3. "
                    "If you use no DNS NameServer 3, leave blank. "),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    failure_url = 'horizon:admin:system_config:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdatecDNS, self).__init__(request, *args, **kwargs)

        # def clean(self, value):
        # super(UpdatecDNS, self).clean(value)
        # return self.regexlist

    def handle(self, request, data):
        # Here, update the maximum dns servers allowed
        max_dns_servers = 3
        send_to_sysinv = False

        try:

            if data:
                NAMESERVERS = OrderedDict()

                if 'uuid' in data.keys():
                    if not data['uuid']:
                        data['uuid'] = ' '

                else:
                    data['uuid'] = ' '

                for index in range(1, max_dns_servers + 1):
                    if data['NAMESERVER_%s' % index] and \
                            data['NAMESERVER_%s' % index] != ' ':
                        NAMESERVERS['NAMESERVER_%s' % index] = \
                            data['NAMESERVER_%s' % index]

                dns_config = api.sysinv.dns_get(request, data['uuid'])

                if hasattr(dns_config, 'uuid'):
                    dns_config_uuid = dns_config.uuid
                    if dns_config.nameservers:
                        nameservers = dns_config.nameservers.split(',')
                    else:
                        nameservers = []

                    if len(NAMESERVERS) != len(nameservers):
                        data['action'] = 'apply'
                        send_to_sysinv = True

                    else:
                        # If the value order is reversed,
                        # don't send action=apply
                        if set(nameservers) != set(NAMESERVERS.values()):
                            for index in range(len(nameservers)):

                                if nameservers[index] != \
                                        NAMESERVERS['NAMESERVER_%s' % (
                                                    index + 1)]:
                                    data['action'] = 'apply'
                                    send_to_sysinv = True
                                    # we need to do action=apply only once
                                    break

                    # sysinv accepts csv values as the nameservers
                    data['nameservers'] = ','.join(NAMESERVERS.values())

                else:
                    dns_config_uuid = ' '

                data.pop('uuid')

                for index in range(1, max_dns_servers + 1):
                    data.pop('NAMESERVER_%s' % index)

            else:
                dns_config_uuid = ' '
                data = {'nameservers': ' '}

            LOG.debug(data)

            if send_to_sysinv is True:
                my_dns = api.sysinv.dns_update(request,
                                               dns_config_uuid, **data)

                if my_dns:
                    msg = _('DNS Server was successfully updated.')

                LOG.debug(msg)
                messages.success(request, msg)

                return True if my_dns else False

            else:
                msg = _('No DNS Server changes have been made.')
                LOG.debug(msg)
                messages.info(request, msg)
                return True

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            messages.error(request, ce)
            LOG.error(ce)
            # redirect = reverse(self.failure_url)
            return False

        except Exception:
            msg = _('Failed to update DNS Server.')
            messages.error(request, msg)
            # msg = self.format_status_message(self.failure_message) + str(e)
            LOG.info(msg)
            # redirect = reverse(self.failure_url)
            exceptions.handle(request, msg)
            return False


class UpdatecNTP(forms.SelfHandlingForm):
    uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    NTP_SERVER_1 = forms.CharField(label=_("NTP Server 1 Address"),
                                   initial='NTP_SERVER_1',
                                   required=False,
                                   help_text=_("NTP Server IP or FQDN. "
                                               "If you use no NTP Server 1, "
                                               "leave blank."))

    NTP_SERVER_2 = forms.CharField(label=_("NTP Server 2 Address"),
                                   initial='NTP_SERVER_2',
                                   required=False,
                                   help_text=_("NTP Server IP or FQDN."
                                               "If you use no NTP Server 2, "
                                               "leave blank."))

    NTP_SERVER_3 = forms.CharField(label=_("NTP Server 3 Address"),
                                   initial='NTP_SERVER_3',
                                   required=False,
                                   help_text=_("NTP Server IP or FQDN."
                                               "If you use no NTP Server 3, "
                                               "leave blank."))

    failure_url = 'horizon:admin:system_config:index'
    failure_message = 'Failed to update NTP configurations.'

    def __init__(self, request, *args, **kwargs):
        super(UpdatecNTP, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        # Here, update the maximum ntp servers allowed
        max_ntp_servers = 3
        send_to_sysinv = False

        try:
            if data:
                NTPSERVERS = OrderedDict()

                if 'uuid' in data.keys():
                    if not data['uuid']:
                        data['uuid'] = ' '
                else:
                    data['uuid'] = ' '

                for index in range(1, max_ntp_servers + 1):
                    if data['NTP_SERVER_%s' % index] and data[
                            'NTP_SERVER_%s' % index] != ' ':
                        NTPSERVERS['NTP_SERVER_%s' % index] = data[
                            'NTP_SERVER_%s' % index]

                ntp_config = api.sysinv.ntp_get(request, data['uuid'])

                if hasattr(ntp_config, 'uuid'):

                    ntp_config_uuid = ntp_config.uuid
                    if ntp_config.ntpservers:
                        ntpservers = ntp_config.ntpservers.split(',')
                    else:
                        ntpservers = []

                    # if their sizes are different, then action=apply
                    if len(NTPSERVERS) != len(ntpservers):
                        data['action'] = 'apply'
                        send_to_sysinv = True

                    else:
                        # If lengths are same,
                        # check if order of values have been changed
                        if set(ntpservers) != set(NTPSERVERS.values()):
                            for index in range(len(ntpservers)):

                                if ntpservers[index] != NTPSERVERS[
                                        'NTP_SERVER_%s' % (index + 1)]:
                                    data['action'] = 'apply'
                                    send_to_sysinv = True
                                    # we need to do action=apply only once
                                    break

                    # sysinv accepts csv values as the ntpservers
                    data['ntpservers'] = ','.join(NTPSERVERS.values())

                else:
                    ntp_config_uuid = ' '

                data.pop('uuid')

                for index in range(1, max_ntp_servers + 1):
                    data.pop('NTP_SERVER_%s' % index)

            else:
                ntp_config_uuid = ' '
                data = {'ntpservers': ''}

            LOG.debug(data)

            if send_to_sysinv:
                my_ntp = \
                    api.sysinv.ntp_update(request, ntp_config_uuid, **data)

                if my_ntp:
                    msg = _('NTP configuration was successfully updated. ')
                    LOG.debug(msg)
                    messages.success(request, msg)
                    return True
                else:
                    return False

            else:
                msg = _('No NTP Server changes have been made.')
                LOG.debug(msg)
                messages.info(request, msg)
                return True

        except exc.ClientException as ce:
            messages.error(request, ce)
            # Display REST API error on the GUI
            LOG.error(ce)
            # redirect = reverse(self.failure_url)
            return False

        except Exception:
            msg = _('Failed to update NTP configuration.')
            messages.error(request, msg)
            LOG.info(msg)
            # redirect = reverse(self.failure_url)
            return False


class UpdatecEXT_OAM(forms.SelfHandlingForm):
    uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    FIELD_LABEL_EXTERNAL_OAM_SUBNET = _("External OAM Subnet")
    FIELD_LABEL_EXTERNAL_OAM_GATEWAY_ADDRESS = \
        _("External OAM Gateway Address")
    FIELD_LABEL_EXTERNAL_OAM_FLOATING_ADDRESS = _(
        "External OAM Floating Address")
    FIELD_LABEL_EXTERNAL_OAM_0_ADDRESS = _("External OAM 0 ADDRESS")
    FIELD_LABEL_EXTERNAL_OAM_1_ADDRESS = _("External OAM 1 ADDRESS")

    EXTERNAL_OAM_SUBNET = forms.IPField(
        label=_("External OAM Subnet"),
        required=True,
        initial='EXTERNAL_OAM_SUBNET',
        help_text=_("Subnet address in CIDR format (e.g. 10.10.10.0/24) "),
        version=forms.IPv4 | forms.IPv6,
        mask=True)

    EXTERNAL_OAM_GATEWAY_ADDRESS = forms.IPField(
        label=_("External OAM Gateway Address"),
        required=False,
        initial='EXTERNAL_OAM_GATEWAY_ADDRESS',
        help_text=_("IP address of External OAM Gateay (e.g. 192.168.0.254)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    EXTERNAL_OAM_FLOATING_ADDRESS = forms.IPField(
        label=_("External OAM Floating Address"),
        required=True,
        initial='EXTERNAL_OAM_FLOATING_ADDRESS',
        help_text=_("IP address of Floating External OAM "
                    "(e.g. 192.168.0.254)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    EXTERNAL_OAM_0_ADDRESS = forms.IPField(
        label=_("External OAM controller-0 Address"),
        required=True,
        initial='EXTERNAL_OAM_0_ADDRESS',
        help_text=_("controller-0 External OAM IP Address"
                    "(e.g. 192.168.0.254)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    EXTERNAL_OAM_1_ADDRESS = forms.IPField(
        label=_("External OAM controller-1 Address"),
        required=True,
        initial='EXTERNAL_OAM_1_ADDRESS',
        help_text=_(
            "controller-1 External OAM IP Address (e.g. 192.168.0.254)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    failure_url = 'horizon:admin:system_config:index'
    failure_message = 'Failed to update OAM configuration.'

    def __init__(self, request, *args, **kwargs):
        super(UpdatecEXT_OAM, self).__init__(request, *args, **kwargs)

        if not kwargs['initial'].get('EXTERNAL_OAM_GATEWAY_ADDRESS'):
            self.fields['EXTERNAL_OAM_GATEWAY_ADDRESS'].widget = \
                forms.widgets.HiddenInput()
        if api.sysinv.is_system_mode_simplex(request):
            self.fields['EXTERNAL_OAM_FLOATING_ADDRESS'].label = \
                _("External OAM Address")
            self.fields['EXTERNAL_OAM_FLOATING_ADDRESS'].help_text = \
                _("IP address of External OAM (e.g. 192.168.0.254)")
            self.fields['EXTERNAL_OAM_0_ADDRESS'].widget = \
                forms.widgets.HiddenInput()
            self.fields['EXTERNAL_OAM_1_ADDRESS'].widget = \
                forms.widgets.HiddenInput()
            self.fields['EXTERNAL_OAM_0_ADDRESS'].required = False
            self.fields['EXTERNAL_OAM_1_ADDRESS'].required = False

    def clean(self):
        cleaned_data = super(UpdatecEXT_OAM, self).clean()
        return cleaned_data

    def handle(self, request, data):

        send_to_sysinv = False

        try:
            if data:
                if 'uuid' in data.keys():
                    if not data['uuid']:
                        data['uuid'] = ' '
                else:
                    data['uuid'] = ' '

                oam_data = api.sysinv.extoam_get(request, data['uuid'])

                if hasattr(oam_data, 'uuid'):
                    oam_data_uuid = oam_data.uuid

                    EXTERNAL_OAM_SUBNET = oam_data.oam_subnet
                    EXTERNAL_OAM_FLOATING_ADDRESS = oam_data.oam_floating_ip
                    EXTERNAL_OAM_GATEWAY_ADDRESS = oam_data.oam_gateway_ip
                    EXTERNAL_OAM_0_ADDRESS = oam_data.oam_c0_ip
                    EXTERNAL_OAM_1_ADDRESS = oam_data.oam_c1_ip

                    data['oam_subnet'] = data['EXTERNAL_OAM_SUBNET']
                    data['oam_floating_ip'] = data[
                        'EXTERNAL_OAM_FLOATING_ADDRESS']

                    if data['EXTERNAL_OAM_GATEWAY_ADDRESS']:
                        data['oam_gateway_ip'] = \
                            data['EXTERNAL_OAM_GATEWAY_ADDRESS']

                    if not api.sysinv.is_system_mode_simplex(request):
                        data['oam_c0_ip'] = data['EXTERNAL_OAM_0_ADDRESS']
                        data['oam_c1_ip'] = data['EXTERNAL_OAM_1_ADDRESS']

                    if EXTERNAL_OAM_SUBNET != \
                            data['EXTERNAL_OAM_SUBNET'] or \
                       EXTERNAL_OAM_FLOATING_ADDRESS != \
                            data['EXTERNAL_OAM_FLOATING_ADDRESS'] or \
                       EXTERNAL_OAM_GATEWAY_ADDRESS != \
                            data['EXTERNAL_OAM_GATEWAY_ADDRESS'] or \
                       EXTERNAL_OAM_0_ADDRESS != \
                            data['EXTERNAL_OAM_0_ADDRESS'] or \
                       EXTERNAL_OAM_1_ADDRESS != \
                            data['EXTERNAL_OAM_1_ADDRESS'] != \
                            oam_data.oam_c1_ip:

                        data['action'] = 'apply'
                        send_to_sysinv = True

                else:
                    oam_data_uuid = ' '

                data.pop('uuid')
                data.pop('EXTERNAL_OAM_0_ADDRESS')
                data.pop('EXTERNAL_OAM_1_ADDRESS')
                data.pop('EXTERNAL_OAM_SUBNET')
                data.pop('EXTERNAL_OAM_FLOATING_ADDRESS')
                data.pop('EXTERNAL_OAM_GATEWAY_ADDRESS')
            else:
                oam_data_uuid = ' '
                data = {'oam_subnet': '', 'oam_floating_ip': '',
                        'oam_gateway_ip': '',
                        'oam_c0_ip': '', 'oam_c1_ip': ''}

            if send_to_sysinv:
                LOG.info("OAM sendtosysinv data=%s", data)

                myoam_data = api.sysinv.extoam_update(self.request,
                                                      oam_data_uuid,
                                                      **data)
                if myoam_data:
                    msg = _('OAM configuration was successfully updated. ')

                LOG.debug(msg)
                messages.success(request, msg)

                return True if myoam_data else False

            else:
                msg = _('No OAM configuration changes have been made.')
                LOG.debug(msg)
                messages.info(request, msg)
                return True

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            messages.error(request, ce)
            LOG.error(ce)
            # redirect = reverse(self.failure_url)
            return False

        except Exception:
            msg = _('Failed to update OAM configuration.')
            messages.error(request, msg)
            # msg = self.format_status_message(self.failure_message) + str(e)
            LOG.info(msg)
            # redirect = reverse(self.failure_url)
            exceptions.handle(request, msg)
            return False


class UpdateiStorage(forms.SelfHandlingForm):
    uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    database = forms.IntegerField(
        label=_("Database Storage (GiB)"),
        required=True,
        help_text=_("Database storage space in gibibytes."),
        min_value=0)

    cgcs = forms.IntegerField(
        label=_("CGCS Storage (GiB)"),
        required=True,
        help_text=_("CGCS image storage space in gibibytes."),
        min_value=0)

    backup = forms.IntegerField(
        label=_("Backup Storage (GiB)"),
        required=True,
        help_text=_("Backup storage space in gibibytes."),
        min_value=0)

    scratch = forms.IntegerField(
        label=_("Scratch Storage (GiB)"),
        required=True,
        help_text=_("Platform Scratch storage space in gibibytes."),
        min_value=0)

    extension = forms.IntegerField(
        label=_("Extension Storage (GiB)"),
        required=True,
        help_text=_("Platform Extension storage space in gibibytes."),
        min_value=0)

    img_conversions = forms.IntegerField(
        label=_("Image Conversion Space (GiB)"),
        required=False,
        help_text=_("Disk space for image conversion in gibibytes."),
        min_value=0)

    patch_vault = forms.IntegerField(
        label=_("Patch-Vault Storage (GiB)"),
        required=False,
        help_text=_("Platform Patch-Vault storage space in gibibytes."),
        min_value=0)

    ceph_mon = forms.IntegerField(
        label=_("Ceph Mon Storage (GiB)"),
        required=False,
        help_text=_("Ceph Monitor volume size in gibibytes."),
        min_value=0)

    failure_url = 'horizon:admin:system_config:index'
    failure_message = 'Failed to update filesystem configuration.'

    def __init__(self, request, *args, **kwargs):
        super(UpdateiStorage, self).__init__(request, *args, **kwargs)
        if not kwargs['initial'].get('ceph_mon'):
            del self.fields['ceph_mon']
        if not kwargs['initial'].get('patch_vault'):
            del self.fields['patch_vault']

    def clean(self):
        cleaned_data = super(UpdateiStorage, self).clean()
        return cleaned_data

    def handle(self, request, data):
        system_uuid = data['uuid']
        data.pop('uuid')

        new_data = {k.replace("_", "-"): v for k, v in data.items()}
        try:
            fs_list = api.sysinv.controllerfs_list(self.request)
            fs_data = {fs.name: fs.size for fs in fs_list}

            for k, v in fs_data.items():
                if new_data.get(k, None) == v:
                    del new_data[k]
                elif k == 'ceph-mon':
                    ceph_data = {'ceph_mon_gib': 0}
                    ceph_data['ceph_mon_gib'] = new_data.get(k)
                    del new_data[k]
                    ceph_mons = api.sysinv.cephmon_list(request)
                    if ceph_mons:
                        for ceph_mon in ceph_mons:
                            if hasattr(ceph_mon, 'uuid'):
                                my_storage = api.sysinv.ceph_mon_update(
                                    request, ceph_mon.uuid, **ceph_data)
                                if not my_storage:
                                    return False

            if new_data:
                my_storage = api.sysinv.storfs_update_many(request,
                                                           system_uuid,
                                                           **new_data)
            return True

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            messages.error(request, ce)
            LOG.error(ce)
            return False

        except Exception as e:
            LOG.error('Exception with %s', e)
            msg = _('Failed to update filesystem configuration.')
            messages.error(request, msg)
            LOG.info(msg)
            exceptions.handle(request, msg)
            return False


class UpdateiStoragePools(forms.SelfHandlingForm):
    tier_name = forms.CharField(widget=forms.widgets.HiddenInput)
    uuid = forms.CharField(widget=forms.widgets.HiddenInput)

    failure_url = 'horizon:admin:system_config:index'
    failure_message = ('Failed to update size of ceph pools.'
                       ' Ceph cluster may be down, check cluster status'
                       ' and try again')

    def __init__(self, request, *args, **kwargs):
        super(UpdateiStoragePools, self).__init__(request, *args, **kwargs)
        self._tier_name = kwargs['initial']['tier_name']

        js_attrs = {'onchange': 'add_total_quota()',
                    'onkeypress': 'this.onchange()',
                    'onpaste': 'this.onchange()',
                    'oninput': 'this.onchange()',
                    'onload': 'this.onchange()'}

        self.fields['cinder_pool_gib'] = forms.IntegerField(
            label=_("Cinder Volumes Pool (GiB)"),
            required=True,
            help_text=_("Storage space allocated to cinder volumes in "
                        "gibibytes."),
            min_value=0,
            widget=forms.NumberInput(attrs=js_attrs))

        if self._tier_name == 'storage':
            self.fields['glance_pool_gib'] = forms.IntegerField(
                label=_("Glance Image Pool (GiB)"),
                required=True,
                help_text=_("Storage space allocated to glance images in "
                            "gibibytes."),
                min_value=0,
                widget=forms.NumberInput(attrs=js_attrs))

            self.fields['ephemeral_pool_gib'] = forms.IntegerField(
                label=_("Ephemeral Storage Pool(GiB)"),
                required=True,
                help_text=_("Storage space allocated to nova ephemeral "
                            "instance disks in gibibytes."),
                min_value=0,
                widget=forms.NumberInput(attrs=js_attrs))

            self.fields['object_pool_gib'] = forms.IntegerField(
                label=_("Object Storage Pool(GiB)"),
                required=True,
                help_text=_("Storage space allocated to objects in "
                            "gibibytes."),
                min_value=0,
                widget=forms.NumberInput(attrs=js_attrs))

    def clean(self):
        cleaned_data = super(UpdateiStoragePools, self).clean()
        return cleaned_data

    def handle(self, request, data):

        send_to_sysinv = False
        try:
            if data:
                if 'uuid' in data.keys():
                    if not data['uuid']:
                        data['uuid'] = ' '
                else:
                    data['uuid'] = ' '

                storage_config = api.sysinv.storagepool_get(request,
                                                            data['uuid'])
                data.pop('uuid')

                if hasattr(storage_config, 'uuid'):
                    storage_config_uuid = storage_config.uuid

                    STORAGE_VALUES = {}
                    if hasattr(storage_config, 'cinder_pool_gib'):
                        STORAGE_VALUES['cinder_pool_gib'] = \
                            unicode(storage_config._cinder_pool_gib)
                    if hasattr(storage_config, 'glance_pool_gib'):
                        STORAGE_VALUES['glance_pool_gib'] = \
                            unicode(storage_config._glance_pool_gib)
                    if hasattr(storage_config, 'ephemeral_pool_gib'):
                        STORAGE_VALUES['ephemeral_pool_gib'] = \
                            unicode(storage_config._ephemeral_pool_gib)
                    if hasattr(storage_config, 'object_pool_gib'):
                        STORAGE_VALUES['object_pool_gib'] = \
                            unicode(storage_config._object_pool_gib)

                    for key in data.keys():
                        data[key] = unicode(data[key])

                    LOG.info("initial send_to_sysinv=%s", send_to_sysinv)
                    if len(STORAGE_VALUES) != len(data):
                        send_to_sysinv = True
                    else:
                        for key in STORAGE_VALUES.keys():
                            if STORAGE_VALUES[key] != data[key]:
                                send_to_sysinv = True
                                break
                else:
                    storage_config_uuid = ' '
            else:
                storage_config_uuid = ' '
                data = {'cinder_pool_gib': '',
                        'glance_pool_gib': '',
                        'ephemeral_pool_gib': '',
                        'object_pool_gib': ''}

            LOG.debug(data)

            if send_to_sysinv:
                my_storage = api.sysinv.storpool_update(request,
                                                        storage_config_uuid,
                                                        **data)

                if my_storage:
                    msg = _(
                        'Size of Ceph storage pools was successfully updated.')
                    LOG.debug(msg)
                    messages.success(request, msg)
                    return True

                return False

            else:
                msg = _('Size of Ceph storage pools have not been updated.')
                LOG.debug(msg)
                messages.info(request, msg)
                return True

        except exc.ClientException as ce:
            messages.error(request, ce)
            # Display REST API error on the GUI
            LOG.error(ce)
            return False

        except Exception:
            msg = _('Failed to update sizes of Ceph storage pools.')
            messages.error(request, msg)
            LOG.info(msg)
            exceptions.handle(request, msg)
            return False


############################################################
#                   SDN Controller Forms                   #
############################################################

SDN_TRANSPORT_MODE_CHOICES = (
    ('tcp', _("TCP")),
    ('udp', _("UDP")),
    ('tls', _("TLS")),
)

SDN_ADMIN_STATE_CHOICES = (
    ('enabled', _("Administratively Enabled")),
    ('disabled', _("Administratively Disabled")),
)


class SDNControllerForm(forms.SelfHandlingForm):
    ip_address = forms.CharField(label=_("SDN Controller Host"),
                                 required=True,
                                 help_text=_("Provide a Fully Qualified "
                                             "Domain Name (FQDN) or IP "
                                             "Address value."))

    port = forms.IntegerField(label=_("SDN Controller Port #"),
                              help_text=_("Remote listening port "
                                          "on the SDN controller."),
                              min_value=1,
                              required=True)

    transport = forms.ChoiceField(label=_("SDN Control channel"
                                          " transport mode"),
                                  required=False,
                                  help_text=_("The transport protocol "
                                              "being used for the SDN "
                                              "control channel."),
                                  choices=SDN_TRANSPORT_MODE_CHOICES)

    state = forms.ChoiceField(label=_("SDN Controller"
                                      " administrative state"),
                              required=True,
                              choices=SDN_ADMIN_STATE_CHOICES)


class CreateSDNController(SDNControllerForm):

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def __init__(self, request, *args, **kwargs):
        super(CreateSDNController, self).__init__(request, *args, **kwargs)

        # specify default values for optional choices
        self.initial['transport'] = 'tcp'
        self.initial['state'] = 'enabled'

    def handle(self, request, data):
        try:
            # Don't prevalidate. Let SysInv handle it
            controller = api.sysinv.sdn_controller_create(request, **data)
            msg = (_('SDN Controller was successfully created.'))
            LOG.debug(msg)
            messages.success(request, msg)
            return controller
        except Exception:
            redirect = reverse('horizon:admin:system_config:index')
            msg = _('Failed to create SDN Controller.')
            exceptions.handle(request, msg, redirect=redirect)


class UpdateSDNController(SDNControllerForm):
    uuid = forms.CharField(widget=forms.HiddenInput)
    failure_url = 'horizon:admin:system_config:index'

    def handle(self, request, data):
        try:
            controller = api.sysinv.sdn_controller_update(
                request, **data)
            msg = (_('SDN Controller %s was successfully updated.') %
                   data['uuid'])
            LOG.debug(msg)
            messages.success(request, msg)
            return controller
        except Exception:
            msg = (_('Failed to update SDN Controller %s') %
                   data['uuid'])
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class EditPipeline(forms.SelfHandlingForm):
    pipeline_name = forms.CharField(label=_("Name"),
                                    initial='name',
                                    required=False,
                                    help_text=_("Name of the Pipeline."),
                                    widget=forms.TextInput(
                                        attrs={'readonly': 'readonly'}))

    location = forms.CharField(label=_("Location"),
                               initial='location',
                               required=False,
                               help_text=_("Location of PM file."))

    enabled = forms.BooleanField(label=_("Enabled"),
                                 initial='enabled',
                                 required=False,
                                 help_text=_(
                                     "Enable or disable writing to file"))

    max_bytes = forms.IntegerField(initial='max_bytes',
                                   label=_('Max Bytes'),
                                   help_text=_(
                                       'Maximum size (in bytes) to allow the'
                                       ' file to grow before backing it up.'),
                                   required=False)

    backup_count = forms.IntegerField(initial='backup_count',
                                      label=_('Backup Count'),
                                      help_text=_('Number of files to keep.'),
                                      required=False)

    compress = forms.BooleanField(label=_("Compress Backups"),
                                  initial='compress',
                                  required=False,
                                  help_text=_("Gzip compress the"
                                              " backup files"))

    failure_url = 'horizon:admin:system_config:index'

    def __init__(self, request, *args, **kwargs):
        super(EditPipeline, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        pipeline_name = data['pipeline_name']
        try:
            # Remove entries from this update that can not be updated
            del data['pipeline_name']

            # Update the pipeline using the API call
            pipeline = api.ceilometer.pipeline_update(request, pipeline_name,
                                                      data)

            msg = _('Pipeline "%s" was successfully updated.') % pipeline_name
            LOG.debug(msg)
            messages.success(request, msg)
            return pipeline

        except Exception as ex:
            msg = _('Failed to update pipeline "%s".') % pipeline_name
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, str(ex), redirect=redirect)
