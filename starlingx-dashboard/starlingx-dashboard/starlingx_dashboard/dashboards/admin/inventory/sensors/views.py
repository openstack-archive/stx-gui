#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import views

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.sensors.forms import \
    AddSensorGroup
from starlingx_dashboard.dashboards.admin.inventory.sensors.forms import \
    UpdateSensorGroup

LOG = logging.getLogger(__name__)


class AddSensorGroupView(forms.ModalFormView):
    form_class = AddSensorGroup
    template_name = 'admin/inventory/storages/createsensorgroup.html'
    # template_name = 'admin/inventory/storages/createlocalvolumegroup.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddSensorGroupView, self) \
            .get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(AddSensorGroupView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = stx_api.sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['host_uuid'] = host.uuid
        initial['hostname'] = host.hostname
        return initial


class UpdateSensorGroupView(forms.ModalFormView):
    form_class = UpdateSensorGroup
    template_name = 'admin/inventory/sensors/updatesensorgroup.html'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            sensorgroup_id = self.kwargs['sensorgroup_id']
            host_id = self.kwargs['host_id']
            LOG.debug("sensorgroup_id=%s kwargs=%s",
                      sensorgroup_id, self.kwargs)
            try:
                self._object = \
                    stx_api.sysinv.host_sensorgroup_get(self.request,
                                                        sensorgroup_id)
                self._object.host_id = host_id

            except Exception:
                redirect = reverse("horizon:project:networks:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve sensorgroup details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateSensorGroupView, self).get_context_data(**kwargs)
        sensorgroup = self._get_object()
        context['sensorgroup_id'] = sensorgroup.uuid
        context['host_id'] = sensorgroup.host_id
        return context

    def get_initial(self):
        sensorgroup = self._get_object()
        return {'id': sensorgroup.uuid,
                'uuid': sensorgroup.uuid,
                'host_uuid': sensorgroup.host_uuid,
                'sensorgroupname': sensorgroup.sensorgroupname,
                'sensortype': sensorgroup.sensortype,
                'datatype': sensorgroup.datatype,
                'audit_interval_group': sensorgroup.audit_interval_group,
                'actions_critical_choices':
                    sensorgroup.actions_critical_choices,
                'actions_major_choices': sensorgroup.actions_major_choices,
                'actions_minor_choices': sensorgroup.actions_minor_choices,
                'actions_critical_group': sensorgroup.actions_critical_group,
                'actions_major_group': sensorgroup.actions_major_group,
                'actions_minor_group': sensorgroup.actions_minor_group,
                'algorithm': sensorgroup.algorithm}


class DetailSensorView(views.HorizonTemplateView):
    template_name = 'admin/inventory/_detail_sensor.html'
    page_title = '{{ sensor.sensorname }}'

    def get_context_data(self, **kwargs):
        context = super(DetailSensorView, self)\
            .get_context_data(**kwargs)
        sensor = self.get_data()

        hostname = self.get_hostname(sensor.host_uuid)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(sensor.host_uuid,))),
            (_("Sensors"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context["sensor"] = sensor
        return context

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = stx_api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_data(self):
        if not hasattr(self, "_sensor"):
            sensor_id = self.kwargs['sensor_id']
            try:
                sensor = stx_api.sysinv.host_sensor_get(self.request,
                                                        sensor_id)
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'Sensor "%s".') % sensor_id,
                                  redirect=redirect)

            self._sensor = sensor
        return self._sensor


class DetailSensorGroupView(views.HorizonTemplateView):
    template_name = 'admin/inventory/_detail_sensor_group.html'
    page_title = '{{ sensorgroup.sensorgroupname }}'

    def get_context_data(self, **kwargs):
        context = super(DetailSensorGroupView, self)\
            .get_context_data(**kwargs)
        sensorgroup = self.get_data()

        hostname = self.get_hostname(sensorgroup.host_uuid)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(sensorgroup.host_uuid,))),
            (_("Sensor Groups"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context["sensorgroup"] = sensorgroup
        return context

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = stx_api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_data(self):
        if not hasattr(self, "_sensorgroup"):
            sensorgroup_id = self.kwargs['sensorgroup_id']
            try:
                sensorgroup = \
                    stx_api.sysinv.host_sensorgroup_get(self.request,
                                                        sensorgroup_id)
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'SensorGroup "%s".') % sensorgroup_id,
                                  redirect=redirect)

            self._sensorgroup = sensorgroup
        return self._sensorgroup
