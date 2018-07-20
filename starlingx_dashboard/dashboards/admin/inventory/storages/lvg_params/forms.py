# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2015-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.core import validators  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api
from oslo_serialization import jsonutils

from openstack_dashboard.api import sysinv

LOG = logging.getLogger(__name__)

NOVA_PARAMS_FIELD_MAP = {
    sysinv.LVG_NOVA_PARAM_BACKING:
    sysinv.LVG_NOVA_PARAM_BACKING,
    sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB:
    sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB,
    sysinv.LVG_NOVA_PARAM_DISK_OPS:
    sysinv.LVG_NOVA_PARAM_DISK_OPS,
}

CINDER_PARAMS_FIELD_MAP = {
    sysinv.LVG_CINDER_PARAM_LVM_TYPE:
    sysinv.LVG_CINDER_PARAM_LVM_TYPE,
}

NOVA_PARAMS_KEY_MAP = (
    (sysinv.LVG_NOVA_PARAM_BACKING,
     _("Instance Backing")),
    (sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB,
     _("Instances LV Size [in MiB]")),
    (sysinv.LVG_NOVA_PARAM_DISK_OPS,
     _("Concurrent Disk Operations")),
)

CINDER_PARAMS_KEY_MAP = (
    (sysinv.LVG_CINDER_PARAM_LVM_TYPE,
     _("LVM Provisioning Type")),
)

PARAMS_HELP = {
    sysinv.LVG_NOVA_PARAM_BACKING:
    'Determines the format and location of instance disks. Local CoW image \
    file backed, local RAW LVM logical volume backed, or remote RAW Ceph \
    storage backed',
    sysinv.LVG_NOVA_PARAM_DISK_OPS:
    'Number of parallel disk I/O intensive operations (glance image downloads, \
    image format conversions, etc.).',
    sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB:
    'An integer specifying the size (in MiB) of the instances logical volume. \
    (.e.g. 10 GiB = 10240). Volume is created from nova-local and will be \
    mounted at /etc/nova/instances.',
    sysinv.LVG_CINDER_PARAM_LVM_TYPE:
    'Cinder configuration setting which determines how the volume group is \
    provisioned. Thick provisioning will be used if the value is set to: \
    default. Thin provisioning will be used in the value is set to: thin',
}

NOVA_PARAMS_KEY_NAMES = dict(NOVA_PARAMS_KEY_MAP)

NOVA_PARAMS_CHOICES = NOVA_PARAMS_KEY_MAP

CINDER_PARAMS_KEY_NAMES = dict(CINDER_PARAMS_KEY_MAP)

CINDER_PARAMS_CHOICES = CINDER_PARAMS_KEY_MAP

BACKING_CHOICES = (
    (sysinv.LVG_NOVA_BACKING_LVM, _("Local RAW LVM backed")),
    (sysinv.LVG_NOVA_BACKING_IMAGE, _("Local CoW image backed")),
    (sysinv.LVG_NOVA_BACKING_REMOTE, _("Remote RAW Ceph storage backed")),
)

LVM_TYPE_CHOICES = (
    (sysinv.LVG_CINDER_LVM_TYPE_THICK, _("Thick Provisioning (default)")),
    (sysinv.LVG_CINDER_LVM_TYPE_THIN, _("Thin Provisioning (thin)")),
)


def get_param_key_name(key):
    name = NOVA_PARAMS_KEY_NAMES.get(key, None)
    if not name:
        name = CINDER_PARAMS_KEY_NAMES.get(key, None)
    return name


