#
# Copyright (c) 2013-2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

import cpu_functions.utils as icpu_utils

from cgtsclient.common import constants
from cgtsclient import exc
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows
from openstack_dashboard import api

LOG = logging.getLogger(__name__)

PERSONALITY_CHOICES = (
    (api.sysinv.PERSONALITY_COMPUTE, _("Compute")),
    (api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
    (api.sysinv.PERSONALITY_STORAGE, _("Storage")),
)

FIELD_LABEL_PERFORMANCE_PROFILE = _("Performance Profile")
PERFORMANCE_CHOICES = (
    (api.sysinv.SUBFUNCTIONS_COMPUTE, _("Standard")),
    (api.sysinv.SUBFUNCTIONS_COMPUTE + ','
     + api.sysinv.SUBFUNCTIONS_LOWLATENCY, _("Low Latency")),
)

PERSONALITY_CHOICES_WITHOUT_STORAGE = (
    (api.sysinv.PERSONALITY_COMPUTE, _("Compute")),
    (api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
)

PERSONALITY_CHOICE_CONTROLLER = (
    (api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
)

BM_TYPES_CHOICES = (
    (api.sysinv.BM_TYPE_NULL, _('No Board Management')),
    (api.sysinv.BM_TYPE_GENERIC, _("Board Management Controller")),
)


def ifprofile_applicable(host, profile):
    for interface in profile.interfaces:
        if (api.sysinv.PERSONALITY_COMPUTE == host._personality and
                interface.networktype == 'oam'):
            return False
        if (api.sysinv.PERSONALITY_COMPUTE not in host._subfunctions and
                interface.networktype == 'data'):
            return False
    return True


def cpuprofile_applicable(host, profile):
    if (host.sockets == profile.sockets and
            host.physical_cores == profile.physical_cores and
            host.hyperthreading == profile.hyperthreading):
        errorstring = icpu_utils.check_core_functions(host.subfunctions,
                                                      profile.cpus)
        if not errorstring:
            return True
    return False


def diskprofile_applicable(host, diskprofile):
    # if host contain sufficient number of disks for diskprofile
    if not len(host.disks) >= len(diskprofile.disks):
        return False

    if api.sysinv.PERSONALITY_COMPUTE in host._subfunctions:
        if diskprofile.lvgs:
            for lvg in diskprofile.lvgs:
                if (hasattr(lvg, 'lvm_vg_name') and
                   'nova-local' in lvg.lvm_vg_name):
                    return True
                else:
                    return False
        else:
            return False
    elif api.sysinv.PERSONALITY_STORAGE in host._subfunctions:
        if diskprofile.stors:
            if (host.capabilities.get('pers_subtype') ==
                    api.sysinv.PERSONALITY_SUBTYPE_CEPH_CACHING):
                for pstor in diskprofile.stors:
                    if pstor.function == 'journal':
                        return False
            return True
        else:
            return False

    return True


def memoryprofile_applicable(host, personality, profile):
    # If profile has more than in host
    if not len(host.memory) >= len(profile.memory):
        return False
    if len(host.nodes) != len(profile.nodes):
        return False
    if 'compute' not in personality:
        return False
    return True


def profile_get_uuid(request, profilename):
    ifprofiles = api.sysinv.host_interfaceprofile_list(request)
    cpuprofiles = api.sysinv.host_cpuprofile_list(request)
    storprofiles = api.sysinv.host_diskprofile_list(request)
    memoryprofiles = api.sysinv.host_memprofile_list(request)

    profiles = ifprofiles + cpuprofiles + storprofiles + memoryprofiles

    for iprofile in profiles:
        if iprofile.profilename == profilename:
            break
    else:
        raise forms.ValidationError("Profile not found: %s" % profilename)
    return iprofile.uuid


class AddHostInfoAction(workflows.Action):
    FIELD_LABEL_PERSONALITY = _("Personality")
    FIELD_LABEL_HOSTNAME = _("Host Name")
    FIELD_LABEL_MGMT_MAC = _("Management MAC Address")
    FIELD_LABEL_MGMT_IP = _("Management IP Address")

    personality = forms.ChoiceField(label=FIELD_LABEL_PERSONALITY,
                                    help_text=_("Host Personality"),
                                    choices=PERSONALITY_CHOICES,
                                    widget=forms.Select(
                                        attrs={'class': 'switchable',
                                               'data-slug': 'personality'}))

    subfunctions = forms.ChoiceField(
        label=FIELD_LABEL_PERFORMANCE_PROFILE,
        choices=PERFORMANCE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   api.sysinv.PERSONALITY_COMPUTE: _(
                       "Personality Sub-Type")}))

    hostname = forms.RegexField(label=FIELD_LABEL_HOSTNAME,
                                max_length=255,
                                required=False,
                                regex=r'^[\w\.\-]+$',
                                error_messages={
                                    'invalid':
                                        _('Name may only contain letters,'
                                          ' numbers, underscores, '
                                          'periods and hyphens.')},
                                widget=forms.TextInput(
                                    attrs={'class': 'switched',
                                           'data-switch-on': 'personality',
                                           'data-personality-' +
                                           api.sysinv.PERSONALITY_COMPUTE:
                                               FIELD_LABEL_HOSTNAME,
                                           }))

    mgmt_mac = forms.MACAddressField(
        label=FIELD_LABEL_MGMT_MAC,
        widget=forms.TextInput(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   api.sysinv.PERSONALITY_COMPUTE: FIELD_LABEL_MGMT_MAC,
                   'data-personality-' +
                   api.sysinv.PERSONALITY_CONTROLLER: FIELD_LABEL_MGMT_MAC,
                   'data-personality-' +
                   api.sysinv.PERSONALITY_STORAGE: FIELD_LABEL_MGMT_MAC,
                   }))

    class Meta(object):
        name = _("Host Info")
        help_text = _(
            "From here you can add the configuration for a new host.")

    def __init__(self, request, *arg, **kwargs):
        super(AddHostInfoAction, self).__init__(request, *arg, **kwargs)

        # pesonality cannot be storage if ceph is not configured
        cinder_backend = api.sysinv.get_cinder_backend(request)
        if api.sysinv.CINDER_BACKEND_CEPH not in cinder_backend:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

        # All-in-one system, personality can only be controller.
        systems = api.sysinv.system_list(request)
        system_type = systems[0].to_dict().get('system_type')
        if system_type == constants.TS_AIO:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICE_CONTROLLER
            self.fields['personality'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super(AddHostInfoAction, self).clean()
        return cleaned_data


class UpdateHostInfoAction(workflows.Action):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)

    personality = forms.ChoiceField(label=_("Personality"),
                                    choices=PERSONALITY_CHOICES,
                                    widget=forms.Select(
                                        attrs={'class': 'switchable',
                                               'data-slug': 'personality'}))

    subfunctions = forms.ChoiceField(
        label=FIELD_LABEL_PERFORMANCE_PROFILE,
        choices=PERFORMANCE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   api.sysinv.PERSONALITY_COMPUTE: _(
                       "Performance Profile")}))

    pers_subtype = forms.ChoiceField(
        label=_("Personality Sub-Type"),
        choices=api.sysinv.Host.SUBTYPE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   api.sysinv.PERSONALITY_STORAGE: _(
                       "Personality Sub-Type")}))

    hostname = forms.RegexField(label=_("Host Name"),
                                max_length=255,
                                required=False,
                                regex=r'^[\w\.\-]+$',
                                error_messages={
                                    'invalid':
                                    _('Name may only contain letters,'
                                      ' numbers, underscores, '
                                      'periods and hyphens.')},
                                widget=forms.TextInput(
                                    attrs={'class': 'switched',
                                           'data-switch-on': 'personality',
                                           'data-personality-' +
                                           api.sysinv.PERSONALITY_COMPUTE: _(
                                               "Host Name")}))

    location = forms.CharField(label=_("Location"),
                               initial='location',
                               required=False,
                               help_text=_("Physical location of Host."))

    cpuProfile = forms.ChoiceField(label=_("CPU Profile"),
                                   required=False)

    interfaceProfile = forms.ChoiceField(label=_("Interface Profile"),
                                         required=False)

    diskProfile = forms.ChoiceField(label=_("Storage Profile"),
                                    required=False)

    memoryProfile = forms.ChoiceField(label=_("Memory Profile"),
                                      required=False)

    ttys_dcd = forms.BooleanField(
        label=_("Serial Console Data Carrier Detect"),
        required=False,
        help_text=_("Enable serial line data carrier detection. "
                    "When selected, dropping carrier detect on the serial "
                    "port revoke any active session and a new login "
                    "process is initiated when a new connection is detected."))

    class Meta(object):
        name = _("Host Info")
        help_text = _(
            "From here you can update the configuration of the current host.\n"
            "Note: this will not affect the resources allocated to any"
            " existing"
            " instances using this host until the host is rebooted.")

    def __init__(self, request, *args, **kwargs):
        super(UpdateHostInfoAction, self).__init__(request, *args, **kwargs)

        # pesonality cannot be storage if ceph is not configured
        cinder_backend = api.sysinv.get_cinder_backend(request)
        if api.sysinv.CINDER_BACKEND_CEPH not in cinder_backend:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

        # All-in-one system, personality can only be controller.
        systems = api.sysinv.system_list(request)
        self.system_mode = systems[0].to_dict().get('system_mode')
        self.system_type = systems[0].to_dict().get('system_type')
        if self.system_type == constants.TS_AIO:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICE_CONTROLLER
            self.fields['personality'].widget.attrs['disabled'] = 'disabled'

        # hostname cannot be modified once it is set
        if self.initial['hostname']:
            self.fields['hostname'].widget.attrs['readonly'] = 'readonly'
            self.fields['hostname'].required = False

        # subfunctions cannot be modified once it is set
        if self.initial['subfunctions']:
            self.fields['subfunctions'].widget.attrs['disabled'] = 'disabled'
            self.fields['subfunctions'].required = False

        # personality cannot be modified once it is set
        host_id = self.initial['host_id']
        personality = self.initial['personality']

        if (api.sysinv.CINDER_BACKEND_CEPH not in api.sysinv.get_cinder_backend(request)) \
                or personality:
            self.fields['pers_subtype'].widget.attrs['disabled'] = 'disabled'
            self.fields['pers_subtype'].required = False

        mem_profile_configurable = False

        if personality and self.system_mode != constants.SYSTEM_MODE_SIMPLEX:
            self.fields['personality'].widget.attrs['disabled'] = 'disabled'
            self.fields['personality'].required = False
            self._personality = personality

            host = api.sysinv.host_get(self.request, host_id)
            host.nodes = api.sysinv.host_node_list(self.request, host.uuid)
            host.cpus = api.sysinv.host_cpu_list(self.request, host.uuid)
            host.ports = api.sysinv.host_port_list(self.request, host.uuid)
            host.disks = api.sysinv.host_disk_list(self.request, host.uuid)

            if 'compute' in host.subfunctions:
                mem_profile_configurable = True
                host.memory = api.sysinv.host_memory_list(
                    self.request, host.uuid)
            else:
                del self.fields['memoryProfile']

            if host.nodes and host.cpus and host.ports:
                # Populate Available Cpu Profile Choices
                try:
                    avail_cpu_profile_list = api.sysinv.host_cpuprofile_list(
                        self.request)

                    host_profile = icpu_utils.HostCpuProfile(
                        host.subfunctions,
                        host.cpus, host.nodes)

                    cpu_profile_tuple_list = [
                        ('', _("Copy from an available cpu profile."))]
                    for ip in avail_cpu_profile_list:
                        nodes = api.sysinv.host_node_list(self.request,
                                                          ip.uuid)
                        cpu_profile = icpu_utils.CpuProfile(ip.cpus, nodes)
                        if host_profile.profile_applicable(cpu_profile):
                            cpu_profile_tuple_list.append(
                                (ip.profilename, ip.profilename))

                except Exception:
                    exceptions.handle(self.request, _(
                        'Unable to retrieve list of cpu profiles.'))
                    cpu_profile_tuple_list = []

                self.fields['cpuProfile'].choices = cpu_profile_tuple_list

                # Populate Available Interface Profile Choices
                try:
                    avail_interface_profile_list = \
                        api.sysinv.host_interfaceprofile_list(self.request)

                    interface_profile_tuple_list = [
                        ('', _("Copy from an available interface profile."))]
                    for ip in avail_interface_profile_list:
                        if ifprofile_applicable(host, ip):
                            interface_profile_tuple_list.append(
                                (ip.profilename, ip.profilename))

                except Exception:
                    exceptions.handle(self.request, _(
                        'Unable to retrieve list of interface profiles.'))
                    interface_profile_tuple_list = []

                self.fields[
                    'interfaceProfile'].choices = interface_profile_tuple_list
            else:
                self.fields['cpuProfile'].widget = forms.widgets.HiddenInput()
                self.fields[
                    'interfaceProfile'].widget = forms.widgets.HiddenInput()

            if ((personality == 'storage' or 'compute' in host._subfunctions)
               and host.disks):
                # Populate Available Disk Profile Choices
                try:
                    disk_profile_tuple_list = [
                        ('', _("Copy from an available storage profile."))]
                    avail_disk_profile_list = \
                        api.sysinv.host_diskprofile_list(self.request)
                    for dp in avail_disk_profile_list:
                        if diskprofile_applicable(host, dp):
                            disk_profile_tuple_list.append(
                                (dp.profilename, dp.profilename))

                except Exception as e:
                    LOG.exception(e)
                    exceptions.handle(self.request, _(
                        'Unable to retrieve list of storage profiles.'))
                    disk_profile_tuple_list = []

                self.fields['diskProfile'].choices = disk_profile_tuple_list
            else:
                self.fields['diskProfile'].widget = forms.widgets.HiddenInput()

            if mem_profile_configurable and host.nodes and host.memory:
                # Populate Available Memory Profile Choices
                try:
                    avail_memory_profile_list = \
                        api.sysinv.host_memprofile_list(self.request)
                    memory_profile_tuple_list = [
                        ('', _("Copy from an available memory profile."))]
                    for mp in avail_memory_profile_list:
                        if memoryprofile_applicable(host, host._subfunctions,
                                                    mp):
                            memory_profile_tuple_list.append(
                                (mp.profilename, mp.profilename))

                except Exception:
                    exceptions.handle(self.request, _(
                        'Unable to retrieve list of memory profiles.'))
                    memory_profile_tuple_list = []

                self.fields[
                    'memoryProfile'].choices = memory_profile_tuple_list

        else:
            self.fields['cpuProfile'].widget = forms.widgets.HiddenInput()
            self.fields[
                'interfaceProfile'].widget = forms.widgets.HiddenInput()
            self.fields['diskProfile'].widget = forms.widgets.HiddenInput()
            self.fields['memoryProfile'].widget = forms.widgets.HiddenInput()

    def clean_location(self):
        try:
            host_id = self.cleaned_data['host_id']
            host = api.sysinv.host_get(self.request, host_id)
            location = host._location
            location['locn'] = self.cleaned_data.get('location')
            return location
        except Exception:
            msg = _('Unable to get host data')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

    def clean(self):
        cleaned_data = super(UpdateHostInfoAction, self).clean()
        disabled = self.fields['personality'].widget.attrs.get('disabled')
        if disabled == 'disabled':
            if self.system_type == constants.TS_AIO:
                self._personality = 'controller'
            cleaned_data['personality'] = self._personality

        if cleaned_data['personality'] == api.sysinv.PERSONALITY_STORAGE:
            self._subfunctions = api.sysinv.PERSONALITY_STORAGE
            cleaned_data['subfunctions'] = self._subfunctions
        elif cleaned_data['personality'] == api.sysinv.PERSONALITY_CONTROLLER:
            if self.system_type == constants.TS_AIO:
                self._subfunctions = (api.sysinv.PERSONALITY_CONTROLLER + ','
                                      + api.sysinv.PERSONALITY_COMPUTE)
            else:
                self._subfunctions = api.sysinv.PERSONALITY_CONTROLLER
            cleaned_data['subfunctions'] = self._subfunctions
        elif cleaned_data['personality'] == api.sysinv.PERSONALITY_COMPUTE:
            cleaned_data['pers_subtype'] = None

        return cleaned_data


