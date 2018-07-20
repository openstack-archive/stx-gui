#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

from __future__ import absolute_import

import datetime
import logging

from cgtsclient.v1 import client as cgts_client
from cgtsclient.v1 import icpu as icpu_utils

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.api import base

import cgcs_patch.constants as patch_constants
import sysinv.common.constants as constants

SYSTEM_TYPE_STANDARD = constants.TIS_STD_BUILD
SYSTEM_TYPE_AIO = constants.TIS_AIO_BUILD

PERSONALITY_CONTROLLER = 'controller'
PERSONALITY_COMPUTE = 'compute'
PERSONALITY_NETWORK = 'network'
PERSONALITY_STORAGE = 'storage'
PERSONALITY_UNKNOWN = 'unknown'

SUBFUNCTIONS_COMPUTE = 'compute'
SUBFUNCTIONS_LOWLATENCY = 'lowlatency'

BM_TYPE_NULL = ''
BM_TYPE_NONE = 'none'
BM_TYPE_GENERIC = 'bmc'

RECORDTYPE_INSTALL = 'install'
RECORDTYPE_INSTALL_ANSWER = 'install_answers'
RECORDTYPE_RECONFIG = 'reconfig'

INSTALL_OUTPUT_TEXT = 'text'
INSTALL_OUTPUT_GRAPHICAL = 'graphical'

# Sensor Actions Choices
SENSORS_AC_NOACTIONSCONFIGURABLE = "NoActionsConfigurable"
SENSORS_AC_NONE = "None"
SENSORS_AC_IGNORE = "ignore"
SENSORS_AC_LOG = "log"
SENSORS_AC_ALARM = "alarm"
SENSORS_AC_RESET = "reset"
SENSORS_AC_POWERCYCLE = "power-cycle"
SENSORS_AC_POWEROFF = "poweroff"

# Cinder backend values
CINDER_BACKEND_LVM = "lvm"
CINDER_BACKEND_CEPH = "ceph"

# Local Volume Group Values
LVG_NOVA_LOCAL = "nova-local"
LVG_CGTS_VG = "cgts-vg"
LVG_CINDER_VOLUMES = "cinder-volumes"
LVG_DEL = 'removing'
LVG_ADD = 'adding'
LVG_PROV = 'provisioned'

# Physical Volume Values
PV_ADD = 'adding'
PV_DEL = 'removing'

# Storage: Volume Group Parameter Types
LVG_NOVA_PARAM_BACKING = 'instance_backing'
LVG_NOVA_PARAM_INSTANCES_SIZE_MIB = 'instances_lv_size_mib'
LVG_NOVA_PARAM_DISK_OPS = 'concurrent_disk_operations'
LVG_NOVA_BACKING_LVM = 'lvm'
LVG_NOVA_BACKING_IMAGE = 'image'
LVG_NOVA_BACKING_REMOTE = 'remote'
LVG_CINDER_PARAM_LVM_TYPE = 'lvm_type'
LVG_CINDER_LVM_TYPE_THIN = 'thin'
LVG_CINDER_LVM_TYPE_THICK = 'default'

# Storage: User Created Partitions
USER_PARTITION_PHYS_VOL = constants.USER_PARTITION_PHYSICAL_VOLUME
PARTITION_STATUS_MSG = constants.PARTITION_STATUS_MSG
PARTITION_IN_USE_STATUS = constants.PARTITION_IN_USE_STATUS

# Fault management values
FM_ALL = 'ALL'
FM_ALARM = 'ALARM'
FM_LOG = 'LOG'
FM_SUPPRESS_SHOW = 'SUPPRESS_SHOW'
FM_SUPPRESS_HIDE = 'SUPPRESS_HIDE'
FM_ALL_SUPPRESS_HIDE = 'ALL|SUPPRESS_HIDE'
FM_SUPPRESSED = 'suppressed'
FM_UNSUPPRESSED = 'unsuppressed'
FM_CRITICAL = 'critical'
FM_MAJOR = 'major'
FM_MINOR = 'minor'
FM_WARNING = 'warning'
FM_NONE = 'none'

# Host Personality Sub-Types
PERSONALITY_SUBTYPE_CEPH_BACKING = 'ceph-backing'
PERSONALITY_SUBTYPE_CEPH_CACHING = 'ceph-caching'

# The default size of a stor's journal. This should be the same value as
# journal_default_size from sysinv.conf.
JOURNAL_DEFAULT_SIZE = 1024

# Platform configuration
PLATFORM_CONFIGURATION = '/etc/platform/platform.conf'

# Neutron ML2 Service Parameters (ripped from sysinv constants)
SERVICE_TYPE_NETWORK = 'network'
SERVICE_PARAM_SECTION_NETWORK_DEFAULT = 'default'
SERVICE_PARAM_NAME_DEFAULT_SERVICE_PLUGINS = 'service_plugins'
SERVICE_PARAM_ODL_ROUTER_PLUGINS = [
    'odl-router',
    'networking_odl.l3.l3_odl.OpenDaylightL3RouterPlugin']

LOG = logging.getLogger(__name__)


def cgtsclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    # FIXME this returns the wrong URL
    endpoint = base.url_for(request, 'platform', 'adminURL')
    version = 1

    LOG.debug('cgtsclient connection created using token "%s" and url "%s"',
              request.user.token.id, endpoint)
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s',
              {'user': request.user.id, 'tenant': request.user.tenant_id})

    return cgts_client.Client(version=version,
                              endpoint=endpoint,
                              auth_url=base.url_for(request, 'identity',
                                                    'adminURL'),
                              token=request.user.token.id,  # os_auth_token
                              username=request.user.username,
                              password=request.user.token.id,
                              tenant_id=request.user.tenant_id,  # os_tenant_id
                              insecure=insecure, cacert=cacert)


class Memory(base.APIResourceWrapper):
    """Wrapper for Inventory System"""

    _attrs = ['numa_node',
              'memtotal_mib',
              'platform_reserved_mib',
              'memavail_mib',
              'hugepages_configured',
              'vm_hugepages_nr_2M_pending',
              'vm_hugepages_avail_2M',
              'vm_hugepages_nr_1G_pending',
              'vm_hugepages_avail_1G',
              'vm_hugepages_nr_1G',
              'vm_hugepages_nr_2M',
              'vm_hugepages_nr_4K',
              'vm_hugepages_possible_2M',
              'vm_hugepages_possible_1G',
              'vm_hugepages_use_1G',
              'uuid', 'ihost_uuid', 'inode_uuid',
              'minimum_platform_reserved_mib']

    def __init__(self, apiresource):
        super(Memory, self).__init__(apiresource)


class System(base.APIResourceWrapper):
    """Wrapper for Inventory System"""

    _attrs = ['uuid', 'name', 'system_type', 'system_mode', 'description',
              'software_version', 'capabilities', 'updated_at', 'created_at',
              'location']

    def __init__(self, apiresource):
        super(System, self).__init__(apiresource)

    def get_short_software_version(self):
        if self.software_version:
            return self.software_version.split(" ")[0]
        return None


class Node(base.APIResourceWrapper):
    """Wrapper for Inventory Node (or Socket)"""

    _attrs = ['uuid', 'numa_node', 'capabilities', 'ihost_uuid']

    def __init__(self, apiresource):
        super(Node, self).__init__(apiresource)


class Cpu(base.APIResourceWrapper):
    """Wrapper for Inventory Cpu Cores"""

    _attrs = ['id', 'uuid', 'cpu', 'numa_node', 'core', 'thread',
              'allocated_function',
              'cpu_model', 'cpu_family',
              'capabilities',
              'ihost_uuid', 'inode_uuid']

    def __init__(self, apiresource):
        super(Cpu, self).__init__(apiresource)


class Port(base.APIResourceWrapper):
    """Wrapper for Inventory Ports"""

    _attrs = ['id', 'uuid', 'name', 'namedisplay', 'pciaddr', 'pclass',
              'pvendor', 'pdevice', 'interface_id',
              'psvendor', 'psdevice', 'numa_node', 'mac', 'mtu', 'speed',
              'link_mode', 'capabilities', 'host_uuid', 'interface_uuid',
              'bootp', 'autoneg', 'type', 'sriov_numvfs', 'sriov_totalvfs',
              'sriov_vfs_pci_address', 'driver', 'dpdksupport', 'neighbours']

    def __init__(self, apiresource):
        super(Port, self).__init__(apiresource)
        self.autoneg = 'Yes'  # TODO(wrs) Remove this when autoneg supported
        # in DB

    def get_port_display_name(self):
        if self.name:
            return self.name
        if self.namedisplay:
            return self.namedisplay
        else:
            return '(' + str(self.uuid)[-8:] + ')'


class Disk(base.APIResourceWrapper):
    """Wrapper for Inventory Disks"""

    _attrs = ['uuid',
              'device_node',
              'device_path',
              'device_id',
              'device_wwn',
              'device_num',
              'device_type',
              'size_mib',
              'available_mib',
              'rpm',
              'serial_id',
              'capabilities',
              'ihost_uuid',
              'istor_uuid',
              'ipv_uuid']

    def __init__(self, apiresource):
        super(Disk, self).__init__(apiresource)

    def get_model_num(self):
        if 'model_num' in self.capabilities:
            return self.capabilities['model_num']


