#
# Copyright (c) 2013-2015, 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging
import re

from django.core.urlresolvers import reverse  # noqa
from django import template
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from starlingx_dashboard.api import sysinv

LOG = logging.getLogger(__name__)


class CreateStorageVolume(tables.LinkAction):
    name = "createstoragevolume"
    verbose_name = ("Assign Storage Function")
    url = "horizon:admin:inventory:addstoragevolume"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        is_system_k8s_aio = sysinv.is_system_k8s_aio(request)
        host = self.table.kwargs['host']
        self.verbose_name = _("Assign Storage Function")

        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        if host._personality != 'storage' and not is_system_k8s_aio:
            return False

        if host._administrative == 'unlocked':
            if 'storage' in host._subfunctions or is_system_k8s_aio:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Node Unlocked)"))

        return True


class CreateDiskProfile(tables.LinkAction):
    name = "creatediskprofile"
    verbose_name = ("Create Storage Profile")
    url = "horizon:admin:inventory:adddiskprofile"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        return not sysinv.is_system_mode_simplex(request)


class CreatePartition(tables.LinkAction):
    name = "createpartition"
    verbose_name = ("Create a new partition")
    url = "horizon:admin:inventory:createpartition"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        self.verbose_name = _("Create a new partition")

        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        if host._personality != 'storage':
            return True

        return True


class DeletePartition(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Partition",
            "Delete Partitions",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Partition",
            "Deleted Partitions",
            count
        )

    def allowed(self, request, partition=None):
        host = self.table.kwargs['host']
        PARTITION_IN_USE_STATUS = sysinv.PARTITION_IN_USE_STATUS
        PARTITION_STATUS_MSG = sysinv.PARTITION_STATUS_MSG

        if partition:
            if partition.type_guid != sysinv.USER_PARTITION_PHYS_VOL:
                return False

            if (partition.status ==
                    PARTITION_STATUS_MSG[PARTITION_IN_USE_STATUS]):
                return False

            if partition.ipv_uuid:
                return False

            # Get all the partitions from the same disk.
            disk_partitions = \
                sysinv.host_disk_partition_list(request, host.uuid,
                                                partition.idisk_uuid)

            if partition.device_path:
                partition_number = re.match('.*?([0-9]+)$',
                                            partition.device_path).group(1)
                for dpart in disk_partitions:
                    dpart_number = re.match('.*?([0-9]+)$',
                                            dpart.device_path).group(1)
                    if int(dpart_number) > int(partition_number):
                        return False

        return True

    def delete(self, request, partition_id):
        host_id = self.table.kwargs['host_id']
        try:
            sysinv.host_disk_partition_delete(request, partition_id)
        except Exception as e:
            msg = _('Failed to delete host %(hid)s partition %(pv)s. '
                    '%(e_msg)s') % {'hid': host_id,
                                    'pv': partition_id,
                                    'e_msg': e}
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class EditPartition(tables.LinkAction):
    name = "editpartition"
    verbose_name = _("Edit")
    url = "horizon:admin:inventory:editpartition"

    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, partition):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, partition.uuid))

    def allowed(self, request, partition=None):
        host = self.table.kwargs['host']
        PARTITION_IN_USE_STATUS = sysinv.PARTITION_IN_USE_STATUS
        PARTITION_STATUS_MSG = sysinv.PARTITION_STATUS_MSG

        if partition:
            pv = None

            if partition.type_guid != sysinv.USER_PARTITION_PHYS_VOL:
                return False

            if partition.ipv_uuid:
                pv = sysinv.host_pv_get(
                    request, partition.ipv_uuid)
                if pv.lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
                    if (host.personality == "Controller-Active" and
                            host._administrative == 'unlocked'):
                        return False
                else:
                    return False

            if (partition.status ==
                    PARTITION_STATUS_MSG[PARTITION_IN_USE_STATUS]):
                if not (pv and
                        pv.lvm_vg_name == sysinv.LVG_CINDER_VOLUMES):
                    return False

            # Get all the partitions from the same disk.
            disk_partitions = \
                sysinv.host_disk_partition_list(request,
                                                host.uuid,
                                                partition.idisk_uuid)

            if partition.device_path:
                partition_number = re.match('.*?([0-9]+)$',
                                            partition.device_path).group(1)
                for dpart in disk_partitions:
                    dpart_number = re.match('.*?([0-9]+)$',
                                            dpart.device_path).group(1)
                    if int(dpart_number) > int(partition_number):
                        return False

        return True