class AddHostInfo(workflows.Step):
    action_class = AddHostInfoAction
    contributes = ("personality",
                   "subfunctions",
                   "hostname",
                   "mgmt_mac")


class UpdateHostInfo(workflows.Step):
    action_class = UpdateHostInfoAction
    contributes = ("host_id",
                   "personality",
                   "subfunctions",
                   "hostname",
                   "location",
                   "cpuProfile",
                   "interfaceProfile",
                   "diskProfile",
                   "memoryProfile",
                   "ttys_dcd",
                   "pers_subtype")


class UpdateInstallParamsAction(workflows.Action):
    INSTALL_OUTPUT_CHOICES = (
        (api.sysinv.INSTALL_OUTPUT_TEXT, _("text")),
        (api.sysinv.INSTALL_OUTPUT_GRAPHICAL, _("graphical")),
    )

    boot_device = forms.RegexField(label=_("Boot Device"),
                                   max_length=255,
                                   regex=r'^[^/\s]|(/dev/disk/by-path/(.+))',
                                   error_messages={
                                       'invalid':
                                       _('Device path is relative to /dev')},
                                   help_text=_("Device for boot partition."))

    rootfs_device = forms.RegexField(label=_("Rootfs Device"),
                                     max_length=255,
                                     regex=r'^[^/\s]|(/dev/disk/by-path/(.+))',
                                     error_messages={
                                         'invalid':
                                         _('Device path is relative to /dev')},
                                     help_text=_("Device for rootfs "
                                                 "partition."))

    install_output = forms.ChoiceField(label=_("Installation Output"),
                                       choices=INSTALL_OUTPUT_CHOICES,
                                       widget=forms.Select(
                                           attrs={'class': 'switchable',
                                                  'data-slug': 'install_output'
                                                  }))

    console = forms.CharField(label=_("Console"),
                              required=False,
                              help_text=_("Console configuration "
                                          "(eg. 'ttyS0,115200' or "
                                          "empty for none)."))

    class Meta(object):
        name = _("Installation Parameters")
        help_text = _(
            "From here you can update the installation parameters of"
            " the current host.")

    def __init__(self, request, *args, **kwargs):
        super(UpdateInstallParamsAction, self).__init__(request, *args,
                                                        **kwargs)

        host_id = self.initial['host_id']
        host = api.sysinv.host_get(self.request, host_id)

        self.fields['boot_device'].initial = host.boot_device
        self.fields['rootfs_device'].initial = host.rootfs_device
        self.fields['install_output'].initial = host.install_output
        self.fields['console'].initial = host.console

    def clean(self):
        cleaned_data = super(UpdateInstallParamsAction, self).clean()
        return cleaned_data