class StorageVolume(base.APIResourceWrapper):
    """Wrapper for Inventory Volumes"""

    _attrs = ['uuid',
              'osdid',
              'state',
              'function',
              'capabilities',
              'idisk_uuid',
              'ihost_uuid',
              'tier_name',
              'journal_path',
              'journal_size_mib',
              'journal_location']

    def __init__(self, apiresource):
        super(StorageVolume, self).__init__(apiresource)


class PhysicalVolume(base.APIResourceWrapper):
    """Wrapper for Physical Volumes"""

    _attrs = ['uuid',
              'pv_state',
              'pv_type',
              'disk_or_part_uuid',
              'disk_or_part_device_node',
              'disk_or_part_device_path',
              'lvm_pv_name',
              'lvm_vg_name',
              'lvm_pv_uuid',
              'lvm_pv_size',
              'lvm_pe_total',
              'lvm_pe_alloced',
              'ihost_uuid',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(PhysicalVolume, self).__init__(apiresource)


def host_pv_list(request, host_id):
    pvs = cgtsclient(request).ipv.list(host_id)
    return [PhysicalVolume(n) for n in pvs]


def host_pv_get(request, ipv_id):
    pv = cgtsclient(request).ipv.get(ipv_id)
    if not pv:
        raise ValueError('No match found for pv_id "%s".' % ipv_id)
    return PhysicalVolume(pv)


def host_pv_create(request, **kwargs):
    pv = cgtsclient(request).ipv.create(**kwargs)
    return PhysicalVolume(pv)


def host_pv_delete(request, ipv_id):
    return cgtsclient(request).ipv.delete(ipv_id)


class Partition(base.APIResourceWrapper):
    """Wrapper for Inventory Partitions."""

    _attrs = ['uuid',
              'start_mib',
              'end_mib',
              'size_mib',
              'device_path',
              'type_guid',
              'type_name',
              'idisk_uuid',
              'ipv_uuid',
              'ihost_uuid',
              'status']

    def __init__(self, apiresource):
        super(Partition, self).__init__(apiresource)


def host_disk_partition_list(request, host_id, disk_id=None):
    partitions = cgtsclient(request).partition.list(host_id, disk_id)
    return [Partition(p) for p in partitions]


def host_disk_partition_get(request, partition_id):
    partition = cgtsclient(request).partition.get(partition_id)
    if not partition:
        raise ValueError('No match found for partition_id '
                         '"%s".' % partition_id)
    return Partition(partition)


def host_disk_partition_create(request, **kwargs):
    partition = cgtsclient(request).partition.create(**kwargs)
    return Partition(partition)


def host_disk_partition_update(request, partition_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    partition = cgtsclient(request).partition.update(partition_id, mypatch)
    return Partition(partition)


def host_disk_partition_delete(request, partition_id, **kwargs):
    return cgtsclient(request).partition.delete(partition_id)


class LocalVolumeGroup(base.APIResourceWrapper):
    """Wrapper for Inventory Local Volume Groups"""

    _attrs = ['lvm_vg_name',
              'vg_state',
              'uuid',
              'ihost_uuid',
              'capabilities',
              'lvm_vg_access',
              'lvm_max_lv',
              'lvm_cur_lv',
              'lvm_max_pv',
              'lvm_cur_pv',
              'lvm_vg_size',
              'lvm_vg_total_pe',
              'lvm_vg_free_pe',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(LocalVolumeGroup, self).__init__(apiresource)


class LocalVolumeGroupParam(object):
    def __init__(self, lvg_id, key, val):
        self.lvg_id = lvg_id
        self.id = key
        self.key = key
        self.value = val


def host_lvg_list(request, host_id, get_params=False):
    lvgs = cgtsclient(request).ilvg.list(host_id)
    if get_params:
        for lvg in lvgs:
            lvg.params = host_lvg_get_params(request, lvg.uuid, True, lvg)
    return [LocalVolumeGroup(n) for n in lvgs]


def host_lvg_get(request, ilvg_id, get_params=False):
    lvg = cgtsclient(request).ilvg.get(ilvg_id)
    if not lvg:
        raise ValueError('No match found for lvg_id "%s".' % ilvg_id)
    if get_params:
        lvg.params = host_lvg_get_params(request, lvg.id, True, lvg)
    return LocalVolumeGroup(lvg)


def host_lvg_create(request, **kwargs):
    lvg = cgtsclient(request).ilvg.create(**kwargs)
    return LocalVolumeGroup(lvg)


def host_lvg_delete(request, ilvg_id):
    return cgtsclient(request).ilvg.delete(ilvg_id)


def host_lvg_update(request, ilvg_id, patch):
    return cgtsclient(request).ilvg.update(ilvg_id, patch)


def host_lvg_get_params(request, lvg_id, raw=False, lvg=None):
    if lvg is None:
        lvg = cgtsclient(request).ilvg.get(lvg_id)
    params = lvg.capabilities
    if raw:
        return params
    return [LocalVolumeGroupParam(lvg_id, key, value) for
            key, value in params.items()]


class Sensor(base.APIResourceWrapper):
    """Wrapper for Sensors"""

    _attrs = ['uuid',
              'status',
              'state',
              'sensortype',
              'datatype',
              'sensorname',
              'actions_critical',
              'actions_major',
              'actions_minor',
              'host_uuid',
              'sensorgroup_uuid',
              'suppress',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(Sensor, self).__init__(apiresource)

    def get_sensor_display_name(self):
        if self.sensorname:
            return self.sensorname
        else:
            return '(' + str(self.uuid)[-8:] + ')'


def host_sensor_list(request, host_id):
    sensors = cgtsclient(request).isensor.list(host_id)
    return [Sensor(n) for n in sensors]


def host_sensor_get(request, isensor_id):
    sensor = cgtsclient(request).isensor.get(isensor_id)
    if not sensor:
        raise ValueError('No match found for sensor_id "%s".' % isensor_id)
    return Sensor(sensor)


def host_sensor_create(request, **kwargs):
    sensor = cgtsclient(request).isensor.create(**kwargs)
    return Sensor(sensor)


def host_sensor_update(request, sensor_id, **kwargs):
    LOG.debug("sensor_update(): sensor_id=%s, kwargs=%s", sensor_id, kwargs)
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isensor.update(sensor_id, mypatch)


def host_sensor_suppress(request, sensor_id):
    kwargs = {'suppress': "True"}
    sensor = host_sensor_update(request, sensor_id, **kwargs)
    return sensor


def host_sensor_unsuppress(request, sensor_id):
    kwargs = {'suppress': "False"}
    sensor = host_sensor_update(request, sensor_id, **kwargs)
    return sensor


def host_sensor_delete(request, isensor_id):
    return cgtsclient(request).isensor.delete(isensor_id)


class SensorGroup(base.APIResourceWrapper):
    """Wrapper for Inventory Sensor Groups"""

    _attrs = ['uuid',
              'sensorgroupname',
              'sensortype',
              'state',
              'datatype',
              'sensors',
              'host_uuid',
              'algorithm',
              'actions_critical_group',
              'actions_major_group',
              'actions_minor_group',
              'actions_critical_choices',
              'actions_major_choices',
              'actions_minor_choices',
              'audit_interval_group',
              'suppress',
              'created_at',
              'updated_at']

    ACTIONS_DISPLAY_CHOICES = (
        (None, _("None")),
        (SENSORS_AC_NONE, _("None.")),
        (SENSORS_AC_IGNORE, _("Ignore")),
        (SENSORS_AC_LOG, _("Log")),
        (SENSORS_AC_ALARM, _("Alarm")),
        (SENSORS_AC_RESET, _("Reset Host")),
        (SENSORS_AC_POWERCYCLE, _("Power Cycle Host")),
        (SENSORS_AC_POWEROFF, _("Power Off Host")),
        (SENSORS_AC_NOACTIONSCONFIGURABLE, _("No Configurable Actions")),
    )

    def __init__(self, apiresource):
        super(SensorGroup, self).__init__(apiresource)

    def get_sensorgroup_display_name(self):
        if self.sensorgroupname:
            return self.sensorgroupname
        else:
            return '(' + str(self.uuid)[-8:] + ')'

    @staticmethod
    def _get_display_value(display_choices, data):
        """Lookup the display value in the provided dictionary."""
        display_value = [display for (value, display) in display_choices
                         if value and value.lower() == (data or '').lower()]

        if display_value:
            return display_value[0]
        return None

    def _get_sensorgroup_actions_critical_list(self):
        actions_critical_choices_list = []
        if self.actions_critical_choices:
            actions_critical_choices_list = \
                self.actions_critical_choices.split(",")

        return actions_critical_choices_list

    @property
    def sensorgroup_actions_critical_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_critical_choices)

        actions_critical_choices_tuple = (self.actions_critical_choices, dv)

        return actions_critical_choices_tuple

    @property
    def sensorgroup_actions_critical_choices_tuple_list(self):
        actions_critical_choices_list = \
            self._get_sensorgroup_actions_critical_list()

        actions_critical_choices_tuple_list = []
        if not actions_critical_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_critical_choices_tuple_list.append((ac, dv))
        else:
            actions_critical_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_critical_choices_tuple_set.add((ac, dv))

            for ac in actions_critical_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_critical_choices_tuple_set.add((ac, dv))

            actions_critical_choices_tuple_list = \
                list(actions_critical_choices_tuple_set)

        LOG.debug("actions_critical_choices_tuple_list=%s",
                  actions_critical_choices_tuple_list)

        return actions_critical_choices_tuple_list

    def _get_sensorgroup_actions_major_list(self):
        actions_major_choices_list = []
        if self.actions_major_choices:
            actions_major_choices_list = \
                self.actions_major_choices.split(",")

        return actions_major_choices_list

    @property
    def sensorgroup_actions_major_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_major_choices)

        actions_major_choices_tuple = (self.actions_major_choices, dv)

        return actions_major_choices_tuple

    @property
    def sensorgroup_actions_major_choices_tuple_list(self):
        actions_major_choices_list = self._get_sensorgroup_actions_major_list()

        actions_major_choices_tuple_list = []
        if not actions_major_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_major_choices_tuple_list.append((ac, dv))
        else:
            actions_major_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_major_choices_tuple_set.add((ac, dv))

            for ac in actions_major_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_major_choices_tuple_set.add((ac, dv))

            actions_major_choices_tuple_list = \
                list(actions_major_choices_tuple_set)

        LOG.debug("actions_major_choices_tuple_list=%s",
                  actions_major_choices_tuple_list)

        return actions_major_choices_tuple_list

    def _get_sensorgroup_actions_minor_list(self):
        actions_minor_choices_list = []
        if self.actions_minor_choices:
            actions_minor_choices_list = \
                self.actions_minor_choices.split(",")

        return actions_minor_choices_list

    @property
    def sensorgroup_actions_minor_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_minor_choices)

        actions_minor_choices_tuple = (self.actions_minor_choices, dv)

        return actions_minor_choices_tuple

    @property
    def sensorgroup_actions_minor_choices_tuple_list(self):
        actions_minor_choices_list = self._get_sensorgroup_actions_minor_list()

        actions_minor_choices_tuple_list = []
        if not actions_minor_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_minor_choices_tuple_list.append((ac, dv))
        else:
            actions_minor_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_minor_choices_tuple_set.add((ac, dv))

            for ac in actions_minor_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_minor_choices_tuple_set.add((ac, dv))

            actions_minor_choices_tuple_list = \
                list(actions_minor_choices_tuple_set)

        LOG.debug("actions_minor_choices_tuple_list=%s",
                  actions_minor_choices_tuple_list)

        return actions_minor_choices_tuple_list


def host_sensorgroup_list(request, host_id):
    sensorgroups = cgtsclient(request).isensorgroup.list(host_id)
    return [SensorGroup(n) for n in sensorgroups]


def host_sensorgroup_get(request, isensorgroup_id):
    sensorgroup = cgtsclient(request).isensorgroup.get(isensorgroup_id)
    if not sensorgroup:
        raise ValueError('No match found for sensorgroup_id "%s".' %
                         isensorgroup_id)
    return SensorGroup(sensorgroup)


def host_sensorgroup_create(request, **kwargs):
    sensorgroup = cgtsclient(request).isensorgroup.create(**kwargs)
    return SensorGroup(sensorgroup)


def host_sensorgroup_update(request, sensorgroup_id, **kwargs):
    LOG.debug("sensorgroup_update(): sensorgroup_id=%s, kwargs=%s",
              sensorgroup_id, kwargs)
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isensorgroup.update(sensorgroup_id, mypatch)


def host_sensorgroup_delete(request, isensorgroup_id):
    return cgtsclient(request).isensorgroup.delete(isensorgroup_id)


def host_sensorgroup_relearn(request, host_uuid):
    LOG.info("relearn sensor model for host %s", host_uuid)
    return cgtsclient(request).isensorgroup.relearn(host_uuid)


def host_sensorgroup_suppress(request, sensorgroup_id):
    kwargs = {'suppress': "True"}
    sensorgroup = host_sensorgroup_update(request, sensorgroup_id, **kwargs)
    return sensorgroup


def host_sensorgroup_unsuppress(request, sensorgroup_id):
    kwargs = {'suppress': "False"}
    sensorgroup = host_sensorgroup_update(request, sensorgroup_id, **kwargs)
    return sensorgroup


class Host(base.APIResourceWrapper):
    """Wrapper for Inventory Hosts"""

    _attrs = ['id', 'uuid', 'hostname', 'personality', 'pers_subtype',
              'subfunctions', 'subfunction_oper', 'subfunction_avail',
              'location', 'serialid', 'operational', 'administrative',
              'invprovision', 'peers',
              'availability', 'uptime', 'task', 'capabilities',
              'created_at', 'updated_at', 'mgmt_mac', 'mgmt_ip',
              'bm_ip', 'bm_type', 'bm_username',
              'config_status', 'vim_progress_status', 'patch_current',
              'requires_reboot', 'boot_device', 'rootfs_device',
              'install_output', 'console', 'ttys_dcd', 'patch_state',
              'allow_insvc_patching', 'install_state', 'install_state_info']

    PERSONALITY_DISPLAY_CHOICES = (
        (PERSONALITY_CONTROLLER, _("Controller")),
        (PERSONALITY_COMPUTE, _("Compute")),
        (PERSONALITY_NETWORK, _("Network")),
        (PERSONALITY_STORAGE, _("Storage")),
    )
    ADMIN_DISPLAY_CHOICES = (
        ('locked', _("Locked")),
        ('unlocked', _("Unlocked")),
    )
    OPER_DISPLAY_CHOICES = (
        ('disabled', _("Disabled")),
        ('enabled', _("Enabled")),
    )
    AVAIL_DISPLAY_CHOICES = (
        ('available', _("Available")),
        ('intest', _("In-Test")),
        ('degraded', _("Degraded")),
        ('failed', _("Failed")),
        ('power-off', _("Powered-Off")),
        ('offline', _("Offline")),
        ('online', _("Online")),
        ('offduty', _("Offduty")),
        ('dependency', _("Dependency")),
    )
    CONFIG_STATUS_DISPLAY_CHOICES = (
        ('up_to_date', _("up-to-date")),
        ('out_of_date', _("out-of-date")),
    )
    PATCH_STATE_DISPLAY_CHOICES = (
        (patch_constants.PATCH_AGENT_STATE_IDLE,
         _("Idle")),
        (patch_constants.PATCH_AGENT_STATE_INSTALLING,
         _("Patch Installing")),
        (patch_constants.PATCH_AGENT_STATE_INSTALL_FAILED,
         _("Patch Install Failed")),
        (patch_constants.PATCH_AGENT_STATE_INSTALL_REJECTED,
         _("Patch Install Rejected")),
    )

    INSTALL_STATE_DISPLAY_CHOICES = (
        (constants.INSTALL_STATE_PRE_INSTALL, _("Pre-install")),
        (constants.INSTALL_STATE_INSTALLING, _("Installing Packages")),
        (constants.INSTALL_STATE_POST_INSTALL, _("Post-install")),
        (constants.INSTALL_STATE_FAILED, _("Install Failed")),
        (constants.INSTALL_STATE_INSTALLED, _("Installed")),
        (constants.INSTALL_STATE_BOOTING, _("Booting")),
        (constants.INSTALL_STATE_COMPLETED, _("Completed")),
    )

    SUBTYPE_CHOICES = (
        (PERSONALITY_SUBTYPE_CEPH_BACKING, _("CEPH backing")),
        (PERSONALITY_SUBTYPE_CEPH_CACHING, _("CEPH caching")),
    )

    def __init__(self, apiresource):
        super(Host, self).__init__(apiresource)
        self._personality = self.personality
        self._subfunctions = self.subfunctions
        self._subfunction_oper = self.subfunction_oper
        self._subfunction_avail = self.subfunction_avail
        self._location = self.location
        self._peers = self.peers
        self._bm_type = self.bm_type
        self._administrative = self.administrative
        self._invprovision = self.invprovision
        self._operational = self.operational
        self._availability = self.availability
        self._capabilities = self.capabilities
        self._ttys_dcd = self.ttys_dcd
        self._pers_subtype = self.capabilities.get('pers_subtype', "")
        self.patch_current = "N/A"
        self.requires_reboot = "N/A"
        self.allow_insvc_patching = True
        self._patch_state = patch_constants.PATCH_AGENT_STATE_IDLE

        self._install_state = self.install_state
        if self._install_state is not None:
            self._install_state = self._install_state.strip("+")

    @property
    def personality(self):
        # Override controller personality to retrieve
        # the current activity state which
        # is reported in the hosts location field
        if (self._personality == PERSONALITY_CONTROLLER):
            if (self._capabilities['Personality'] == 'Controller-Active'):
                return _('Controller-Active')
            else:
                return _('Controller-Standby')
        return self._get_display_value(self.PERSONALITY_DISPLAY_CHOICES,
                                       self._personality)

    @property
    def additional_subfunctions(self):
        return len(self._subfunctions.split(',')) > 1

    @property
    def is_cpe(self):
        subfunctions = self._subfunctions.split(',')
        if PERSONALITY_CONTROLLER in subfunctions and \
                PERSONALITY_COMPUTE in subfunctions:
            return True
        else:
            return False

    @property
    def subfunctions(self):
        return self._subfunctions.split(',')

    @property
    def subfunction_oper(self):
        return self._get_display_value(self.OPER_DISPLAY_CHOICES,
                                       self._subfunction_oper)

    @property
    def subfunction_avail(self):
        return self._get_display_value(self.AVAIL_DISPLAY_CHOICES,
                                       self._subfunction_avail)

    @property
    def compute_config_required(self):
        return self.config_status == 'Compute config required'

    @property
    def location(self):
        if hasattr(self._location, 'locn'):
            return self._location.locn
        if 'locn' in self._location:
            return self._location['locn']
        else:
            return ''

    @property
    def peers(self):
        if hasattr(self._peers, 'name'):
            return self._peers.name
        if self._peers and 'name' in self._peers:
            return self._peers['name']
        else:
            return ''

    @property
    def boottime(self):
        return datetime.datetime.now() - datetime.timedelta(
            seconds=self.uptime)

    @property
    def administrative(self):
        return self._get_display_value(self.ADMIN_DISPLAY_CHOICES,
                                       self._administrative)

    @property
    def operational(self):
        return self._get_display_value(self.OPER_DISPLAY_CHOICES,
                                       self._operational)

    @property
    def availability(self):
        return self._get_display_value(self.AVAIL_DISPLAY_CHOICES,
                                       self._availability)

    @property
    def bm_type(self):
        bm_type = self._bm_type
        if bm_type and not bm_type.lower().startswith(BM_TYPE_NONE):
            bm_type = BM_TYPE_GENERIC
        else:
            bm_type = BM_TYPE_NULL

        return bm_type

    @property
    def ttys_dcd(self):
        return self._ttys_dcd == 'True'

    @property
    def patch_state(self):
        return self._get_display_value(self.PATCH_STATE_DISPLAY_CHOICES,
                                       self._patch_state)

    @property
    def pers_subtype(self):
        return self._get_display_value(self.SUBTYPE_CHOICES,
                                       self._pers_subtype)

    @property
    def install_state(self):
        return self._get_display_value(self.INSTALL_STATE_DISPLAY_CHOICES,
                                       self._install_state)

    def _get_display_value(self, display_choices, data):
        """Lookup the display value in the provided dictionary."""
        display_value = [display for (value, display) in display_choices
                         if value.lower() == (data or '').lower()]

        if display_value:
            return display_value[0]
        return None


class AlarmSummary(base.APIResourceWrapper):
    """Wrapper for Inventory Alarm Summaries"""

    _attrs = ['system_uuid',
              'warnings',
              'minor',
              'major',
              'critical',
              'status']

    def __init__(self, apiresource):
        super(AlarmSummary, self).__init__(apiresource)


def alarm_summary_get(request, include_suppress=False):
    summary = cgtsclient(request).ialarm.summary(
        include_suppress=include_suppress)
    if len(summary) > 0:
        return AlarmSummary(summary[0])
    return None


class Alarm(base.APIResourceWrapper):
    """Wrapper for Inventory Alarms"""

    _attrs = ['uuid',
              'alarm_id',
              'alarm_state',
              'entity_type_id',
              'entity_instance_id',
              'timestamp',
              'severity',
              'reason_text',
              'alarm_type',
              'probable_cause',
              'proposed_repair_action',
              'service_affecting',
              'suppression_status',
              'mgmt_affecting']

    def __init__(self, apiresource):
        super(Alarm, self).__init__(apiresource)


def alarm_list(request, search_opts=None):
    paginate = False
    include_suppress = False

    if search_opts is None:
        search_opts = {}

    limit = search_opts.get('limit', None)
    marker = search_opts.get('marker', None)
    sort_key = search_opts.get('sort_key', None)
    sort_dir = search_opts.get('sort_dir', None)
    page_size = base.get_request_page_size(request, limit)

    if "suppression" in search_opts:
        suppression = search_opts.pop('suppression')

        if suppression == FM_SUPPRESS_SHOW:
            include_suppress = True
        elif suppression == FM_SUPPRESS_HIDE:
            include_suppress = False

    if 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            limit = page_size + 1

    alarms = cgtsclient(request).ialarm.list(
        limit=limit, marker=marker, sort_key=sort_key, sort_dir=sort_dir,
        include_suppress=include_suppress)

    has_more_data = False
    if paginate and len(alarms) > page_size:
        alarms.pop(-1)
        has_more_data = True
    elif paginate and len(alarms) > getattr(settings,
                                            'API_RESULT_LIMIT', 1000):
        has_more_data = True

    if paginate:
        return [Alarm(n) for n in alarms], has_more_data
    else:
        return [Alarm(n) for n in alarms]


def alarm_get(request, alarm_id):
    alarm = cgtsclient(request).ialarm.get(alarm_id)
    if not alarm:
        raise ValueError('No match found for alarm_id "%s".' % alarm_id)
    return Alarm(alarm)


def system_list(request):
    systems = cgtsclient(request).isystem.list()
    return [System(n) for n in systems]


def system_get(request):
    system = cgtsclient(request).isystem.list()[0]
    if not system:
        raise ValueError('No system found.')
    return System(system)


def system_update(request, system_id, **kwargs):
    LOG.debug("system_update(): system_id=%s, kwargs=%s", system_id, kwargs)
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isystem.update(system_id, mypatch)


def host_create(request, **kwargs):
    LOG.debug("host_create(): kwargs=%s", kwargs)
    host = cgtsclient(request).ihost.create(**kwargs)
    return Host(host)


def host_update(request, host_id, **kwargs):
    LOG.debug("host_update(): host_id=%s, kwargs=%s", host_id, kwargs)
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).ihost.update(host_id, mypatch)


