#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django import template
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory import tables as itables

LOG = logging.getLogger(__name__)


class AddSensorGroup(tables.LinkAction):
    name = "addsensorgroup"
    verbose_name = ("Add Sensor Group")
    url = "horizon:admin:inventory:addsensorgroup"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        self.verbose_name = _("Add Sensor Group")
        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes
        if not host._administrative == 'locked':
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Node Unlocked)"))
        return True  # The action should always be displayed


class RemoveSensorGroup(tables.DeleteAction):
    data_type_singular = _("Sensor Group")
    data_type_plural = _("Sensor Groups")

    def allowed(self, request, sensorgroup=None):
        host = self.table.kwargs['host']
        return host._administrative == 'locked'

    def delete(self, request, sensorgroup_id):
        host_id = self.table.kwargs['host_id']
        try:
            stx_api.sysinv.host_sensorgroup_delete(request, sensorgroup_id)
        except Exception:
            msg = _('Failed to delete host %(hid)s '
                    'sensor group %(sensorgroup)s') % \
                {'hid': host_id, 'sensorgroup': sensorgroup_id}
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class EditSensorGroup(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit SensorGroup")
    url = "horizon:admin:inventory:editsensorgroup"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, sensorgroup=None):
        host_id = self.table.kwargs['host_id']
        # sensorgroup_uuid = self.table.kwargs['sensorgroup_id']
        return reverse(self.url, args=(host_id, sensorgroup.uuid))

    def allowed(self, request, datum):
        # host = self.table.kwargs['host']
        return True
        # return host._administrative == 'locked'


def sensorgroup_suppressed(sensorgroup=None):
    if not sensorgroup:
        return False
    return (sensorgroup.suppress == "True")


def get_sensorgroup_suppress(sensorgroup):
    suppress_str = ""
    if sensorgroup_suppressed(sensorgroup):
        suppress_str = "suppressed"

    return suppress_str


class SuppressSensorGroup(tables.BatchAction):
    name = "suppress"
    action_type = 'danger'
    confirm_class = 'btn-danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Suppress SensorGroup",
            "Suppress SensorGroups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Suppressed SensorGroup",
            "Suppressed SensorGroups",
            count
        )

    def get_confirm_message(self, request, datum):
        return _("<b>WARNING</b>: This operation will suppress actions "
                 "for sensorgroup '%s'.  This will affect all sensors in "
                 "this sensorgroup.") % datum.sensorgroupname

    def allowed(self, request, sensorgroup=None):
        return not sensorgroup_suppressed(sensorgroup)

    def action(self, request, sensorgroup_id):
        stx_api.sysinv.host_sensorgroup_suppress(request, sensorgroup_id)

    def handle(self, table, request, obj_ids):
        return itables.handle_sysinv(self, table, request, obj_ids)


class UnSuppressSensorGroup(tables.BatchAction):
    name = "unsuppress"
    classes = ('btn-warning', 'btn-unsuppress')

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "UnSuppress SensorGroup",
            "UnSuppress SensorGroups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "UnSuppressed SensorGroup",
            "UnSuppressed SensorGroups",
            count
        )

    def allowed(self, request, sensorgroup=None):
        return sensorgroup_suppressed(sensorgroup)

    def action(self, request, sensorgroup_id):
        stx_api.sysinv.host_sensorgroup_unsuppress(request, sensorgroup_id)

    def handle(self, table, request, obj_ids):
        return itables.handle_sysinv(self, table, request, obj_ids)


def get_sensors(sensorgroup):
    sensor_str_list = ", ".join(sensorgroup.sensorNameList)
    return sensor_str_list


def get_sensorgroups(sensor):
    sensorgroup_str_list = ", ".join(sensor.sensorgroupNameList)
    return sensorgroup_str_list


def get_sensorgroup_actions(sensorgroup):
    # if sensorgroup.something_configured == 'True':
    template_name = \
        'admin/inventory/sensors/_sensorgroup_actions.html'
    context = {"sensorgroup": sensorgroup}
    return template.loader.render_to_string(template_name, context)


def get_sensor_actions(sensor):
    # if sensor.something_configured == 'True':
    template_name = \
        'admin/inventory/sensors/_sensor_actions.html'
    context = {"sensor": sensor}
    return template.loader.render_to_string(template_name, context)


class RelearnSensorModel(tables.Action):
    name = "relearn"
    requires_input = False
    icon = "refresh"
    action_type = 'danger'
    verbose_name = _("Relearn Sensor Model")
    confirm_message = "This operation will delete this sensor model." \
                      "All alarm assertions against this model will be " \
                      "cleared. Any sensor suppression settings at the " \
                      "group or sensor levels will be lost. " \
                      "Will attempt to preserve customized group actions " \
                      "and monitor interval in new model."

    def allowed(self, request, datum):
        bm_type = self.table.kwargs['host'].bm_type
        return bm_type and bm_type.lower() != 'none'

    def single(self, table, request, obj_ids):
        LOG.debug("requesting relearn of sensor model for host "
                  "%s", table.kwargs['host'].uuid)
        stx_api.sysinv.host_sensorgroup_relearn(request,
                                                table.kwargs['host'].uuid)


