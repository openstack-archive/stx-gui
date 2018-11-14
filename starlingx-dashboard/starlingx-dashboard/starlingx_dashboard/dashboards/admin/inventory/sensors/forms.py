#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from cgtsclient import exc

from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class AddSensorGroup(forms.SelfHandlingForm):

    DATA_TYPE_CHOICES = (
        (None, _("<Select Sensor Data type>")),
        ('analog', _("Analog Sensor")),
        ('discrete', _("Discrete Sensor")),
    )

    host_uuid = forms.CharField(label=_("host_uuid"),
                                initial='host_uuid',
                                widget=forms.widgets.HiddenInput)

    hostname = forms.CharField(label=_("Hostname"),
                               initial='hostname',
                               widget=forms.TextInput(attrs={
                                   'readonly': 'readonly'}))

    sensorgroup_name = forms.CharField(label=_("Sensor Group Name"),
                                       required=True,
                                       widget=forms.TextInput(
                                           attrs={'readonly': 'readonly'}))

    sensorgroup_datatype = forms.ChoiceField(
        label=_("Sensor Group Data Type"),
        required=True,
        choices=DATA_TYPE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switchable',
                   'data-slug': 'datatype'}))

    sensortype = forms.CharField(label=_("Sensor Type"),
                                 required=True,
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddSensorGroup, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddSensorGroup, self).clean()
        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']

        try:
            del data['host_id']
            del data['hostname']

            # The REST API takes care of creating the sensorgroup and assoc
            sensorgroup = stx_api.sysinv.host_sensorgroup_create(request,
                                                                 **data)

            msg = _('Sensor group was successfully created.')
            LOG.debug(msg)
            messages.success(request, msg)

            return sensorgroup
        except exc.ClientException as ce:
            msg = _('Failed to create sensor group.')
            LOG.info(msg)
            LOG.error(ce)

            # Allow REST API error message to appear on UI
            messages.error(request, ce)

            # Redirect to host details pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            msg = _('Failed to create sensor group.')
            LOG.info(msg)
            LOG.error(e)

            # if not a rest API error, throw default
            redirect = reverse(self.failure_url, args=[host_id])
            return exceptions.handle(request, message=e, redirect=redirect)


class UpdateSensorGroup(forms.SelfHandlingForm):

    DATA_TYPE_CHOICES = (
        ('analog', _("Analog Sensor")),
        ('discrete', _("Discrete Sensor")),
    )

    id = forms.CharField(widget=forms.widgets.HiddenInput)

    sensorgroupname = forms.CharField(
        label=_("SensorGroup Name"),
        required=False,
        widget=forms.widgets.TextInput(
            attrs={
                'class': 'switchable',
                'readonly': 'readonly',
                'data-slug': 'sensorgroupname'}))

    sensortype = forms.CharField(
        label=_("SensorType"),
        required=False,
        widget=forms.widgets.TextInput(
            attrs={
                'class': 'switchable',
                'readonly': 'readonly',
                'data-slug': 'sensortype'}))

    audit_interval_group = forms.IntegerField(
        label=_("Audit Interval (secs)"),
        help_text=_("Sensor Group Audit Interval in seconds."),
        required=False)

    actions_critical_group = forms.ChoiceField(
        label=_("Sensor Group Critical Actions"),
        required=False,
        help_text=_("Actions to take upon Sensor Group Critical event."))

    actions_major_group = forms.ChoiceField(
        label=_("Sensor Group Major Actions"),
        required=False,
        help_text=_("Actions to take upon Sensor Group Major event."))

    actions_minor_group = forms.ChoiceField(
        label=_("Sensor Group Minor Actions"),
        required=False,
        help_text=_("Actions to take upon Sensor Group Minor event."))

    failure_url = 'horizon:admin:inventory:index'

    def __init__(self, *args, **kwargs):
        super(UpdateSensorGroup, self).__init__(*args, **kwargs)

        sensorgroup = stx_api.sysinv.host_sensorgroup_get(
            self.request, kwargs['initial']['uuid'])

        self.fields['actions_critical_group'].choices = \
            sensorgroup.sensorgroup_actions_critical_choices_tuple_list

        self.fields['actions_major_group'].choices = \
            sensorgroup.sensorgroup_actions_major_choices_tuple_list

        self.fields['actions_minor_group'].choices = \
            sensorgroup.sensorgroup_actions_minor_choices_tuple_list

        LOG.debug("actions_critical_choices_choices = %s %s",
                  sensorgroup.sensorgroup_actions_critical_choices,
                  sensorgroup.sensorgroup_actions_critical_choices_tuple_list)

        LOG.debug("actions_major_choices_choices = %s %s",
                  sensorgroup.sensorgroup_actions_major_choices,
                  sensorgroup.sensorgroup_actions_major_choices_tuple_list)

        LOG.debug("actions_minor_choices_choices = %s %s",
                  sensorgroup.sensorgroup_actions_minor_choices,
                  sensorgroup.sensorgroup_actions_minor_choices_tuple_list)

    def clean(self):
        cleaned_data = super(UpdateSensorGroup, self).clean()
        return cleaned_data

    def handle(self, request, data):
        sensorgroup_id = data['id']
        # host_uuid = data['host_uuid']
        if data['audit_interval_group']:
            data['audit_interval_group'] = \
                str(data['audit_interval_group'])
        else:
            data['audit_interval_group'] = str("0")

        del data['id']

        if not data['actions_critical_group']:
            data['actions_critical_group'] = "none"

        if not data['actions_major_group']:
            data['actions_major_group'] = "none"

        if not data['actions_minor_group']:
            data['actions_minor_group'] = "none"

        data.pop('datatype', None)
        data.pop('sensortype', None)
        mysensorgroupname = data.pop('sensorgroupname', None)

        try:
            sensorgroup = \
                stx_api.sysinv.host_sensorgroup_update(request,
                                                       sensorgroup_id,
                                                       **data)

            msg = _('SensorGroup "%s" was '
                    'successfully updated.') % mysensorgroupname
            LOG.debug(msg)
            messages.success(request, msg)
            return sensorgroup

        except exc.ClientException as ce:
            # Allow REST API error message to appear on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure page
            redirect = reverse(self.failure_url, args=[sensorgroup_id])
            return shortcuts.redirect(redirect)

        except Exception:
            msg = (_('Failed to update sensorgroup "%s".') %
                   data['sensorgroupname'])
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[sensorgroup_id])
            exceptions.handle(request, msg, redirect=redirect)
