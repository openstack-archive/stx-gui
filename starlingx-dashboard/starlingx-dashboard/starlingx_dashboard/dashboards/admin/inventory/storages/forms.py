#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class AddDiskProfile(forms.SelfHandlingForm):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)
    profilename = forms.CharField(label=_("Storage Profile Name"),
                                  required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddDiskProfile, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddDiskProfile, self).clean()
        # host_id = cleaned_data.get('host_id')
        return cleaned_data

    def handle(self, request, data):
        diskProfileName = data['profilename']
        try:
            diskProfile = stx_api.sysinv.host_diskprofile_create(request,
                                                                 **data)

            msg = _('Storage Profile "%s" was successfully created.') \
                % diskProfileName
            LOG.debug(msg)

            messages.success(request, msg)

            return diskProfile
        except Exception as e:
            msg = _('Failed to create storage profile "%s".') % diskProfileName
            LOG.info(msg)
            LOG.error(e)

            messages.error(request, e)

            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            return shortcuts.redirect(redirect)


class EditStorageVolume(forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.widgets.HiddenInput)

    journal_locations = forms.ChoiceField(label=_("Journal"),
                                          required=False,
                                          widget=forms.Select(attrs={
                                              'data-slug':
                                                  'journal_locations'}),
                                          help_text=_("Assign disk to journal "
                                                      "storage volume."))

    journal_size_gib = forms.CharField(
        label=_("Journal Size GiB"),
        required=False,
        initial=stx_api.sysinv.JOURNAL_DEFAULT_SIZE,
        widget=forms.TextInput(attrs={'data-slug': 'journal_size_gib'}),
        help_text=_("Journal's size for the current OSD."))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, request, *args, **kwargs):
        super(EditStorageVolume, self).__init__(request, *args, **kwargs)

        stor = stx_api.sysinv.host_stor_get(
            self.request, kwargs['initial']['uuid'])

        initial_journal_location = kwargs['initial']['journal_location']
        host_uuid = kwargs['initial']['host_uuid']

        # Populate available journal choices. If no journal is available,
        # then the journal is collocated.
        avail_journal_list = stx_api.sysinv.host_stor_get_by_function(
            self.request,
            host_uuid,
            'journal')

        journal_tuple_list = []

        if stor.uuid == initial_journal_location:
            journal_tuple_list.append((stor.uuid, "Collocated with OSD"))
        else:
            journal_tuple_list.append((initial_journal_location,
                                       "%s " % initial_journal_location))

        if avail_journal_list:
            for j in avail_journal_list:
                if j.uuid != initial_journal_location:
                    journal_tuple_list.append((j.uuid, "%s " % j.uuid))

        if stor.uuid != initial_journal_location:
            journal_tuple_list.append((stor.uuid, "Collocated with OSD"))

        self.fields['journal_locations'].choices = journal_tuple_list

    def handle(self, request, data):
        stor_id = data['id']

        try:
            # Obtain journal information.
            journal = data['journal_locations'][:]

            if journal:
                data['journal_location'] = journal
            else:
                data['journal_location'] = None
                data['journal_size_mib'] = \
                    stx_api.sysinv.JOURNAL_DEFAULT_SIZE * 1024

            del data['journal_locations']
            del data['id']
            del data['journal_size_gib']

            # The REST API takes care of updating the stor journal information.
            stor = stx_api.sysinv.host_stor_update(request, stor_id, **data)

            msg = _('Storage volume was successfully updated.')
            LOG.debug(msg)
            messages.success(request, msg)

            return stor
        except exc.ClientException as ce:
            msg = _('Failed to update storage volume.')
            LOG.info(msg)
            LOG.error(ce)

            # Allow REST API error message to appear on UI.
            messages.error(request, ce)

            # Redirect to host details pg.
            redirect = reverse(self.failure_url, args=[stor_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to update storage volume.')
            LOG.info(msg)
            LOG.error(e)

            # if not a rest API error, throw default
            redirect = reverse(self.failure_url, args=[stor_id])
            return exceptions.handle(request, message=e, redirect=redirect)


class AddStorageVolume(forms.SelfHandlingForm):
    # Only allowed to choose 'osd'
    FUNCTION_CHOICES = (
        ('osd', _("osd")),
        ('journal', _("journal")),
        # ('monitor', _("monitor")),
    )

    host_id = forms.CharField(label=_("host_id"),
                              initial='host_id',
                              widget=forms.widgets.HiddenInput)

    ihost_uuid = forms.CharField(label=_("ihost_uuid"),
                                 initial='ihost_uuid',
                                 widget=forms.widgets.HiddenInput)

    idisk_uuid = forms.CharField(label=_("idisk_uuid"),
                                 initial='idisk_uuid',
                                 widget=forms.widgets.HiddenInput)

    tier_uuid = forms.CharField(label=_("tier_uuid"),
                                initial='tier_uuid',
                                widget=forms.widgets.HiddenInput)

    hostname = forms.CharField(label=_("Hostname"),
                               initial='hostname',
                               widget=forms.TextInput(attrs={
                                   'readonly': 'readonly'}))

    function = forms.ChoiceField(label=_("Function"),
                                 required=False,
                                 choices=FUNCTION_CHOICES,
                                 widget=forms.Select(attrs={
                                     'class': 'switchable',
                                     'data-slug': 'function'}))

    disks = forms.ChoiceField(label=_("Disks"),
                              required=True,
                              widget=forms.Select(attrs={
                                  'class': 'switchable',
                                  'data-slug': 'disk'}),
                              help_text=_("Assign disk to a storage volume."))

    journal_locations = forms.ChoiceField(label=_("Journal"),
                                          required=False,
                                          widget=forms.Select(attrs={
                                              'class': 'switched',
                                              'data-switch-on': 'function',
                                              'data-function-osd': _(
                                                  "Journal")}),
                                          help_text=_("Assign disk to a "
                                                      "journal storage "
                                                      "volume."))

    journal_size_gib = forms.CharField(
        label=_("Journal Size GiB"),
        required=False,
        initial=stx_api.sysinv.JOURNAL_DEFAULT_SIZE,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'function',
            'data-function-osd': _("Journal Size GiB")}),
        help_text=_("Journal's size for the current OSD."))

    tiers = forms.ChoiceField(label=_("Storage Tier"),
                              required=False,
                              widget=forms.Select(attrs={
                                  'class': 'switched',
                                  'data-switch-on': 'function',
                                  'data-function-osd':
                                  _("Storage Tier")}),
                              help_text=_("Assign OSD to a storage tier."))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddStorageVolume, self).__init__(*args, **kwargs)

        # Populate available disk choices
        this_stor_uuid = 0
        host_uuid = kwargs['initial']['ihost_uuid']

        avail_disk_list = stx_api.sysinv.host_disk_list(self.request,
                                                        host_uuid)
        disk_tuple_list = []
        for d in avail_disk_list:
            if d.istor_uuid and d.istor_uuid != this_stor_uuid:
                continue
            is_rootfs_device = \
                (('stor_function' in d.capabilities) and
                 (d.capabilities['stor_function'] == 'rootfs'))
            if is_rootfs_device:
                continue
            disk_model = d.get_model_num()
            if disk_model is not None and "floppy" in disk_model.lower():
                continue
            disk_tuple_list.append(
                (d.uuid, "%s (path: %s size:%s model:%s type: %s)" % (
                    d.device_node,
                    d.device_path,
                    str(d.size_gib),
                    disk_model,
                    d.device_type)))

        # Get the cluster
        cluster_list = stx_api.sysinv.cluster_list(self.request)
        cluster_uuid = cluster_list[0].uuid

        # Populate the available tiers for OSD assignment
        avail_tier_list = stx_api.sysinv.storage_tier_list(self.request,
                                                           cluster_uuid)
        tier_tuple_list = [(t.uuid, t.name) for t in avail_tier_list]

        # Populate available journal choices. If no journal is available,
        # then the journal is collocated.
        avail_journal_list = stx_api.sysinv.host_stor_get_by_function(
            self.request, host_uuid, 'journal')

        journal_tuple_list = []
        if avail_journal_list:
            for j in avail_journal_list:
                journal_tuple_list.append((j.uuid, "%s " % j.uuid))
        else:
            journal_tuple_list.append((None, "Collocated with OSD"))
            self.fields['journal_size_gib'].widget.attrs['disabled'] = \
                'disabled'

        self.fields['disks'].choices = disk_tuple_list
        self.fields['journal_locations'].choices = journal_tuple_list
        self.fields['tiers'].choices = tier_tuple_list

    def clean(self):
        cleaned_data = super(AddStorageVolume, self).clean()
        # host_id = cleaned_data.get('host_id')
        # ihost_uuid = cleaned_data.get('ihost_uuid')

        # disks = cleaned_data.get('disks')

        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']
        # host_uuid = data['ihost_uuid']
        disks = data['disks'][:]  # copy
        tiers = data['tiers'][:]  # copy

        # GUI only allows one disk to be picked
        data['idisk_uuid'] = disks

        # GUI only allows one tier to be picked
        data['tier_uuid'] = tiers

        # Obtain journal information.
        journal = data['journal_locations'][:]

        if journal:
            data['journal_location'] = journal
        else:
            data['journal_location'] = None
            data['journal_size_mib'] = \
                stx_api.sysinv.JOURNAL_DEFAULT_SIZE * 1024

        try:
            del data['host_id']
            del data['disks']
            del data['tiers']
            del data['hostname']
            del data['journal_locations']
            del data['journal_size_gib']

            # The REST API takes care of creating the stor
            # and updating disk.foristorid
            stor = stx_api.sysinv.host_stor_create(request, **data)

            msg = _('Storage volume was successfully created.')
            LOG.debug(msg)
            messages.success(request, msg)

            return stor
        except exc.ClientException as ce:
            msg = _('Failed to create storage volume.')
            LOG.info(msg)
            LOG.error(ce)

            # Allow REST API error message to appear on UI
            messages.error(request, ce)

            # Redirect to host details pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to create storage volume.')
            LOG.info(msg)
            LOG.error(e)

            # if not a rest API error, throw default
            redirect = reverse(self.failure_url, args=[host_id])
            return exceptions.handle(request, message=e, redirect=redirect)


