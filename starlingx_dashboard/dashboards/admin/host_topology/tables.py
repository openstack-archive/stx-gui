#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.admin.fault_management import \
    tables as fm_tables
from openstack_dashboard.dashboards.admin.inventory.interfaces import \
    tables as if_tables
from openstack_dashboard.dashboards.admin.providernets.providernets.ranges import \
    tables as sr_tables

LOG = logging.getLogger(__name__)


class ProviderNetworkRangeTable(sr_tables.ProviderNetworkRangeTable):
    class Meta(object):
        name = "provider_network_ranges"
        verbose_name = _("Segmentation Ranges")
        table_actions = ()
        row_actions = ()


class AlarmsTable(fm_tables.AlarmsTable):
    class Meta(object):
        name = "alarms"
        verbose_name = _("Related Alarms")
        multi_select = False
        table_actions = []
        row_actions = []


class InterfacesTable(if_tables.InterfacesTable):
    class Meta(object):
        name = "interfaces"
        verbose_name = _("Interfaces")
        multi_select = False
        table_actions = []
        row_actions = []