def host_apply_profile(request, host_id, profile_uuid):
    LOG.debug("host_apply_profile(): host_id=%s, profile_uuid=%s",
              host_id, profile_uuid)

    kwargs = {}
    kwargs['action'] = 'apply-profile'
    kwargs['iprofile_uuid'] = profile_uuid

    host = host_update(request, host_id, **kwargs)
    return host


def host_delete(request, host_id):
    LOG.debug("host_delete(): host_id=%s", host_id)
    return cgtsclient(request).ihost.delete(host_id)


def host_lock(request, host_id):
    kwargs = {'action': 'lock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_force_lock(request, host_id):
    kwargs = {'action': 'force-lock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_unlock(request, host_id):
    kwargs = {'action': 'unlock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_force_unlock(request, host_id):
    kwargs = {'action': 'force-unlock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reboot(request, host_id):
    kwargs = {'action': 'reboot'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reset(request, host_id):
    kwargs = {'action': 'reset'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reinstall(request, host_id):
    kwargs = {'action': 'reinstall'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_power_on(request, host_id):
    kwargs = {'action': 'power-on'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_power_off(request, host_id):
    kwargs = {'action': 'power-off'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_swact(request, host_id):
    kwargs = {'action': 'swact'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_get(request, host_id):
    host = cgtsclient(request).ihost.get(host_id)
    if not host:
        raise ValueError('No match found for host_id "%s".' % host_id)
    return Host(host)


def host_list(request):
    hosts = cgtsclient(request).ihost.list()
    return [Host(n) for n in hosts]


class DNS(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'nameservers', 'uuid', 'link']

    def __init__(self, apiresource):
        super(DNS, self).__init__(apiresource)


def dns_update(request, dns_id, **kwargs):
    LOG.debug("dns_update(): dns_id=%s, kwargs=%s", dns_id, kwargs)
    mypatch = []

    for key, value in kwargs.iteritems():
        if key == 'nameservers' and not value:
            value = 'NC'
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    return cgtsclient(request).idns.update(dns_id, mypatch)


def dns_delete(request, dns_id):
    LOG.debug("dns_delete(): dns_id=%s", dns_id)
    return cgtsclient(request).idns.delete(dns_id)


def dns_get(request, dns_id):
    dns = cgtsclient(request).idns.get(dns_id)
    if not dns:
        raise ValueError('No match found for dns_id "%s".' % dns_id)
    return DNS(dns)


def dns_list(request):
    dns = cgtsclient(request).idns.list()
    return [DNS(n) for n in dns]


class NTP(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'ntpservers', 'uuid', 'link']

    def __init__(self, apiresource):
        super(NTP, self).__init__(apiresource)


def ntp_update(request, ntp_id, **kwargs):
    LOG.debug("ntp_update(): ntp_id=%s, kwargs=%s", ntp_id, kwargs)
    mypatch = []

    for key, value in kwargs.iteritems():
        if key == 'ntpservers' and not value:
            value = 'NC'
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    return cgtsclient(request).intp.update(ntp_id, mypatch)


def ntp_delete(request, ntp_id):
    LOG.debug("ntp_delete(): ntp_id=%s", ntp_id)
    return cgtsclient(request).intp.delete(ntp_id)


def ntp_get(request, ntp_id):
    ntp = cgtsclient(request).intp.get(ntp_id)
    if not ntp:
        raise ValueError('No match found for ntp_id "%s".' % ntp_id)
    return NTP(ntp)


def ntp_list(request):
    ntp = cgtsclient(request).intp.list()
    return [NTP(n) for n in ntp]


class EXTOAM(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'oam_subnet', 'oam_gateway_ip',
              'oam_floating_ip', 'oam_c0_ip', 'oam_c1_ip',
              'oam_start_ip', 'oam_end_ip',
              'uuid', 'link', 'region_config']

    def __init__(self, apiresource):
        super(EXTOAM, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._oam_subnet = self.oam_subnet
            self._oam_gateway_ip = self.oam_gateway_ip
            self._oam_floating_ip = self.oam_floating_ip
            self._oam_c0_ip = self.oam_c0_ip
            self._oam_c1_ip = self.oam_c1_ip

            self._region_config = self.region_config
            self._oam_start_ip = self.oam_start_ip or ""
            self._oam_end_ip = self.oam_end_ip or ""
        else:
            self._oam_subnet = None
            self._oam_gateway_ip = None
            self._oam_floating_ip = None
            self._oam_c0_ip = None
            self._oam_c1_ip = None

            self._region_config = None
            self._oam_start_ip = None
            self._oam_end_ip = None

    @property
    def oam_subnet(self):
        return self._oam_subnet

    @property
    def oam_gateway_ip(self):
        return self._oam_gateway_ip

    @property
    def oam_floating_ip(self):
        return self._oam_floating_ip

    @property
    def oam_c0_ip(self):
        return self._oam_c0_ip

    @property
    def oam_c1_ip(self):
        return self._oam_c1_ip

    @property
    def region_config(self):
        return self._region_config

    @property
    def oam_start_ip(self):
        return self._oam_start_ip or ""

    @property
    def oam_end_ip(self):
        return self._oam_end_ip or ""


def extoam_update(request, extoam_id, **kwargs):
    LOG.debug("extoam_update(): extoam_id=%s, kwargs=%s", extoam_id, kwargs)
    # print 'THIS IS IN SYSINV UPDATE: ', kwargs
    mypatch = []
    # print "\nThis is the dns_id: ", dns_id, "\n"
    # print "\nThese are the values in sysinv dns_update: ", kwargs, "\n"
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).iextoam.update(extoam_id, mypatch)


def extoam_delete(request, extoam_id):
    LOG.debug("extoam_delete(): extoam_id=%s", extoam_id)
    return cgtsclient(request).iextoam.delete(extoam_id)


def extoam_get(request, extoam_id):
    extoam = cgtsclient(request).iextoam.get(extoam_id)
    # print "THIS IS SYSNINV GET"
    if not extoam:
        raise ValueError('No match found for extoam_id "%s".' % extoam_id)
    return EXTOAM(extoam)


def extoam_list(request):
    extoam = cgtsclient(request).iextoam.list()
    # print "THIS IS SYSINV LIST"
    return [EXTOAM(n) for n in extoam]


class Cluster(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'cluster_uuid', 'type', 'name']

    def __init__(self, apiresource):
        super(Cluster, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._uuid = self.uuid
            self._name = self.name
            self._type = self.type
            self._cluster_uuid = self.cluster_uuid
        else:
            self._uuid = None
            self._name = None
            self._type = None
            self._cluster_uuid = None

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def cluster_uuid(self):
        return self._cluster_uuid


def cluster_list(request):
    clusters = cgtsclient(request).cluster.list()

    return [Cluster(n) for n in clusters]


class StorageTier(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'name', 'type', 'status']

    def __init__(self, apiresource):
        super(StorageTier, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._uuid = self.uuid
            self._name = self.name
            self._type = self.type
            self._status = self.status
        else:
            self._uuid = None
            self._name = None
            self._type = None
            self._status = None

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def status(self):
        return self._status


class StorageCeph(base.APIResourceWrapper):
    """..."""

    _attrs = ['cinder_pool_gib', 'glance_pool_gib', 'ephemeral_pool_gib',
              'object_pool_gib', 'object_gateway', 'uuid', 'tier_name', 'link',
              'ceph_total_space_gib']

    def __init__(self, apiresource):
        super(StorageCeph, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._tier_name = self.tier_name
            self._cinder_pool_gib = self.cinder_pool_gib
            self._glance_pool_gib = self.glance_pool_gib
            self._ephemeral_pool_gib = self.ephemeral_pool_gib
            self._object_pool_gib = self.object_pool_gib
            self._object_gateway = self.object_gateway
            self._ceph_total_space_gib = self.ceph_total_space_gib
        else:
            self._tier_name = None
            self._cinder_pool_gib = None
            self._glance_pool_gib = None
            self._ephemeral_pool_gib = None
            self._object_pool_gib = None
            self._object_gateway = None
            self._ceph_total_space_gib = None

    @property
    def tier_name(self):
        return self._tier_name

    @property
    def cinder_pool_gib(self):
        return self._cinder_pool_gib

    @property
    def glance_pool_gib(self):
        return self._glance_pool_gib

    @property
    def ephemeral_pool_gib(self):
        return self._ephemeral_pool_gib

    @property
    def object_pool_gib(self):
        return self._object_pool_gib

    @property
    def object_gateway(self):
        return self._object_gateway

    @property
    def ceph_total_space_gib(self):
        return self._ceph_total_space_gib


class StorageBackend(base.APIResourceWrapper):
    """..."""
    _attrs = ['isystem_uuid', 'name', 'backend',
              'state', 'task', 'uuid', 'link']

    def __init__(self, apiresource):
        super(StorageBackend, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._name = self.name
            self._backend = self.backend
            self._state = self.state
            self._task = self.task
        else:
            self._backend = None
            self._state = None
            self._task = None

    @property
    def name(self):
        return self._name

    @property
    def backend(self):
        return self._backend

    @property
    def state(self):
        return self._state

    @property
    def task(self):
        return self._task


class ControllerFS(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'link', 'name', 'size', 'logical_volume', 'replicated',
              'device_path', 'ceph_mon_gib', 'hostname']

    def __init__(self, apiresource):
        super(ControllerFS, self).__init__(apiresource)

        if hasattr(self, 'ceph_mon_gib'):
            self._size = self.ceph_mon_gib
            self._name = 'ceph-mon'
            self._logical_volume = None
            self._replicated = None
            self._uuid = self.uuid

        else:
            self._uuid = self.uuid
            self._name = self.name
            self._logical_volume = self.logical_volume
            self._size = self.size
            self._replicated = self.replicated

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def logical_volume(self):
        return self._logical_volume

    @property
    def size(self):
        return self._size

    @property
    def replicated(self):
        return self._replicated


class CephMon(base.APIResourceWrapper):
    """..."""
    _attrs = ['device_path', 'ceph_mon_gib', 'hostname', 'uuid', 'link']

    def __init__(self, apiresource):
        super(CephMon, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._device_path = self.device_path
            self._ceph_mon_gib = self.ceph_mon_gib
            self._hostname = self.hostname
        else:
            self._device_path = None
            self._ceph_mon_gib = None
            self._hostname = None

    @property
    def device_path(self):
        return self._device_path

    @property
    def ceph_mon_gib(self):
        return self._ceph_mon_gib

    @property
    def hostname(self):
        return self._hostname


class STORAGE(base.APIResourceWrapper):
    """..."""
    _attrs = ['isystem_uuid', 'backup_gib', 'scratch_gib', 'cgcs_gib',
              'img_conversions_gib', 'database_gib', 'uuid', 'link']

    def __init__(self, controller_fs, ceph_mon):
        if controller_fs:
            super(STORAGE, self).__init__(controller_fs)

        self._backup_gib = None
        self._scratch_gib = None
        self._cgcs_gib = None
        self._img_conversions_gib = None
        self._database_gib = None
        self._ceph_mon_gib = None

        if hasattr(self, 'uuid'):
            if controller_fs:
                self._backup_gib = controller_fs.backup_gib
                self._scratch_gib = controller_fs.scratch_gib
                self._cgcs_gib = controller_fs.cgcs_gib
                self._img_conversions_gib = controller_fs.img_conversions_gib
                self._database_gib = controller_fs.database_gib

            if ceph_mon:
                self._device_path = ceph_mon.device_path
                self._ceph_mon_gib = ceph_mon.ceph_mon_gib
                self._hostname = ceph_mon.hostname

    @property
    def backup_gib(self):
        return self._backup_gib

    @property
    def scratch_gib(self):
        return self._scratch_gib

    @property
    def cgcs_gib(self):
        return self._cgcs_gib

    @property
    def database_gib(self):
        return self._database_gib

    @property
    def img_conversions_gib(self):
        return self._img_conversions_gib

    @property
    def ceph_mon_gib(self):
        return self._ceph_mon_gib


def storfs_update(request, controller_fs_id, **kwargs):
    LOG.info("Updating controller fs storage with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.iteritems():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).controller_fs.update(controller_fs_id, my_patch)


def storfs_update_many(request, system_uuid, **kwargs):
    LOG.info("Updating controller fs storage with kwargs=%s", kwargs)

    patch_list = []

    for key, value in kwargs.iteritems():
        patch = []
        patch.append({'op': 'replace', 'path': '/name', 'value': key})
        patch.append({'op': 'replace', 'path': '/size', 'value': value})
        patch_list.append(patch)

    return cgtsclient(request).controller_fs.update_many(system_uuid,
                                                         patch_list)


def ceph_mon_update(request, ceph_mon_id, **kwargs):
    LOG.info("Updating ceph-mon storage with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.iteritems():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).ceph_mon.update(ceph_mon_id, my_patch)


def storpool_update(request, storage_ceph_id, **kwargs):
    LOG.info("Updating storage pool with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.iteritems():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).storage_ceph.update(storage_ceph_id,
                                                   my_patch)


def controllerfs_get(request, name):
    fs_list = controllerfs_list(request)
    for controller_fs in fs_list:
        if controller_fs.name == name:
            return ControllerFS(controller_fs)

    raise ValueError(
        'No match found for filesystem with name "%s".' % name)


def cephmon_get(request, host_id=None):
    cephmon = cgtsclient(request).ceph_mon.list(host_id)
    if not cephmon:
        return None
    return CephMon(cephmon[0])


def storagepool_get(request, storceph_id=None):
    storceph = cgtsclient(request).storage_ceph.get(storceph_id)
    if not storceph:
        return None
    return StorageCeph(storceph)


def cephmon_list(request):
    ceph_mons = cgtsclient(request).ceph_mon.list()
    if not ceph_mons:
        return None
    return [CephMon(n) for n in ceph_mons]


def storagepool_list(request):
    storage_pools = cgtsclient(request).storage_ceph.list()
    if not storage_pools:
        return None
    return [StorageCeph(n) for n in storage_pools]


def storagefs_list(request):
    # Obtain the storage data from controller_fs and ceph_mon.
    ceph_mon_list = cgtsclient(request).ceph_mon.list()

    # Verify if the results are None and if not, extract the first object.
    # - controller_fs is a one row tables, so the first
    # element of the list is also the only one.
    # - ceph_mon has the ceph_mon_gib field identical for all the entries,
    # so the first element is enough for obtaining the needed data.

    controllerfs_obj = None
    ceph_mon_obj = None

    if ceph_mon_list:
        ceph_mon_obj = ceph_mon_list[0]

    return [STORAGE(controllerfs_obj, ceph_mon_obj)]


def controllerfs_list(request):
    controllerfs = cgtsclient(request).controller_fs.list()
    ceph_mon_list = cgtsclient(request).ceph_mon.list()

    if ceph_mon_list and not is_system_mode_simplex(request):
        controllerfs.append(ceph_mon_list[0])

    return [ControllerFS(n) for n in controllerfs]


def storage_tier_list(request, cluster_id):
    storage_tiers = cgtsclient(request).storage_tier.list(cluster_id)

    return [StorageTier(n) for n in storage_tiers]


def storage_backend_list(request):
    backends = cgtsclient(request).storage_backend.list()

    return [StorageBackend(n) for n in backends]


def storage_usage_list(request):
    ulist = cgtsclient(request).storage_backend.usage()
    return ulist


def get_cinder_backend(request):
    storage_list = storage_backend_list(request)
    cinder_backends = []

    if storage_list:
        for storage in storage_list:
            if hasattr(storage, 'backend'):
                cinder_backends.append(storage.backend)

    return cinder_backends


def host_node_list(request, host_id):
    nodes = cgtsclient(request).inode.list(host_id)
    return [Node(n) for n in nodes]


def host_node_get(request, node_id):
    node = cgtsclient(request).inode.get(node_id)
    if not node:
        raise ValueError('No match found for node_id "%s".' % node_id)
    return Node(node)


def host_cpu_list(request, host_id):
    cpus = cgtsclient(request).icpu.list(host_id)
    return [Cpu(n) for n in cpus]


def _update_cpu_capability(cpu_data):
    capability = {'function': cpu_data.get('function')}
    sockets = []
    for k, v in cpu_data.items():
        if k.startswith('num_cores_on_processor'):
            sockets.append({k.strip('num_cores_on_processor'): v})

    capability.update({'sockets': sockets})
    LOG.info("_update_cpu_capability=%s", capability)
    return capability


def host_cpus_modify(request, host_uuid,
                     platform_cpu_data,
                     vswitch_cpu_data,
                     shared_cpu_data):

    capabilities = []
    if platform_cpu_data:
        capability = _update_cpu_capability(platform_cpu_data)
        capabilities.append(capability)
    if vswitch_cpu_data:
        capability = _update_cpu_capability(vswitch_cpu_data)
        capabilities.append(capability)
    if shared_cpu_data:
        capability = _update_cpu_capability(shared_cpu_data)
        capabilities.append(capability)

    LOG.info("host_cpus_modify host_uuid=%s capabilities=%s",
             host_uuid, capabilities)

    return cgtsclient(request).ihost.host_cpus_modify(host_uuid, capabilities)


def host_cpu_update(request, cpu_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).icpu.update(cpu_id, mypatch)


def host_memory_list(request, host_id):
    memorys = cgtsclient(request).imemory.list(host_id)
    return [Memory(n) for n in memorys]


def host_memory_get(request, memory_id):
    memory = cgtsclient(request).imemory.get(memory_id)
    if not memory:
        raise ValueError('No match found for memory_id "%s".' % memory_id)
    return Memory(memory)


def host_memory_update(request, memory_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).imemory.update(memory_id, mypatch)


def host_port_list(request, host_id):
    ports = cgtsclient(request).ethernet_port.list(host_id)
    return [Port(n) for n in ports]


def host_port_get(request, port_id):
    port = cgtsclient(request).ethernet_port.get(port_id)
    if not port:
        raise ValueError('No match found for port_id "%s".' % port_id)
    return Port(port)


def host_port_update(request, port_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).ethernet_port.update(port_id, mypatch)


def host_disk_list(request, host_id):
    disks = cgtsclient(request).idisk.list(host_id)
    return [Disk(n) for n in disks]


def host_disk_get(request, disk_id):
    disk = cgtsclient(request).idisk.get(disk_id)
    if not disk:
        raise ValueError('No match found for disk_id "%s".' % disk_id)
    return Disk(disk)


def host_stor_list(request, host_id):
    volumes = cgtsclient(request).istor.list(host_id)
    return [StorageVolume(n) for n in volumes]


def host_stor_get(request, stor_id):
    volume = cgtsclient(request).istor.get(stor_id)
    if not volume:
        raise ValueError('No match found for stor_id "%s".' % stor_id)
    return StorageVolume(volume)


def host_stor_create(request, **kwargs):
    stor = cgtsclient(request).istor.create(**kwargs)
    return StorageVolume(stor)


def host_stor_delete(request, stor_id):
    return cgtsclient(request).istor.delete(stor_id)


def host_stor_update(request, stor_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    stor = cgtsclient(request).istor.update(stor_id, mypatch)
    return StorageVolume(stor)


def host_stor_get_by_function(request, host_id, function=None):
    volumes = cgtsclient(request).istor.list(host_id)

    if function:
        volumes = [v for v in volumes if v.function == function]

    return [StorageVolume(n) for n in volumes]


class Interface(base.APIResourceWrapper):
    """Wrapper for Inventory Interfaces"""

    _attrs = ['id', 'uuid', 'ifname', 'iftype', 'imtu', 'imac', 'networktype',
              'aemode', 'txhashpolicy', 'vlan_id', 'uses', 'used_by',
              'ihost_uuid', 'providernetworks',
              'ipv4_mode', 'ipv6_mode', 'ipv4_pool', 'ipv6_pool',
              'sriov_numvfs']

    def __init__(self, apiresource):
        super(Interface, self).__init__(apiresource)
        if not self.ifname:
            self.ifname = '(' + str(self.uuid)[-8:] + ')'


def host_interface_list(request, host_id):
    interfaces = cgtsclient(request).iinterface.list(host_id)
    return [Interface(n) for n in interfaces]


def host_interface_get(request, interface_id):
    interface = cgtsclient(request).iinterface.get(interface_id)
    if not interface:
        raise ValueError(
            'No match found for interface_id "%s".' % interface_id)
    return Interface(interface)


def host_interface_create(request, **kwargs):
    interface = cgtsclient(request).iinterface.create(**kwargs)
    return Interface(interface)


def host_interface_update(request, interface_id, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).iinterface.update(interface_id, mypatch)


def host_interface_delete(request, interface_id):
    return cgtsclient(request).iinterface.delete(interface_id)


class Address(base.APIResourceWrapper):
    """Wrapper for Inventory Addresses"""

    _attrs = ['uuid', 'interface_uuid', 'address', 'prefix', 'enable_dad']

    def __init__(self, apiresource):
        super(Address, self).__init__(apiresource)


def address_list_by_interface(request, interface_id):
    addresses = cgtsclient(request).address.list_by_interface(interface_id)
    return [Address(n) for n in addresses]


def address_get(request, address_uuid):
    address = cgtsclient(request).address.get(address_uuid)
    if not address:
        raise ValueError(
            'No match found for address uuid "%s".' % address_uuid)
    return Address(address)


def address_create(request, **kwargs):
    address = cgtsclient(request).address.create(**kwargs)
    return Address(address)


def address_delete(request, address_uuid):
    return cgtsclient(request).address.delete(address_uuid)


class AddressPool(base.APIResourceWrapper):
    """Wrapper for Inventory Address Pools"""

    _attrs = ['uuid', 'name', 'network', 'prefix', 'order', 'ranges']

    def __init__(self, apiresource):
        super(AddressPool, self).__init__(apiresource)


def address_pool_list(request):
    pools = cgtsclient(request).address_pool.list()
    return [AddressPool(p) for p in pools]


def address_pool_get(request, address_pool_uuid):
    pool = cgtsclient(request).address_pool.get(address_pool_uuid)
    if not pool:
        raise ValueError(
            'No match found for address pool uuid "%s".' % address_pool_uuid)
    return AddressPool(pool)


def address_pool_create(request, **kwargs):
    pool = cgtsclient(request).address_pool.create(**kwargs)
    return AddressPool(pool)


def address_pool_delete(request, address_pool_uuid):
    return cgtsclient(request).address_pool.delete(address_pool_uuid)


def address_pool_update(request, address_pool_uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).address_pool.update(address_pool_uuid, mypatch)


class Route(base.APIResourceWrapper):
    """Wrapper for Inventory Routers"""

    _attrs = ['uuid', 'interface_uuid', 'network',
              'prefix', 'gateway', 'metric']

    def __init__(self, apiresource):
        super(Route, self).__init__(apiresource)


def route_list_by_interface(request, interface_id):
    routees = cgtsclient(request).route.list_by_interface(interface_id)
    return [Route(n) for n in routees]


def route_get(request, route_uuid):
    route = cgtsclient(request).route.get(route_uuid)
    if not route:
        raise ValueError(
            'No match found for route uuid "%s".' % route_uuid)
    return Route(route)


def route_create(request, **kwargs):
    route = cgtsclient(request).route.create(**kwargs)
    return Route(route)


def route_delete(request, route_uuid):
    return cgtsclient(request).route.delete(route_uuid)


class BaseProfile(base.APIResourceWrapper):
    """Base Wrapper class for Profiles"""

    def __init__(self, request, apiresource):
        super(BaseProfile, self).__init__(apiresource)
        # load dependent data if required
        self._load_data(request)

    def _load_data(self, request):
        """stub function for loading additional data"""
        pass


class InterfaceProfile(BaseProfile):
    """Wrapper for Inventory Interface Profile"""

    _attrs = ['uuid', 'profilename', 'ports', 'interfaces']

    def __init__(self, request, apiresource):
        super(InterfaceProfile, self).__init__(request, apiresource)

        self.ports = [Port(n) for n in self.ports]
        self.interfaces = [Interface(n) for n in self.interfaces]

        for p in self.ports:
            p.namedisplay = p.get_port_display_name()

        for i in self.interfaces:
            i.ports = [p.get_port_display_name() for p in self.ports if
                       p.interface_uuid and p.interface_uuid == i.uuid]
            i.ports = ", ".join(i.ports)


class InterfaceProfileFragmentary(InterfaceProfile):
    def _load_data(self, request):
        self.ports = \
            cgtsclient(request).iprofile.list_ethernet_port(self.uuid)
        self.interfaces = \
            cgtsclient(request).iprofile.list_iinterface(self.uuid)


def host_interfaceprofile_list(request):
    profiles = cgtsclient(request).iprofile.list_interface_profiles()
    return [InterfaceProfile(request, n) for n in profiles]


def host_interfaceprofile_create(request, **kwargs):
    host_id = kwargs['host_id']
    del kwargs['host_id']

    ihost = cgtsclient(request).ihost.get(host_id)
    kwargs['ihost_uuid'] = ihost.uuid

    kwargs['profiletype'] = 'if'

    # create new if profile
    iprofile = cgtsclient(request).iprofile.create(**kwargs)
    return InterfaceProfileFragmentary(request, iprofile)


def host_interfaceprofile_delete(request, iprofile_uuid):
    return cgtsclient(request).iprofile.delete(iprofile_uuid)


class CpuProfile(BaseProfile):
    """Wrapper for Inventory Cpu Profiles"""

    _attrs = ['uuid', 'profilename', 'cpus', 'nodes']

    def __init__(self, request, apiresource):
        super(CpuProfile, self).__init__(request, apiresource)

        self.cpus = [Cpu(n) for n in self.cpus]
        self.nodes = [Node(n) for n in self.nodes]

        icpu_utils.restructure_host_cpu_data(self)


class CpuProfileFragmentary(CpuProfile):
    def _load_data(self, request):
        self.cpus = cgtsclient(request).iprofile.list_icpus(self.uuid)
        self.nodes = cgtsclient(request).iprofile.list_inodes(self.uuid)


def host_cpuprofile_list(request):
    profiles = cgtsclient(request).iprofile.list_cpu_profiles()
    return [CpuProfile(request, n) for n in profiles]


def host_cpuprofile_create(request, **kwargs):
    host_id = kwargs['host_id']
    del kwargs['host_id']

    ihost = cgtsclient(request).ihost.get(host_id)
    kwargs['ihost_uuid'] = ihost.uuid

    kwargs['profiletype'] = 'cpu'

    # create new cpu profile
    iprofile = cgtsclient(request).iprofile.create(**kwargs)
    return CpuProfileFragmentary(request, iprofile)


def host_cpuprofile_delete(request, iprofile_uuid):
    return cgtsclient(request).iprofile.delete(iprofile_uuid)


#
# DISK PROFILES
#

# Most of the work happens in the cgts-client package
# to avoid code duplicated in GUI and CLI

class DiskProfile(BaseProfile):
    """Wrapper for Inventory Disk Profiles"""

    _attrs = ['uuid', 'profilename', 'disks', 'partitions', 'stors', 'lvgs',
              'pvs']

    def __init__(self, request, apiresource):
        super(DiskProfile, self).__init__(request, apiresource)

        self.disks = [Disk(n) for n in self.disks]
        self.partitions = [Partition(n) for n in self.partitions]
        self.stors = [StorageVolume(n) for n in self.stors]
        self.pvs = [PhysicalVolume(n) for n in self.pvs]
        self.lvgs = [LocalVolumeGroup(n) for n in self.lvgs]

        for lvg in self.lvgs:
            lvg.params = host_lvg_get_params(request, lvg.uuid, False, lvg)


class DiskProfileFragmentary(DiskProfile):
    def _load_data(self, request):
        self.disks = cgtsclient(request).iprofile.list_idisks(self.uuid)
        self.partitions = cgtsclient(request).iprofile.list_partitions(
            self.uuid)
        self.stors = cgtsclient(request).iprofile.list_istors(self.uuid)
        self.pvs = cgtsclient(request).iprofile.list_ipvs(self.uuid)
        self.lvgs = cgtsclient(request).iprofile.list_ilvgs(self.uuid)


def host_diskprofile_list(request):
    profiles = cgtsclient(request).iprofile.list_storage_profiles()
    return [DiskProfile(request, n) for n in profiles]


def host_diskprofile_create(request, **kwargs):
    host_id = kwargs['host_id']
    del kwargs['host_id']

    ihost = cgtsclient(request).ihost.get(host_id)
    kwargs['ihost_uuid'] = ihost.uuid

    kwargs['profiletype'] = 'stor'

    # create new stor profile
    iprofile = cgtsclient(request).iprofile.create(**kwargs)
    return DiskProfileFragmentary(request, iprofile)


def host_diskprofile_delete(request, iprofile_uuid):
    return cgtsclient(request).iprofile.delete(iprofile_uuid)


class MemoryProfile(BaseProfile):
    """Wrapper for Inventory Memory Profiles"""

    _attrs = ['uuid', 'profilename', 'memory', 'nodes']

    def __init__(self, request, apiresource):
        super(MemoryProfile, self).__init__(request, apiresource)

        self.memory = [Memory(n) for n in self.memory]
        self.nodes = [Node(n) for n in self.nodes]


class MemoryProfileFragmentary(MemoryProfile):
    def _load_data(self, request):
        self.memory = cgtsclient(request).iprofile.list_imemorys(self.uuid)
        self.nodes = cgtsclient(request).iprofile.list_inodes(self.uuid)


def host_memprofile_list(request):
    profiles = cgtsclient(request).iprofile.list_memory_profiles()
    return [MemoryProfile(request, n) for n in profiles]


def host_memprofile_create(request, **kwargs):
    host_id = kwargs['host_id']
    del kwargs['host_id']

    ihost = cgtsclient(request).ihost.get(host_id)
    kwargs['ihost_uuid'] = ihost.uuid

    kwargs['profiletype'] = 'memory'

    # create new memory profile
    iprofile = cgtsclient(request).iprofile.create(**kwargs)
    return MemoryProfileFragmentary(request, iprofile)


def host_memprofile_delete(request, iprofile_uuid):
    return cgtsclient(request).iprofile.delete(iprofile_uuid)


class EventLog(base.APIResourceWrapper):
    """Wrapper for Inventory Customer Logs"""

    _attrs = ['uuid',
              'event_log_id',
              'state',
              'entity_type_id',
              'entity_instance_id',
              'timestamp',
              'severity',
              'reason_text',
              'event_log_type',
              'probable_cause',
              'proposed_repair_action',
              'service_affecting',
              'suppression',
              'suppression_status']

    def __init__(self, apiresource):
        super(EventLog, self).__init__(apiresource)


def event_log_list(request, search_opts=None):
    paginate = False
    if search_opts is None:
        search_opts = {}

    limit = search_opts.get('limit', None)
    marker = search_opts.get('marker', None)
    page_size = base.get_request_page_size(request, limit)

    if 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            limit = page_size + 1

    query = None
    alarms = False
    logs = False
    include_suppress = False

    if "evtType" in search_opts:
        evtType = search_opts.pop('evtType')
        if evtType == FM_ALARM:
            alarms = True
        elif evtType == FM_LOG:
            logs = True

    if "suppression" in search_opts:
        suppression = search_opts.pop('suppression')

        if suppression == FM_SUPPRESS_SHOW:
            include_suppress = True
        elif suppression == FM_SUPPRESS_HIDE:
            include_suppress = False

    logs = cgtsclient(request)\
        .event_log.list(q=query,
                        limit=limit,
                        marker=marker,
                        alarms=alarms,
                        logs=logs,
                        include_suppress=include_suppress)

    has_more_data = False
    if paginate and len(logs) > page_size:
        logs.pop(-1)
        has_more_data = True
    elif paginate and len(logs) > getattr(settings, 'API_RESULT_LIMIT', 1000):
        has_more_data = True

    return [EventLog(n) for n in logs], has_more_data


def event_log_get(request, event_log_id):
    log = cgtsclient(request).event_log.get(event_log_id)
    if not log:
        raise ValueError('No match found for event_log_id "%s".' %
                         event_log_id)
    return EventLog(log)


class EventSuppression(base.APIResourceWrapper):
    """Wrapper for Inventory Alarm Suppression"""

    _attrs = ['uuid',
              'alarm_id',
              'description',
              'suppression_status']

    def __init__(self, apiresource):
        super(EventSuppression, self).__init__(apiresource)


def event_suppression_list(request):

    suppression_list = cgtsclient(request).event_suppression.list()

    return [EventSuppression(n) for n in suppression_list]


def event_suppression_update(request, event_suppression_uuid, **kwargs):
    patch = []
    for key, value in kwargs.iteritems():
        patch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request)\
        .event_suppression.update(event_suppression_uuid, patch)


class Device(base.APIResourceWrapper):
    """Wrapper for Inventory Devices"""

    _attrs = ['uuid', 'name', 'pciaddr', 'host_uuid',
              'pclass_id', 'pvendor_id', 'pdevice_id',
              'pclass', 'pvendor', 'pdevice',
              'numa_node', 'enabled', 'extra_info',
              'sriov_totalvfs', 'sriov_numvfs', 'sriov_vfs_pci_address']

    def __init__(self, apiresource):
        super(Device, self).__init__(apiresource)
        if not self.name:
            self.name = '(' + str(self.uuid)[-8:] + ')'


def host_device_list(request, host_id):
    devices = cgtsclient(request).pci_device.list(host_id)
    return [Device(n) for n in devices]


def device_list_all(request):
    devices = cgtsclient(request).pci_device.list_all()
    return [Device(n) for n in devices]


def host_device_get(request, device_uuid):
    device = cgtsclient(request).pci_device.get(device_uuid)
    if device:
        return Device(device)
    raise ValueError('No match found for device "%s".' % device_uuid)


def host_device_update(request, device_uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).pci_device.update(device_uuid, mypatch)


class LldpNeighbour(base.APIResourceWrapper):
    """Wrapper for Inventory LLDP Neighbour"""

    _attrs = ['port_uuid',
              'port_name',
              'port_namedisplay',
              'uuid',
              'host_uuid',
              'msap',
              'chassis_id',
              'port_identifier',
              'port_description',
              'ttl',
              'system_name',
              'system_description',
              'system_capabilities',
              'management_address',
              'dot1_port_vid',
              'dot1_proto_vids',
              'dot1_vlan_names',
              'dot1_proto_ids',
              'dot1_vid_digest',
              'dot1_management_vid',
              'dot1_lag',
              'dot3_mac_status',
              'dot3_power_mdi',
              'dot3_max_frame']

    def __init__(self, apiresource):
        super(LldpNeighbour, self).__init__(apiresource)

    def get_local_port_display_name(self):
        if self.port_name:
            return self.port_name
        if self.port_namedisplay:
            return self.port_namedisplay
        else:
            return '(' + str(self.port_uuid)[-8:] + ')'


def host_lldpneighbour_list(request, host_uuid):
    neighbours = cgtsclient(request).lldp_neighbour.list(host_uuid)
    return [LldpNeighbour(n) for n in neighbours]


def host_lldpneighbour_get(request, neighbour_uuid):
    neighbour = cgtsclient(request).lldp_neighbour.get(neighbour_uuid)

    if not neighbour:
        raise ValueError('No match found for neighbour id "%s".' %
                         neighbour_uuid)
    return LldpNeighbour(neighbour)


def port_lldpneighbour_list(request, port_uuid):
    neighbours = cgtsclient(request).lldp_neighbour.list_by_port(port_uuid)
    return [LldpNeighbour(n) for n in neighbours]


class ServiceParameter(base.APIResourceWrapper):
    """Wrapper for Service Parameter configuration"""

    _attrs = ['uuid', 'service', 'section', 'name', 'value']

    def __init__(self, apiresource):
        super(ServiceParameter, self).__init__(apiresource)


def service_parameter_list(request):
    parameters = cgtsclient(request).service_parameter.list()
    return [ServiceParameter(n) for n in parameters]


class SDNController(base.APIResourceWrapper):
    """Wrapper for SDN Controller configuration"""

    _attrs = ['uuid', 'ip_address', 'port', 'transport', 'state',
              'created_at', 'updated_at']

    def __init__(self, apiresource):
        super(SDNController, self).__init__(apiresource)


def sdn_controller_list(request):
    controllers = cgtsclient(request).sdn_controller.list()
    return [SDNController(n) for n in controllers]


def sdn_controller_get(request, uuid):
    controller = cgtsclient(request).sdn_controller.get(uuid)

    if not controller:
        raise ValueError('No match found for SDN controller id "%s".' %
                         uuid)
    return SDNController(controller)


def sdn_controller_create(request, **kwargs):
    controller = cgtsclient(request).sdn_controller.create(**kwargs)
    return SDNController(controller)


def sdn_controller_update(request, uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.iteritems():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).sdn_controller.update(uuid, mypatch)


def sdn_controller_delete(request, uuid):
    return cgtsclient(request).sdn_controller.delete(uuid)


def get_sdn_enabled(request):
    # The SDN enabled flag is present in the Capabilities
    # of the system table, however capabilties is not exposed
    # as an attribute through system_list() or system_get()
    # at this level. We will therefore check the platform.conf
    # to see if SDN is configured.
    try:
        with open(PLATFORM_CONFIGURATION, 'r') as fd:
            content = fd.readlines()
        sdn_enabled = None
        for line in content:
            if 'sdn_enabled' in line:
                sdn_enabled = line
                break
        sdn_enabled = sdn_enabled.strip('\n').split('=', 1)
        return (sdn_enabled[1].lower() == 'yes')
    except Exception:
        return False


def get_sdn_l3_mode_enabled(request):
    # Get the Service Parameter list on this host
    # and ensure that the L3 Enabled service parameter
    # is set.
    try:
        allowed_vals = SERVICE_PARAM_ODL_ROUTER_PLUGINS
        parameters = service_parameter_list(request)
        for parameter in parameters:
            if ((parameter.service == SERVICE_TYPE_NETWORK) and
               (parameter.section == SERVICE_PARAM_SECTION_NETWORK_DEFAULT) and
               (parameter.name == SERVICE_PARAM_NAME_DEFAULT_SERVICE_PLUGINS)):
                return(any(sp in allowed_vals
                           for sp in parameter.value.split(',')))
    except Exception:
        pass
    return False


def is_system_mode_simplex(request):
    systems = system_list(request)
    system_mode = systems[0].to_dict().get('system_mode')
    if system_mode == constants.SYSTEM_MODE_SIMPLEX:
        return True
    return False


def get_system_type(request):
    systems = system_list(request)
    system_type = systems[0].to_dict().get('system_type')
    return system_type