class SensorGroupsTable(tables.DataTable):
    name = tables.Column('sensorgroupname',
                         link="horizon:admin:inventory:sensorgroupdetail",
                         verbose_name=('Name'))
    sensor_type = tables.Column('sensortype',
                                verbose_name=('SensorType'))
    sensor_state = tables.Column('state',
                                 verbose_name=('State'))
    sensors = tables.Column(get_sensors,
                            verbose_name=('Sensors'),
                            help_text=_("Sensors in SensorGroup."))
    actions_group = tables.Column(get_sensorgroup_actions,
                                  verbose_name=('Sensor Handling Actions'),
                                  help_text=_("Actions performed on "
                                              "Sensor Event."))
    suppressed = tables.Column(get_sensorgroup_suppress,
                               verbose_name=('Suppression'),
                               help_text=_("Indicates 'suppressed' if Actions "
                                           "are suppressed."))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.sensorgroupname

    class Meta(object):
        name = "sensorgroups"
        verbose_name = ("Sensor Groups")
        columns = ('name', 'sensor_type', 'sensor_state', 'sensors',
                   'actions_group', 'suppressed')
        multi_select = False
        row_actions = (EditSensorGroup,
                       UnSuppressSensorGroup,
                       SuppressSensorGroup)
        table_actions = (RelearnSensorModel,)
        hidden_title = False


class EditSensor(tables.LinkAction):
    name = "updatesensor"
    verbose_name = _("Edit Sensor")
    url = "horizon:admin:inventory:editsensor"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, sensor=None):
        host_id = self.table.kwargs['host_id']
        # sensorgroup_uuid = self.table.kwargs['sensorgroup_id']
        return reverse(self.url, args=(host_id, sensor.uuid))

    def allowed(self, request, datum):
        # host = self.table.kwargs['host']
        return True
        # return host._administrative == 'locked'


def sensor_suppressed(sensor=None):
    if not sensor:
        return False
    return (sensor.suppress == "True")


def get_suppress(sensor):
    suppress_str = ""
    if sensor_suppressed(sensor):
        suppress_str = "suppressed"

    return suppress_str


class SuppressSensor(tables.BatchAction):
    name = "suppress"
    classes = ('btn-confirm', 'btn-suppress')

    confirm_class = 'btn-confirm'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Suppress Sensor",
            "Suppress Sensors",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Suppressed Sensor",
            "Suppressed Sensors",
            count
        )

    def get_confirm_message(self, request, datum):
        return _("<b>WARNING</b>: This operation will suppress actions "
                 " for sensor '%s'. ") % datum.sensorname

    def allowed(self, request, sensor=None):
        return not sensor_suppressed(sensor)

    def action(self, request, sensor_id):
        stx_api.sysinv.host_sensor_suppress(request, sensor_id)

    def handle(self, table, request, obj_ids):
        return itables.handle_sysinv(self, table, request, obj_ids)


class UnSuppressSensor(tables.BatchAction):
    name = "unsuppress"
    classes = ('btn-warning', 'btn-unsuppress')

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "UnSuppress Sensor",
            "UnSuppress Sensors",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "UnSuppressed Sensor",
            "UnSuppressed Sensors",
            count
        )

    def allowed(self, request, sensor=None):
        return sensor_suppressed(sensor)

    def action(self, request, sensor_id):
        stx_api.sysinv.host_sensor_unsuppress(request, sensor_id)

    def handle(self, table, request, obj_ids):
        return itables.handle_sysinv(self, table, request, obj_ids)


class SensorsFilterAction(tables.FilterAction):
    def filter(self, table, sensors, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(sensor):
            if (q in sensor.sensorname.lower() or
               q in sensor.sensorgroupname.lower() or
               q in sensor.sensortype.lower() or
               q in sensor.state or
               q in sensor.status):
                return True
            return False

        return list(filter(comp, sensors))


class SensorsTable(tables.DataTable):
    name = tables.Column('sensorname',
                         link="horizon:admin:inventory:sensordetail",
                         verbose_name=('Name'))
    sensor_type = tables.Column('sensortype',
                                verbose_name=('SensorType'))
    sensor_status = tables.Column('status',
                                  verbose_name=('Status'))
    sensor_state = tables.Column('state',
                                 verbose_name=('State'))
    suppressed = tables.Column(get_suppress,
                               verbose_name=('Suppression'),
                               help_text=_("Indicates 'suppressed' if Actions "
                                           "are suppressed."))
    sensorgroupname = tables.Column(get_sensorgroups,
                                    verbose_name=('Sensor Group Name'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.sensorname

    class Meta(object):
        name = "sensors"
        verbose_name = ("Sensors")
        columns = ('name', 'sensorgroupname', 'sensor_type', 'sensor_state',
                   'sensor_status', 'suppressed')
        multi_select = False
        row_actions = (SuppressSensor, UnSuppressSensor)  # EditSensor
        table_actions = (SensorsFilterAction,)
        hidden_title = False
