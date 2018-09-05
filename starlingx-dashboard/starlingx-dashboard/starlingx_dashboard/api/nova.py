#
# Copyright (c) 2018 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0
#

from novaclient.v2 import wrs_pci
from novaclient.v2 import wrs_providernets

from openstack_dashboard.api import base
from openstack_dashboard.api.nova import *


def server_group_list(request, all_projects=False):
    return novaclient(request).server_groups.list(all_projects)


def server_group_get(request, server_group_id):
    return novaclient(request).server_groups.get(server_group_id)


def server_group_create(request, name, project_id, metadata, policies):
    return novaclient(request).server_groups.create(
        name, project_id, metadata, policies)


def server_group_delete(request, server_group_id):
    return novaclient(request).server_groups.delete(server_group_id)


def provider_network_get(request, providernet_id):
    return wrs_providernets.ProviderNetsManager(novaclient(request)).get(
        providernet_id)


class DeviceUsage(base.APIResourceWrapper):
    """Wrapper for Inventory Device Usage
    """
    _attrs = ['device_id', 'device_name', 'vendor_id',
              'pci_vfs_configured', 'pci_vfs_used',
              'pci_pfs_configured', 'pci_pfs_used']


def get_device_usage_list(request):
    usages = wrs_pci.PciDevicesManager(novaclient(request)).list()
    return [DeviceUsage(n) for n in usages]


def get_device_usage(request, device_id):
    if device_id is None:
        raise nova_exceptions.ResourceNotFound

    usage = wrs_pci.PciDevicesManager(novaclient(request)).list(
        device_id=device_id)
    return DeviceUsage(usage[0])


class DetailUsage(base.APIResourceWrapper):
    """Wrapper for Inventory Device Usage
    """
    _attrs = ['host',
              'pci_vfs_configured', 'pci_vfs_used',
              'pci_pfs_configured', 'pci_pfs_used']


def get_detail_usage(request, device_id):
    usages = wrs_pci.PciDevicesManager(novaclient(request)).get(
        device_id)
    return [DetailUsage(n) for n in usages]