class ParamMixin(object):

    def _host_lvg_get(self, lvg_id):
        try:
            return api.sysinv.host_lvg_get(self.request, lvg_id)
        except Exception:
            exceptions.handle(
                self.request,
                _("Unable to retrieve local volume group data. "
                  "lvg=%s") % str(lvg_id))

    def _host_pv_list(self, host_id):
        try:
            return api.sysinv.host_pv_list(self.request, host_id)
        except Exception:
            exceptions.handle(
                self.request,
                _("Unable to retrieve physical volume list. "
                  "host=%s") % str(host_id))

    def _host_pv_disk_get(self, pv):
        try:
            return api.sysinv.host_disk_get(self.request, pv.disk_or_part_uuid)
        except Exception:
            exceptions.handle(
                self.request,
                _("Unable to retrieve disk %(disk)s for PV %(pv)s.") % {
                    'disk': pv.disk_or_part_uuid,
                    'pv': pv.uuid})

    def get_lvg_lvm_info(self, lvg_id):
        lvg = self._host_lvg_get(lvg_id)
        caps = lvg.capabilities
        info = {'lvg': lvg}
        if caps.get(sysinv.LVG_NOVA_PARAM_BACKING) != \
           sysinv.LVG_NOVA_BACKING_LVM:
            return info
        info['total'] = 0
        for pv in self._host_pv_list(info['lvg'].ihost_uuid):
            if pv.lvm_vg_name != lvg.lvm_vg_name:
                continue
            if pv.pv_state == sysinv.PV_DEL:
                continue
            disk = self._host_pv_disk_get(pv)
            if not disk:
                exceptions.handle(
                    self.request,
                    _("PV %s does not have an associated "
                      "disk.") % pv.uuid)
            disk_caps = disk.capabilities
            if 'pv_dev' in disk_caps:
                if 'pv_size_mib' in disk_caps:
                    info['total'] += disk_caps['pv_size_mib']
                else:
                    exceptions.handle(
                        self.request,
                        _("PV partition %s does not have a "
                          "recorded size.") % disk_caps['pv_dev'])
            else:
                info['total'] += disk.size_mib
        info['used'] = caps[sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB]
        info['free'] = info['total'] - info['used']

        # Limit the allowed size to provide a usable configuration when
        # provisioned. This is the same range that is enforced in sysinv:
        # sysinv/api/controllers/v1/ipv.py:_instances_lv_min_allowed_mib().
        # Here we calculate the values to display to the end user so that they
        # know the acceptable range to use.

        # The following comment below is from sysinv to provide context:
        #
        # 80GB is the cutoff in the kickstart files for a virtualbox disk vs. a
        # normal disk. Use a similar cutoff here for the volume group size. If
        # the volume group is large enough then bump the min_mib value. The
        # min_mib value is set to provide a reasonable minimum amount of space
        # for /etc/nova/instances
        if info['total'] < (80 * 1024):
            info['allowed_min'] = 2 * 1024
        else:
            info['allowed_min'] = 5 * 1024
        info['allowed_max'] = info['total'] >> 1
        return info


class ParamForm(ParamMixin, forms.SelfHandlingForm):
    type = forms.ChoiceField(
        label=_("Parameters"),
        required=True,
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'type'}))

    lvg_id = forms.CharField(widget=forms.widgets.HiddenInput)
    failure_url = 'horizon:admin:inventory:localvolumegroupdetail'

    def __init__(self, *args, **kwargs):
        super(ParamForm, self).__init__(*args, **kwargs)
        self._lvg = self.get_lvg_lvm_info(kwargs['initial']['lvg_id'])
        caps = self._lvg['lvg'].capabilities

        if self._lvg['lvg'].lvm_vg_name == sysinv.LVG_NOVA_LOCAL:
            self.fields[sysinv.LVG_NOVA_PARAM_BACKING] = forms.ChoiceField(
                label=_("Instance Backing"),
                initial=caps.get(sysinv.LVG_NOVA_PARAM_BACKING),
                required=True,
                choices=BACKING_CHOICES,
                help_text=(_("%s") %
                           PARAMS_HELP.get(sysinv.LVG_NOVA_PARAM_BACKING,
                                           None)),
                widget=forms.Select(attrs={
                    'class': 'switched',
                    'data-switch-on': 'type',
                    'data-type-instance_backing': ''}))

            self.fields[sysinv.LVG_NOVA_PARAM_DISK_OPS] = forms.IntegerField(
                label=_("Concurrent Disk Operations"),
                initial=caps.get(sysinv.LVG_NOVA_PARAM_DISK_OPS),
                required=True,
                help_text=(_("%s") %
                           PARAMS_HELP.get(sysinv.LVG_NOVA_PARAM_DISK_OPS,
                                           None)),
                widget=forms.TextInput(attrs={
                    'class': 'switched',
                    'data-switch-on': 'type',
                    'data-type-concurrent_disk_operations': ''}))

            if caps.get(sysinv.LVG_NOVA_PARAM_BACKING) == \
               sysinv.LVG_NOVA_BACKING_LVM:
                inst_size_mib = sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB
                self.fields[inst_size_mib] = \
                    forms.IntegerField(
                        label=_("Instances Logical Volume Size"),
                        initial=caps.get(inst_size_mib),
                        required=True,
                        help_text=(_("%s") %
                                   PARAMS_HELP.get(inst_size_mib, None)),
                        widget=forms.TextInput(attrs={
                            'class': 'switched',
                            'data-switch-on': 'type',
                            'data-type-instances_lv_size_mib': ''}))

        elif self._lvg['lvg'].lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
            self.fields[sysinv.LVG_CINDER_PARAM_LVM_TYPE] = forms.ChoiceField(
                label=_("LVM Provisioning Type"),
                initial=caps.get(sysinv.LVG_CINDER_PARAM_LVM_TYPE),
                required=True,
                choices=LVM_TYPE_CHOICES,
                help_text=(_("%s") %
                           PARAMS_HELP.get(sysinv.LVG_CINDER_PARAM_LVM_TYPE,
                                           None)),
                widget=forms.Select(attrs={
                    'class': 'switched',
                    'data-switch-on': 'type',
                    'data-type-lvm_type': ''}))

    def clean(self):
        cleaned_data = super(ParamForm, self).clean()
        key = cleaned_data.get('type', None)
        if self._lvg['lvg'].lvm_vg_name == sysinv.LVG_NOVA_LOCAL:
            field = NOVA_PARAMS_FIELD_MAP.get(key, None)
        elif self._lvg['lvg'].lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
            field = CINDER_PARAMS_FIELD_MAP.get(key, None)

        if field is not None:
            value = cleaned_data.get(field)

        cleaned_data['key'] = key
        cleaned_data['value'] = value

        return cleaned_data

    def _clean_required_value(self, key, field):
        """Validate required fields for a specific key type."""
        keytype = self.cleaned_data.get('type', None)
        if keytype == key:
            value = self.cleaned_data.get(field, None)
            if value in validators.EMPTY_VALUES:
                raise forms.ValidationError(_('This field is required.'))
            return value

    def clean_instances_lv_size_mib(self):
        data = self.cleaned_data[sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB]
        if self.cleaned_data[sysinv.LVG_NOVA_PARAM_BACKING] == sysinv.LVG_NOVA_BACKING_LVM \
           and 'allowed_min' in self._lvg:
            validators.MinValueValidator(self._lvg['allowed_min'])(
                data)
            validators.MaxValueValidator(self._lvg['allowed_max'])(
                data)
        return data

    def get_context_data(self, **kwargs):
        context = super(EditParam, self).get_context_data(**kwargs)
        context.update(self._lvg)
        return context