class UpdateInstallParams(workflows.Step):
    action_class = UpdateInstallParamsAction
    contributes = ("boot_device",
                   "rootfs_device",
                   "install_output",
                   "console")


class BoardManagementAction(workflows.Action):

    FIELD_LABEL_BM_IP = _("Board Management Controller IP Address")
    FIELD_LABEL_BM_USERNAME = _("Board Management Controller User Name")
    FIELD_LABEL_BM_PASSWORD = _("Board Management Controller Password")
    FIELD_LABEL_BM_CONFIRM_PASSWORD = _("Confirm Password")

    bm_type = forms.ChoiceField(
        label=_("Board Management Controller Type "),
        choices=BM_TYPES_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'bm_type'}))

    bm_ip = forms.IPField(
        label=FIELD_LABEL_BM_IP,
        required=False,
        help_text=_(
            "IP address of the Board Management Controller"
            " (e.g. 172.25.0.0)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'bm_type',
            'data-bm_type-' +
            api.sysinv.BM_TYPE_GENERIC: FIELD_LABEL_BM_IP}))

    bm_username = forms.CharField(
        label=FIELD_LABEL_BM_USERNAME,
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'class': 'switched',
            'data-switch-on': 'bm_type',
            'data-bm_type-' +
            api.sysinv.BM_TYPE_GENERIC: FIELD_LABEL_BM_USERNAME}))

    bm_password = forms.RegexField(
        label=FIELD_LABEL_BM_PASSWORD,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'bm_type',
                'data-bm_type-' +
                api.sysinv.BM_TYPE_GENERIC: FIELD_LABEL_BM_PASSWORD}),
        regex=validators.password_validator(),
        required=False,
        error_messages={'invalid': validators.password_validator_msg()})

    bm_confirm_password = forms.CharField(
        label=FIELD_LABEL_BM_CONFIRM_PASSWORD,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'bm_type',
                'data-bm_type-' +
                api.sysinv.BM_TYPE_GENERIC: FIELD_LABEL_BM_CONFIRM_PASSWORD}),
        required=False)

    def clean(self):
        cleaned_data = super(BoardManagementAction, self).clean()

        if cleaned_data.get('bm_type'):
            if 'bm_ip' not in cleaned_data or not cleaned_data['bm_ip']:
                raise forms.ValidationError(
                    _('Board management IP address is required.'))
                raise forms.ValidationError(
                    _('Board management MAC address is required.'))

            if 'bm_username' not in cleaned_data or not \
                    cleaned_data['bm_username']:
                raise forms.ValidationError(
                    _('Board management user name is required.'))

            if 'bm_password' in cleaned_data:
                if cleaned_data['bm_password'] != cleaned_data.get(
                        'bm_confirm_password', None):
                    raise forms.ValidationError(
                        _('Board management passwords do not match.'))
        else:
            cleaned_data.pop('bm_ip')
            cleaned_data.pop('bm_username')

        return cleaned_data

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        # Throw away the password confirmation, we're done with it.
        data.pop('bm_confirm_password', None)