class AddLocalVolumeGroup(forms.SelfHandlingForm):

    host_id = forms.CharField(label=_("host_id"),
                              initial='host_id',
                              widget=forms.widgets.HiddenInput)

    ihost_uuid = forms.CharField(label=_("ihost_uuid"),
                                 initial='ihost_uuid',
                                 widget=forms.widgets.HiddenInput)

    hostname = forms.CharField(label=_("Hostname"),
                               initial='hostname',
                               widget=forms.TextInput(attrs={
                                   'readonly': 'readonly'}))

    lvm_vg_name = forms.ChoiceField(label=_("Local Volume Group Name"),
                                    required=True,
                                    widget=forms.Select(attrs={
                                        'class': 'switchable',
                                        'data-slug': 'lvm_vg_name'}))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddLocalVolumeGroup, self).__init__(*args, **kwargs)

        # Populate available volume group choices
        host_uuid = kwargs['initial']['ihost_uuid']
        host_id = kwargs['initial']['host_id']

        host = stx_api.sysinv.host_get(self.request, host_id)
        subfunctions = host.subfunctions

        # LVGs that are considered as "present" in the system are those
        # in an adding or provisioned state.
        ilvg_list = stx_api.sysinv.host_lvg_list(self.request, host_uuid)
        current_lvg_states = [stx_api.sysinv.LVG_ADD, stx_api.sysinv.LVG_PROV]
        current_lvgs = [lvg.lvm_vg_name for lvg in ilvg_list
                        if lvg.vg_state in current_lvg_states]

        compatible_lvgs = []
        if host.personality.lower().startswith(
                stx_api.sysinv.PERSONALITY_CONTROLLER):
            compatible_lvgs += [stx_api.sysinv.LVG_CINDER_VOLUMES]

        if stx_api.sysinv.SUBFUNCTIONS_WORKER in subfunctions:
            compatible_lvgs += [stx_api.sysinv.LVG_NOVA_LOCAL]

        allowed_lvgs = set(compatible_lvgs) - set(current_lvgs)

        ilvg_tuple_list = []
        for lvg in allowed_lvgs:
            ilvg_tuple_list.append((lvg, lvg))

        self.fields['lvm_vg_name'].choices = ilvg_tuple_list

    def clean(self):
        cleaned_data = super(AddLocalVolumeGroup, self).clean()
        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']

        try:
            del data['host_id']
            del data['hostname']

            # The REST API takes care of creating the stor
            # and updating disk.foristorid
            lvg = stx_api.sysinv.host_lvg_create(request, **data)

            msg = _('Local volume group was successfully created.')
            LOG.debug(msg)
            messages.success(request, msg)

            return lvg
        except exc.ClientException as ce:
            msg = _('Failed to create local volume group.')
            LOG.info(msg)
            LOG.error(ce)

            # Allow REST API error message to appear on UI
            w_msg = str(ce)
            if ('Warning' in w_msg):
                LOG.info(ce)
                messages.warning(request, w_msg.split(':', 1)[-1])
            else:
                LOG.error(ce)
                messages.error(request, w_msg)

            # Redirect to host details pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to create local volume group.')
            LOG.info(msg)
            LOG.error(e)

            # if not a rest API error, throw default
            redirect = reverse(self.failure_url, args=[host_id])
            return exceptions.handle(request, message=e, redirect=redirect)


