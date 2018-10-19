#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _
from horizon import tables

LOG = logging.getLogger(__name__)


def get_name(neighbour):
    return neighbour.get_local_port_display_name()


class LldpNeighboursTable(tables.DataTable):
    name = tables.Column(get_name,
                         verbose_name=_('Name'),
                         link="horizon:admin:inventory:viewneighbour")
    port_identifier = tables.Column('port_identifier',
                                    verbose_name=_('Neighbor'))
    port_description = tables.Column('port_description',
                                     verbose_name=_('Port Description'))
    ttl = tables.Column('ttl', verbose_name=_('Time To Live (Rx)'))

    system_name = tables.Column('system_name',
                                verbose_name=_('System Name'),
                                truncate=100)
    dot3_max_frame = tables.Column('dot3_max_frame',
                                   verbose_name=_('Max Frame Size'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.get_local_port_display_name()

    class Meta(object):
        name = "neighbours"
        verbose_name = _("LLDP Neighbors")
        multi_select = False