# ##########
# TABLES
# ##########


def get_model_num(disk):
    return disk.get_model_num()


def get_disk_info(disk):
    template_name = 'admin/inventory/_disk_info.html'
    context = {
        "disk": disk,
        "disk_info": disk.device_path,
        "id": disk.uuid,
    }
    return template.loader.render_to_string(template_name, context)


class DisksTable(tables.DataTable):
    uuid = tables.Column('uuid',
                         verbose_name=('UUID'))
    disk_info = tables.Column(get_disk_info,
                              verbose_name=_("Disk info"),
                              attrs={'data-type': 'disk_info'})
    type = tables.Column('device_type',
                         verbose_name=('Type'))
    size = tables.Column('size_gib',
                         verbose_name=('Size (GiB)'))
    available_size = tables.Column('available_gib',
                                   verbose_name=('Available Size (GiB)'))
    rpm = tables.Column('rpm',
                        verbose_name=('RPM'))

    serial_id = tables.Column('serial_id',
                              verbose_name=('Serial ID'))

    model_num = tables.Column(get_model_num,
                              verbose_name=('Model'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "disks"
        verbose_name = ("Disks")
        columns = ('uuid', 'disk_info', 'type', 'size', 'available_size',
                   'rpm', 'serial_id', 'model_num')
        multi_select = False
        table_actions = ()


class EditStor(tables.LinkAction):
    name = "editstoragevolume"
    verbose_name = _("Edit")
    url = "horizon:admin:inventory:editstoragevolume"

    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, stor):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, stor.uuid))

    def allowed(self, request, stor=None):
        host = self.table.kwargs['host']

        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        if host._administrative == 'unlocked':
            if 'storage' in host._subfunctions:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']

        if stor and stor.function == 'osd':
            forihostuuid = self.table.kwargs['host'].uuid
            journal_stors = \
                sysinv.host_stor_get_by_function(request, forihostuuid,
                                                 'journal')

            if not journal_stors:
                self.classes = [c for c in self.classes] + ['disabled']

            return True


class DeleteStor(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Journal",
            "Delete Journals",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Journal",
            "Deleted Journals",
            count
        )

    def allowed(self, request, stor):
        host = self.table.kwargs['host']

        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        if host._administrative == 'unlocked':
            if 'storage' in host._subfunctions:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']

        if stor:
            return stor.function == 'journal'

    def delete(self, request, obj_id):
        sysinv.host_stor_delete(request, obj_id)


