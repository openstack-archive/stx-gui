#
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables

LOG = logging.getLogger(__name__)


class UpdatePort(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Port")
    url = "horizon:admin:inventory:editport"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, port):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, port.uuid))

    def allowed(self, request, port=None):
        host = self.table.kwargs['host']
        return host._administrative == 'locked'


def get_devicetype(port):
    template_name = 'admin/inventory/ports/_ports_devicetype.html'
    context = {"port": port}
    return template.loader.render_to_string(template_name, context)


def get_name(port):
    return port.get_port_display_name()


def get_bootp(port):
    if port.bootp:
        return port.bootp
    else:
        return False


def get_link_url(port):
    return reverse("horizon:admin:inventory:viewport",
                   args=(port.host_uuid, port.uuid))


class PortsTable(tables.DataTable):
    name = tables.Column(get_name,
                         verbose_name=_('Name'),
                         link=get_link_url)

    mac = tables.Column('mac',
                        verbose_name=_('MAC Address'))
    pciaddr = tables.Column('pciaddr',
                            verbose_name=_('PCI Address'))
    numa_node = tables.Column('numa_node',
                              verbose_name=_('Processor'))
    autoneg = tables.Column('autoneg',
                            verbose_name=_('Auto Negotiation'))
    # speed = tables.Column('speed',
    # verbose_name=_('Speed (Mbps)'))
    bootp = tables.Column(get_bootp,
                          verbose_name=_('Boot Interface'))
    dpdksupport = tables.Column('dpdksupport',
                                verbose_name=_('Accelerated'))
    devicetype = tables.Column(get_devicetype,
                               verbose_name=_('Device Type'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.get_port_display_name()

    class Meta(object):
        name = "ports"
        verbose_name = _("Ports")
        multi_select = False
        # row_actions = (UpdatePort,)