class AddPhysicalVolume(forms.SelfHandlingForm):

    PV_TYPE_CHOICES = (
        ('disk', _("Disk")),
        ('partition', _("Partition")),
    )

    host_id = forms.CharField(label=_("host_id"),
                              initial='host_id',
                              widget=forms.widgets.HiddenInput)

    ihost_uuid = forms.CharField(label=_("ihost_uuid"),
                                 initial='ihost_uuid',
                                 widget=forms.widgets.HiddenInput)

    disk_or_part_uuid = forms.CharField(label=_("disk_or_part_uuid"),
                                        initial='disk_or_part_uuid',
                                        widget=forms.widgets.HiddenInput)

    hostname = forms.CharField(label=_("Hostname"),
                               initial='hostname',
                               widget=forms.TextInput(attrs={
                                   'readonly': 'readonly'}))

    lvg = forms.ChoiceField(label=_("Local Volume Group"),
                            required=True,
                            widget=forms.Select(attrs={
                                'class': 'switchable',
                                'data-slug': 'lvg'}),
                            help_text=_("Associate this physical volume to a "
                                        "volume group "))

    pv_type = forms.ChoiceField(label=_("PV Type"),
                                required=False,
                                choices=PV_TYPE_CHOICES,
                                widget=forms.Select(attrs={
                                    'class': 'switchable',
                                    'data-slug': 'pv_type',
                                    'initial': 'Disk'}))

    disks = forms.ChoiceField(label=_("Disks"),
                              required=False,
                              widget=forms.Select(attrs={
                                  'class': 'switched',
                                  'data-switch-on': 'pv_type',
                                  'data-pv_type-disk': _("Disks")}),
                              help_text=_("Assign disk to physical volume."))

    partitions = forms.ChoiceField(label=_("Partitions"),
                                   required=False,
                                   widget=forms.Select(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'pv_type',
                                       'data-pv_type-partition':
                                       _("Partitions")}),
                                   help_text=_("Assign partition to physical "
                                   "volume."))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddPhysicalVolume, self).__init__(*args, **kwargs)

        # Populate available partition, disk, and volume group choices
        host_uuid = kwargs['initial']['ihost_uuid']
        host_id = kwargs['initial']['host_id']

        host = stx_api.sysinv.host_get(self.request, host_id)
        subfunctions = host.subfunctions

        compatible_lvgs = []
        if host.personality.lower().startswith(
                stx_api.sysinv.PERSONALITY_CONTROLLER):
            compatible_lvgs += [stx_api.sysinv.LVG_CGTS_VG,
                                stx_api.sysinv.LVG_CINDER_VOLUMES]

        if stx_api.sysinv.SUBFUNCTIONS_WORKER in subfunctions:
            compatible_lvgs += [stx_api.sysinv.LVG_NOVA_LOCAL]

        avail_disk_list = stx_api.sysinv.host_disk_list(self.request,
                                                        host_uuid)
        ilvg_list = stx_api.sysinv.host_lvg_list(self.request, host_uuid)
        partitions = stx_api.sysinv.host_disk_partition_list(self.request,
                                                             host_uuid)
        ipv_list = stx_api.sysinv.host_pv_list(self.request, host_uuid)
        disk_tuple_list = []
        partitions_tuple_list = []
        ilvg_tuple_list = []

        pv_cinder_volumes = next(
            (pv for pv in ipv_list
             if pv.lvm_vg_name == stx_api.sysinv.LVG_CINDER_VOLUMES), None)

        for lvg in ilvg_list:
            if (lvg.lvm_vg_name in compatible_lvgs and
                    lvg.vg_state in [stx_api.sysinv.LVG_ADD,
                                     stx_api.sysinv.LVG_PROV]):
                if (lvg.lvm_vg_name == stx_api.sysinv.LVG_CINDER_VOLUMES and
                        pv_cinder_volumes):
                    continue
                ilvg_tuple_list.append((lvg.uuid, lvg.lvm_vg_name))

        for disk in avail_disk_list:
            capabilities = disk.capabilities

            if capabilities.get('stor_function') == 'rootfs':
                continue
            # TODO(rchurch): re-factor
            elif capabilities.get('device_function') == 'cinder_device':
                continue
            else:
                break

        for d in avail_disk_list:
            disk_cap = d.capabilities
            # TODO(rchurch): re-factor
            is_cinder_device = \
                (('device_function' in disk_cap) and
                 (disk_cap['device_function'] == 'cinder_device'))

            is_rootfs_device = \
                (('stor_function' in disk_cap) and
                 (disk_cap['stor_function'] == 'rootfs'))

            disk_model = d.get_model_num()
            # TODO(rchurch): re-factor
            if not d.ipv_uuid and is_cinder_device:
                continue

            if is_rootfs_device or d.ipv_uuid:
                continue

            if disk_model is not None and "floppy" in disk_model.lower():
                continue

            disk_tuple_list.append(
                (d.uuid, "%s (path:%s size:%s model:%s)" % (
                    d.device_node,
                    d.device_path,
                    str(d.size_gib),
                    disk_model)))

        for p in partitions:
            if p.type_guid != stx_api.sysinv.USER_PARTITION_PHYS_VOL:
                continue
            if p.ipv_uuid:
                continue
            if p.status == stx_api.sysinv.PARTITION_IN_USE_STATUS:
                # If partition is in use, but the PV it is attached to
                # is in a "removing" state, we should allow the partition
                # to be listed as a possible option.
                for pv in ipv_list:
                    if (pv.disk_or_part_device_path == p.device_path and
                            pv.pv_state == stx_api.sysinv.PV_DEL):
                        break
                else:
                    continue

            partitions_tuple_list.append(
                (p.uuid, "%s (size:%s)" % (
                    p.device_path,
                    str(p.size_mib))))

        self.fields['disks'].choices = disk_tuple_list
        self.fields['lvg'].choices = ilvg_tuple_list
        self.fields['partitions'].choices = partitions_tuple_list

    def clean(self):
        cleaned_data = super(AddPhysicalVolume, self).clean()
        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']

        lvgs = data['lvg'][:]

        # GUI only allows one disk to be picked
        if data['pv_type'] == 'disk':
            data['disk_or_part_uuid'] = data['disks'][:]
        else:
            data['disk_or_part_uuid'] = data['partitions'][:]

        data['ilvg_uuid'] = lvgs

        try:
            del data['host_id']
            del data['disks']
            del data['hostname']
            del data['lvg']
            del data['partitions']

            stor = stx_api.sysinv.host_pv_create(request, **data)

            msg = _('Physical volume was successfully created.')
            messages.success(request, msg)
            return stor
        except exc.ClientException as ce:
            msg = _('Failed to create physical volume.')

            # Allow REST API error message to appear on UI
            w_msg = str(ce)
            if ('Warning:' in w_msg):
                LOG.info(ce)
                messages.warning(request, w_msg.split(':', 1)[-1])
            else:
                LOG.error(ce)
                messages.error(request, w_msg)

            # Redirect to host details pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to create physical volume.')
            LOG.error(e)

            # if not a rest API error, throw default
            redirect = reverse(self.failure_url, args=[host_id])
            return exceptions.handle(request, message=e, redirect=redirect)