class AddBoardManagementAction(BoardManagementAction):

    class Meta(object):
        name = _("Board Management")
        help_text = _(
            "From here you can add the"
            " configuration for the board management controller.")


class UpdateBoardManagementAction(BoardManagementAction):

    class Meta(object):
        name = _("Board Management")
        help_text = _(
            "From here you can update the"
            " configuration of the board management controller.")


class AddBoardManagement(workflows.Step):
    action_class = AddBoardManagementAction
    contributes = ("bm_type",
                   "bm_ip",
                   "bm_username",
                   "bm_password",
                   "bm_confirm_password")


class UpdateBoardManagement(workflows.Step):
    action_class = UpdateBoardManagementAction
    contributes = ("bm_type",
                   "bm_ip",
                   "bm_username",
                   "bm_password",
                   "bm_confirm_password")


class AddHost(workflows.Workflow):
    slug = "add"
    name = _("Add Host")
    finalize_button_name = _("Add Host")
    success_message = _('Added host "%s".')
    failure_message = _('Unable to add host "%s".')
    default_steps = (AddHostInfo,
                     AddBoardManagement)

    success_url = 'horizon:admin:inventory:index'
    failure_url = 'horizon:admin:inventory:index'

    hostname = None

    def format_status_message(self, message):
        name = self.hostname
        return message % name

    def handle(self, request, data):
        self.hostname = data['hostname']
        self.mgmt_mac = data['mgmt_mac']

        try:
            host = api.sysinv.host_create(request, **data)
            return True if host else False

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            return False
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class UpdateHost(workflows.Workflow):
    slug = "update"
    name = _("Edit Host")
    finalize_button_name = _("Save")
    success_message = _('Updated host "%s".')
    failure_message = _('Unable to modify host "%s".')
    default_steps = (UpdateHostInfo,
                     UpdateInstallParams,
                     UpdateBoardManagement)

    success_url = 'horizon:admin:inventory:index'
    failure_url = 'horizon:admin:inventory:index'

    hostname = None

    def format_status_message(self, message):
        name = self.hostname or self.context.get('host_id')
        return message % name

    def handle(self, request, data):
        self.hostname = data['hostname']

        try:
            host = api.sysinv.host_get(request, data['host_id'])

            if data['cpuProfile']:
                profile_uuid = profile_get_uuid(request, data['cpuProfile'])
                api.sysinv.host_apply_profile(request, data['host_id'],
                                              profile_uuid)
            data.pop('cpuProfile')

            if data['interfaceProfile']:
                profile_uuid = profile_get_uuid(request,
                                                data['interfaceProfile'])
                api.sysinv.host_apply_profile(request, data['host_id'],
                                              profile_uuid)
            data.pop('interfaceProfile')

            if not data['bm_password']:
                data.pop('bm_password')

            if data['diskProfile']:
                profile_uuid = profile_get_uuid(request, data['diskProfile'])
                api.sysinv.host_apply_profile(request, data['host_id'],
                                              profile_uuid)
            data.pop('diskProfile')

            if data['memoryProfile']:
                profile_uuid = profile_get_uuid(request, data['memoryProfile'])
                api.sysinv.host_apply_profile(request, data['host_id'],
                                              profile_uuid)
            data.pop('memoryProfile')

            # if not trying to change personality, skip check
            if host._personality == data['personality']:
                data.pop('personality')

            if data.get('rootfs_device') == host.rootfs_device:
                data.pop('rootfs_device')

            if data.get('install_output') == host.install_output:
                data.pop('install_output')

            if data.get('console') == host.console:
                data.pop('console')

            if 'pers_subtype' in data:
                if not hasattr(data, 'capabilities'):
                    data['capabilities'] = {}
                pers_subtype = data.pop('pers_subtype')
                if pers_subtype:
                    data['capabilities']['pers_subtype'] = pers_subtype

            # subfunctions cannot be modified once host is configured
            if host._subfunctions and 'subfunctions' in data:
                data.pop('subfunctions')

            host = api.sysinv.host_update(request, **data)
            return True if host else False

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            return False
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False