class StorageVolumesTable(tables.DataTable):
    uuid = tables.Column('uuid',
                         verbose_name=('UUID'))
    osdid = tables.Column('osdid',
                          verbose_name=('OSD ID'))
    function = tables.Column('function',
                             verbose_name=('Function'))
    idisk_uuid = tables.Column('idisk_uuid',
                               verbose_name=('Disk UUID'))
    journal_path = tables.Column('journal_path',
                                 verbose_name=('Journal Path'))
    journal_size_mib = tables.Column('journal_size_gib',
                                     verbose_name=('Journal GiB'))
    journal_location = tables.Column('journal_location',
                                     verbose_name=('Journal Location'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "storagevolumes"
        verbose_name = ("Storage Functions")
        columns = ('uuid', 'function', 'osdid', 'idisk_uuid', 'journal_path',
                   'journal_size_mib', 'journal_location')
        multi_select = False
        row_actions = (DeleteStor, EditStor,)
        table_actions = (CreateStorageVolume, CreateDiskProfile,)


class AddLocalVolumeGroup(tables.LinkAction):
    name = "addlocalvolumegroup"
    verbose_name = ("Add Local Volume Group")
    url = "horizon:admin:inventory:addlocalvolumegroup"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        self.verbose_name = _("Add Local Volume Group")
        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        if not host._administrative == 'locked':
            if 'worker' in host._subfunctions and \
               host.worker_config_required is False:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Node Unlocked)"))

        # LVGs that are considered as "present" in the system are those
        # in an adding or provisioned state.
        current_lvg_states = [sysinv.LVG_ADD, sysinv.LVG_PROV]
        ilvg_list = sysinv.host_lvg_list(request, host.uuid)
        current_lvgs = [lvg.lvm_vg_name for lvg in ilvg_list
                        if lvg.vg_state in current_lvg_states]
        compatible_lvgs = []

        if host._personality == 'controller':
            compatible_lvgs += [sysinv.LVG_CINDER_VOLUMES]

        if 'worker' in host._subfunctions:
            compatible_lvgs += [sysinv.LVG_NOVA_LOCAL]

        allowed_lvgs = set(compatible_lvgs) - set(current_lvgs)
        if not any(allowed_lvgs):
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(All Added)"))

        return True  # The action should always be displayed


class RemoveLocalVolumeGroup(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Local Volume Group",
            "Delete Local Volume Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Local Volume Group",
            "Deleted Local Volume Groups",
            count
        )

    def allowed(self, request, lvg=None):
        host = self.table.kwargs['host']
        cinder_backend = sysinv.get_cinder_backend(request)

        if lvg.lvm_vg_name == sysinv.LVG_NOVA_LOCAL:
            return ((host._administrative == 'locked') or
                    (('worker' in host._subfunctions) and
                     (host.worker_config_required is True)))
        elif lvg.lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
            return (sysinv.CINDER_BACKEND_LVM not in cinder_backend and
                    sysinv.LVG_ADD in lvg.vg_state)

        return False

    def delete(self, request, lvg_id):
        host_id = self.table.kwargs['host_id']
        try:
            sysinv.host_lvg_delete(request, lvg_id)
        except Exception as e:
            msg = _('Failed to delete host %(hid)s local '
                    'volume group %(lvg)s '
                    '%(e_msg)s') % \
                {'hid': host_id, 'lvg': lvg_id, 'e_msg': e}

            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class LocalVolumeGroupsTable(tables.DataTable):
    name = tables.Column('lvm_vg_name',
                         link="horizon:admin:inventory:localvolumegroupdetail",
                         verbose_name=('Name'))
    state = tables.Column('vg_state',
                          verbose_name=('State'))
    access = tables.Column('lvm_vg_access',
                           verbose_name=('Access'))
    size = tables.Column('lvm_vg_size_gib',
                         verbose_name=('Size (GiB)'))
    avail_size = tables.Column('lvm_vg_avail_size_gib',
                               verbose_name=('Avail Size (GiB)'))
    pvs = tables.Column('lvm_cur_pv',
                        verbose_name=('Current Physical Volumes'))
    lvs = tables.Column('lvm_cur_lv',
                        verbose_name=('Current Logical Volumes'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        msg = datum.uuid
        if datum.lvm_vg_name:
            msg += " (%s)" % datum.lvm_vg_name
        return str(msg)

    class Meta(object):
        name = "localvolumegroups"
        verbose_name = ("Local Volume Groups")
        columns = ('name', 'state', 'access', 'size', 'avail_size',
                   'pvs', 'lvs',)
        multi_select = False
        row_actions = (RemoveLocalVolumeGroup,)
        table_actions = (AddLocalVolumeGroup, CreateDiskProfile)


class AddPhysicalVolume(tables.LinkAction):
    name = "addphysicalvolume"
    verbose_name = ("Add Physical Volume")
    url = "horizon:admin:inventory:addphysicalvolume"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        self.verbose_name = _("Add Physical Volume")
        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes

        # cgts-vg, cinder-volumes: Allow adding to any controller
        if host._personality == sysinv.PERSONALITY_CONTROLLER:
            return True

        # nova-local: Allow adding to any locked host with a worker
        # subfunction. On an AIO, the previous check superceeds this.
        if host._administrative != 'locked':
            if 'worker' in host._subfunctions and \
               host.worker_config_required is False:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
                    self.verbose_name = string_concat(self.verbose_name, ' ',
                                                      _("(Node Unlocked)"))
        elif "nova-local" not in [
                lvg.lvm_vg_name for lvg in
                sysinv.host_lvg_list(request, host.uuid)]:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(No nova-local LVG)"))

        return True  # The action should always be displayed


class RemovePhysicalVolume(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Physical Volume",
            "Delete Physical Volumes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Physical Volume",
            "Deleted Physical Volumes",
            count
        )

    def allowed(self, request, pv=None):
        host = self.table.kwargs['host']
        cinder_backend = sysinv.get_cinder_backend(request)

        if pv.lvm_vg_name == sysinv.LVG_NOVA_LOCAL:
            return ((host._administrative == 'locked') or
                    (('worker' in host._subfunctions) and
                     (host.worker_config_required is True)))
        elif pv.lvm_vg_name == sysinv.LVG_CINDER_VOLUMES:
            return (sysinv.CINDER_BACKEND_LVM not in cinder_backend and
                    sysinv.PV_ADD in pv.pv_state)

        return False

    def delete(self, request, pv_id):
        host_id = self.table.kwargs['host_id']
        try:
            sysinv.host_pv_delete(request, pv_id)
        except Exception as e:
            msg = _('Failed to delete host %(hid)s physical volume %(pv)s. '
                    '%(e_msg)s') % {'hid': host_id, 'pv': pv_id, 'e_msg': e}
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class PhysicalVolumesTable(tables.DataTable):
    name = tables.Column('lvm_pv_name',
                         link="horizon:admin:inventory:physicalvolumedetail",
                         verbose_name=('Name'))
    pv_state = tables.Column('pv_state',
                             verbose_name=('State'))
    pv_type = tables.Column('pv_type',
                            verbose_name=('Type'))
    disk_or_part_uuid = tables.Column('disk_or_part_uuid',
                                      verbose_name=('Disk or Partition UUID'))
    disk_or_part_device_path = tables.Column('disk_or_part_device_path',
                                             verbose_name=('Disk or Partition'
                                                           ' Device Path'))
    lvm_vg_name = tables.Column('lvm_vg_name',
                                verbose_name=('LVM Volume Group Name'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        msg = datum.uuid
        if datum.lvm_pv_name:
            msg += " (%s)" % datum.lvm_pv_name
        return str(msg)

    class Meta(object):
        name = "physicalvolumes"
        verbose_name = ("Physical Volumes")
        columns = ('name', 'pv_state', 'pv_type', 'disk_or_part_uuid',
                   'disk_or_part_device_node', 'disk_or_part_device_path',
                   'lvm_vg_name')
        multi_select = False
        table_actions = (AddPhysicalVolume,)
        row_actions = (RemovePhysicalVolume,)


class PartitionsTable(tables.DataTable):
    uuid = tables.Column('uuid',
                         verbose_name=('UUID'))
    size_mib = tables.Column('size_gib',
                             verbose_name=('Size (GiB)'))
    device_path = tables.Column('device_path',
                                verbose_name=('Partition Device Path'))
    type_name = tables.Column('type_name',
                              verbose_name=('Partition Type'))
    ipv_uuid = tables.Column('ipv_uuid',
                             verbose_name=('Physical Volume UUID'))
    idisk_uuid = tables.Column('disk_uuid',
                               verbose_name=('Disk UUID'))
    status = tables.Column('status',
                           verbose_name=('Status'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        msg = datum.uuid
        if datum.device_path:
            msg += " (%s)" % datum.device_path
        return str(msg)

    class Meta(object):
        name = "partitions"
        verbose_name = ("Partitions")
        columns = ('uuid', 'device_path', 'size_mib', 'type_name', 'status')
        multi_select = False
        row_actions = (EditPartition, DeletePartition,)
        table_actions = (CreatePartition,)