class EditPartition(forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.widgets.HiddenInput)

    size_gib = forms.IntegerField(label=_("Partition Size GiB"),
                                  required=False,
                                  initial='size_gib',
                                  widget=forms.TextInput(attrs={
                                      'data-slug': 'size_gib'}),
                                  help_text=_(
                                      "New partition size. Has to be "
                                      "larger than current size."))

    def __init__(self, request, *args, **kwargs):
        super(EditPartition, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        partition_id = data['id']
        data['size_mib'] = data['size_gib'] * 1024

        try:
            del data['id']
            del data['size_gib']
            # The REST API takes care of updating the partition information.
            partition = stx_api.sysinv.host_disk_partition_update(
                request, partition_id, **data)

            msg = _('Partition was successfully updated.')
            LOG.debug(msg)
            messages.success(request, msg)

            return partition
        except exc.ClientException as ce:
            msg = _('Failed to update partition.')
            LOG.info(msg)
            LOG.error(ce)

            # No redirect, return to previous storage tab view.
            # The REST API error message will appear on UI as
            # "horizon.exceptions.handle" will invoke "messages.error".
            return exceptions.handle(request, message=ce)
        except Exception as e:
            msg = _('Failed to update partition.')
            LOG.info(msg)
            LOG.error(e)

            # If not a rest API error, throw default.
            # No redirect, return to previous storage tab view.
            return exceptions.handle(request, message=e)


class CreatePartition(forms.SelfHandlingForm):
    host_id = forms.CharField(label=_("host_id"),
                              initial='host_id',
                              widget=forms.widgets.HiddenInput)

    ihost_uuid = forms.CharField(label=_("ihost_uuid"),
                                 initial='ihost_uuid',
                                 widget=forms.widgets.HiddenInput)

    idisk_uuid = forms.CharField(label=_("idisk_uuid"),
                                 initial='idisk_uuid',
                                 widget=forms.widgets.HiddenInput)

    hostname = forms.CharField(label=_("Hostname"),
                               initial='hostname',
                               widget=forms.TextInput(attrs={
                                   'readonly': 'readonly'}))

    disks = forms.ChoiceField(label=_("Disks"),
                              required=True,
                              widget=forms.Select(attrs={
                                  'class': 'switchable',
                                  'data-slug': 'disk'}),
                              help_text=_("Disk to create partition on."))

    size_gib = forms.IntegerField(label=_("Partition Size GiB"),
                                  required=True,
                                  initial=1,
                                  widget=forms.TextInput(attrs={
                                      'data-slug': 'size_gib'}),
                                  help_text=_("Size in GiB for the new "
                                              "partition."))

    type_guid = forms.CharField(label=_("Partition Type"),
                                initial='LVM Physical Volume',
                                widget=forms.TextInput(attrs={
                                    'readonly': 'readonly'}))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(CreatePartition, self).__init__(*args, **kwargs)

        # Populate disk choices.
        host_uuid = kwargs['initial']['ihost_uuid']
        avail_disk_list = stx_api.sysinv.host_disk_list(self.request,
                                                        host_uuid)
        disk_tuple_list = []
        for d in avail_disk_list:
            disk_model = d.get_model_num()
            if disk_model is not None and "floppy" in disk_model.lower():
                continue
            if d.available_mib == 0:
                continue
            disk_tuple_list.append(
                (d.uuid, "%s (path: %s size:%s available_gib:%s type: %s)" % (
                    d.device_node,
                    d.device_path,
                    str(d.size_gib),
                    str(d.available_gib),
                    d.device_type)))

        self.fields['disks'].choices = disk_tuple_list

    def clean(self):
        cleaned_data = super(CreatePartition, self).clean()
        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']
        disks = data['disks'][:]
        data['idisk_uuid'] = disks
        data['size_mib'] = data['size_gib'] * 1024

        try:
            del data['host_id']
            del data['disks']
            del data['hostname']
            del data['size_gib']
            data['type_guid'] = stx_api.sysinv.USER_PARTITION_PHYS_VOL
            # The REST API takes care of creating the partition.
            partition = stx_api.sysinv.host_disk_partition_create(request,
                                                                  **data)

            msg = _('Partition was successfully created.')
            LOG.debug(msg)
            messages.success(request, msg)

            return partition
        except exc.ClientException as ce:
            msg = _('Failed to create partition.')
            LOG.info(msg)
            LOG.error(ce)

            # Allow REST API error message to appear on UI
            messages.error(request, ce)

            # Redirect to host details pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to create partition.')
            LOG.info(msg)
            LOG.error(e)

            # If not a REST API error, throw default.
            redirect = reverse(self.failure_url, args=[host_id])
            return exceptions.handle(request, message=e, redirect=redirect)
