#
# Copyright (c) 2014-2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4


import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class EditDevice(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Device")
    url = "horizon:admin:inventory:editdevice"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, device=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, device.uuid))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        return (host._administrative == 'locked' and
                stx_api.sysinv.SUBFUNCTIONS_WORKER in host.subfunctions)


def get_viewdevice_link_url(device):
    return reverse("horizon:admin:inventory:viewdevice",
                   args=(device.host_id, device.uuid))


class DevicesTable(tables.DataTable):
    """Devices Table per host under Host Tab"""

    name = tables.Column('name',
                         verbose_name=_('Name'),
                         link=get_viewdevice_link_url)
    address = tables.Column('pciaddr',
                            verbose_name=_('Address'))
    device_id = tables.Column('pdevice_id',
                              verbose_name=_('Device Id'))
    device_name = tables.Column('pdevice',
                                verbose_name=_('Device Name'))
    numa_node = tables.Column('numa_node',
                              verbose_name=_('Numa Node'))
    enabled = tables.Column('enabled',
                            verbose_name=_('Enabled'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.name

    class Meta(object):
        name = "devices"
        verbose_name = _("Devices")
        multi_select = False
        row_actions = (EditDevice,)


class UsageTable(tables.DataTable):
    """Detail usage table for a device under Device Usage tab"""

    host = tables.Column('host',
                         verbose_name=_('Host'))
    pci_pfs_configured = tables.Column('pci_pfs_configured',
                                       verbose_name=_('PFs configured'))
    pci_pfs_used = tables.Column('pci_pfs_configured',
                                 verbose_name=_('PFs used'))
    pci_vfs_configured = tables.Column('pci_vfs_configured',
                                       verbose_name=_('VFs configured'))
    pci_vfs_used = tables.Column('pci_vfs_used',
                                 verbose_name=_('VFs used'))

    def get_object_id(self, datum):
        return str(datum.id)

    def get_object_display(self, datum):
        return datum.host

    class Meta(object):
        name = "usage"
        verbose_name = _("Usage")
        multi_select = False


def get_viewusage_link_url(usage):
    return reverse("horizon:admin:inventory:viewusage",
                   args=(usage.device_id,))


class DeviceUsageTable(tables.DataTable):
    """Device Usage table for all devices (i.e Device Usage tab)"""

    device_name = tables.Column('device_name',
                                link=get_viewusage_link_url,
                                verbose_name=_('PCI Alias'))

    description = tables.Column('description', verbose_name=_('Description'))

    device_id = tables.Column('device_id',
                              verbose_name=_('Device Id'))

    vendor_id = tables.Column('vendor_id',
                              verbose_name=_('Vendor Id'))

    class_id = tables.Column('class_id',
                             verbose_name=_('Class Id'))

    pci_pfs_configured = tables.Column('pci_pfs_configured',
                                       verbose_name=_("PFs configured"))

    pci_pfs_used = tables.Column('pci_pfs_used',
                                 verbose_name=_("PFs used"))

    pci_vfs_configured = tables.Column('pci_vfs_configured',
                                       verbose_name=_("VFs configured"))

    pci_vfs_used = tables.Column('pci_vfs_used',
                                 verbose_name=_("VFs used"))

    def get_object_id(self, datum):
        return str(datum.device_id)

    def get_object_display(self, datum):
        return datum.device_name

    class Meta(object):
        name = "deviceusage"
        verbose_name = _("Device Usage")