class EditParam(ParamForm):
    def __init__(self, *args, **kwargs):
        super(EditParam, self).__init__(*args, **kwargs)

        # cannot change the type/key during edit
        self.fields['type'].widget.attrs['readonly'] = True

        key = self.initial['key']
        value = self.initial['value']

        # ensure checkboxes receive a boolean value as the initial value
        # so that they don't get an override value attribute
        if isinstance(value, basestring) and value.lower() == 'false':
            value = False
        elif isinstance(value, basestring) and value.lower() == 'true':
            value = True

        # setup initial values for the fields based on the defined key/value
        if self._lvg['lvg'].lvm_vg_name == sysinv.LVG_NOVA_LOCAL:
            field = NOVA_PARAMS_FIELD_MAP.get(key, None)
            param_choices = NOVA_PARAMS_CHOICES
        elif self._lvg['lvg'].lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
            field = CINDER_PARAMS_FIELD_MAP.get(key, None)
            param_choices = CINDER_PARAMS_CHOICES

        if field is not None:
            self.initial['type'] = key
            self.initial[field] = value

        # instances_lv_size_mib only valid for lvm backing
        if self._lvg['lvg'].capabilities.get(sysinv.LVG_NOVA_PARAM_BACKING) \
           == sysinv.LVG_NOVA_BACKING_IMAGE:
            self.fields['type'].choices = \
                [(k, v) for k, v in param_choices
                 if k != sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB]
        else:
            self.fields['type'].choices = [(k, v) for k, v in param_choices]

    def handle(self, request, data):
        lvg_id = data['lvg_id']
        try:
            if isinstance(data['value'], bool):
                value = str(data['value'])
                data['value'] = value
            metadata = {data['key']: data['value']}

            patch = []
            patch.append({'path': '/capabilities',
                          'value': jsonutils.dumps(metadata),
                          'op': 'replace'})

            api.sysinv.host_lvg_update(request, lvg_id, patch)
            msg = _('Updated parameter "%s".') % data['key']
            messages.success(request, msg)
            return True
        except Exception as e:
            msg = _('Unable to edit parameter "{0}".'
                    ' Details: {1}').format(data['key'], e)
            redirect = reverse(self.failure_url, args=[lvg_id])
            exceptions.handle(request, msg, redirect=redirect)
