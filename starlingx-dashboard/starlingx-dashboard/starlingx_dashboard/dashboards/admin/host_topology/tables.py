#
# Copyright (c) 2016-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from horizon import tables
from horizon.utils import filters as utils_filters
import logging

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from starlingx_dashboard.dashboards.admin.datanets.datanets.ranges \
    import tables as sr_tables
from starlingx_dashboard.dashboards.admin.inventory.interfaces import \
    tables as if_tables

LOG = logging.getLogger(__name__)

SUPPRESSION_STATUS_CHOICES = (
    ("suppressed", False),
    ("unsuppressed", True),
    ("None", True),
)
SUPPRESSION_STATUS_DISPLAY_CHOICES = (
    ("suppressed", pgettext_lazy("Indicates this type of alarm \
    is suppressed", "suppressed")),
    ("unsuppressed", pgettext_lazy("Indicates this type of alarm \
    is unsuppressed", "unsuppressed")),
    ("None", pgettext_lazy("Indicates an event type", "None")),
)


class ProviderNetworkRangeTable(sr_tables.ProviderNetworkRangeTable):
    class Meta(object):
        name = "provider_network_ranges"
        verbose_name = _("Segmentation Ranges")
        table_actions = ()
        row_actions = ()


def get_alarm_link_url(alarm):
    return "/ngdetails/OS::StarlingX::ActiveAlarms/" + alarm.uuid


class AlarmsTable(tables.DataTable):
    alarm_id = tables.Column('alarm_id',
                             verbose_name=_('Alarm ID'),
                             link=get_alarm_link_url)
    reason_text = tables.Column('reason_text',
                                verbose_name=_('Reason Text'))
    entity_instance_id = tables.Column('entity_instance_id',
                                       verbose_name=_('Entity Instance ID'))
    suppression_status = \
        tables.Column('suppression_status',
                      verbose_name=_('Suppression Status'),
                      status=True,
                      status_choices=SUPPRESSION_STATUS_CHOICES,
                      display_choices=SUPPRESSION_STATUS_DISPLAY_CHOICES)
    severity = tables.Column('severity',
                             verbose_name=_('Severity'))
    timestamp = tables.Column('timestamp',
                              attrs={'data-type': 'timestamp'},
                              filters=(utils_filters.parse_isotime,),
                              verbose_name=_('Timestamp'))

    def get_object_id(self, obj):
        return obj.uuid

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
