# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#


from django.utils.html import escape as escape_html
from django.utils.safestring import mark_safe

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from horizon.utils import filters as utils_filters
from starlingx_dashboard import api as stx_api

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


class AlarmsLimitAction(tables.LimitAction):
    verbose_name = _("Alarms")


class AlarmFilterAction(tables.FixedWithQueryFilter):
    def __init__(self, **kwargs):
        super(AlarmFilterAction, self).__init__(**kwargs)

        self.filter_choices = [
            (
                (stx_api.fm.FM_SUPPRESS_SHOW, _("Show Suppressed"), True),
                (stx_api.fm.FM_SUPPRESS_HIDE, _('Hide Suppressed'), True)
            )
        ]
        self.default_value = stx_api.fm.FM_SUPPRESS_HIDE

        self.disabled_choices = ['enabled']


class AlarmsTable(tables.DataTable):
    alarm_id = tables.Column('alarm_id',
                             link="horizon:admin:fault_management:detail",
                             verbose_name=_('Alarm ID'))
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
        verbose_name = _("Active Alarms")
        status_columns = ["suppression_status"]
        limit_param = "alarm_limit"
        pagination_param = "alarm_marker"
        prev_pagination_param = 'prev_alarm_marker'
        table_actions = (AlarmFilterAction, AlarmsLimitAction)
        multi_select = False
        hidden_title = False


class EventLogsLimitAction(tables.LimitAction):
    verbose_name = _("Events")


class EventLogsFilterAction(tables.FixedWithQueryFilter):
    def __init__(self, **kwargs):
        super(EventLogsFilterAction, self).__init__(**kwargs)

        self.filter_choices = [
            (
                (stx_api.fm.FM_ALL, _("All Events"), True),
                (stx_api.fm.FM_ALARM, _('Alarm Events'), True),
                (stx_api.fm.FM_LOG, _('Log Events'), True),
            ),
            (
                (stx_api.fm.FM_SUPPRESS_SHOW, _("Show Suppressed"), True),
                (stx_api.fm.FM_SUPPRESS_HIDE, _('Hide Suppressed'), True)
            )
        ]
        self.default_value = stx_api.fm.FM_ALL_SUPPRESS_HIDE

        self.disabled_choices = ['enabled', 'enabled']


class EventLogsTable(tables.DataTable):
    timestamp = tables.Column('timestamp',
                              attrs={'data-type': 'timestamp'},
                              filters=(utils_filters.parse_isotime,),
                              verbose_name=_('Timestamp'))

    state = tables.Column('state', verbose_name=_('State'))
    event_log_id = tables.Column('event_log_id',
                                 link="horizon:admin:fault_management:"
                                 "eventlogdetail",
                                 verbose_name=_('ID'))
    reason_text = tables.Column('reason_text', verbose_name=_('Reason Text'))
    entity_instance_id = tables.Column('entity_instance_id',
                                       verbose_name=_('Entity Instance ID'))
    suppression_status = \
        tables.Column('suppression_status',
                      verbose_name=_('Suppression Status'),
                      status=True,
                      status_choices=SUPPRESSION_STATUS_CHOICES,
                      display_choices=SUPPRESSION_STATUS_DISPLAY_CHOICES)
    severity = tables.Column('severity', verbose_name=_('Severity'))

    def get_object_id(self, obj):
        return obj.uuid

    class Meta(object):
        name = "eventLogs"
        verbose_name = _("Events")
        status_columns = ["suppression_status"]
        table_actions = (EventLogsFilterAction,
                         EventLogsLimitAction,)
        limit_param = "event_limit"
        pagination_param = "event_marker"
        prev_pagination_param = 'prev_event_marker'
        multi_select = False


class SuppressEvent(tables.BatchAction):
    name = "suppress"
    action_type = 'danger'
    icon = "remove"
    help_text = _("Events with selected Alarm ID will be suppressed.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Suppress Event",
            "Suppress Event",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Events suppressed for Alarm ID",
            "Events suppressed for Alarm ID",
            count
        )

    def allowed(self, request, datum):
        """Allow suppress action if Alarm ID is unsuppressed."""
        if datum.suppression_status == stx_api.fm.FM_SUPPRESSED:
            return False

        return True

    def action(self, request, obj_id):
        kwargs = {"suppression_status": stx_api.fm.FM_SUPPRESSED}

        try:
            stx_api.fm.event_suppression_update(request, obj_id, **kwargs)
        except Exception:
            exceptions.handle(request,
                              _('Unable to set specified alarm type to \
                               suppressed\'s.'))


class UnsuppressEvent(tables.BatchAction):
    name = "unsuppress"
    action_type = 'danger'
    icon = "remove"
    help_text = _("Events with selected Alarm ID will be unsuppressed.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Unsuppress Event",
            "Unsuppress Event",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Events unsuppressed for Alarm ID",
            "Events unsuppressed for Alarm ID",
            count
        )

    def allowed(self, request, datum):
        """Allow unsuppress action if Alarm ID is suppressed."""
        if datum.suppression_status == stx_api.fm.FM_UNSUPPRESSED:
            return False

        return True

    def action(self, request, obj_id):
        kwargs = {"suppression_status": stx_api.fm.FM_UNSUPPRESSED}

        try:
            stx_api.fm.event_suppression_update(request, obj_id, **kwargs)
        except Exception:
            exceptions.handle(request,
                              _('Unable to set specified alarm type to \
                               unsuppressed\'s.'))


class EventsSuppressionTable(tables.DataTable):
    # noinspection PyMethodParameters
    def description_inject(row_data):  # pylint: disable=no-self-argument
        description = \
            escape_html(str(row_data.description)).replace("\n", "<br/>")
        description = description.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        description = description.replace(" " * 4, "&nbsp;" * 4)
        description = description.replace(" " * 3, "&nbsp;" * 3)
        description = description.replace(" " * 2, "&nbsp;" * 2)
        return mark_safe(description)

    alarm_id = tables.Column('alarm_id',
                             verbose_name=_('Event ID'))
    description = tables.Column(description_inject,
                                verbose_name=_('Description'))
    status = tables.Column('suppression_status',
                           verbose_name=_('Status'))

    def get_object_id(self, obj):
        # return obj.alarm_id
        return obj.uuid

    def get_object_display(self, datum):
        """Returns a display name that identifies this object."""
        if hasattr(datum, 'alarm_id'):
            return datum.alarm_id
        return None

    class Meta(object):
        name = "eventsSuppression"
        limit_param = "events_suppression_limit"
        pagination_param = "events_suppression_marker"
        prev_pagination_param = 'prev_event_ids_marker'
        verbose_name = _("Events Suppression")
        row_actions = (SuppressEvent, UnsuppressEvent,)
        multi_select = False
