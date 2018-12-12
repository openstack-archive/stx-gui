#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from dcmanagerclient import exceptions as exc

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api
from starlingx_dashboard.dashboards.admin.software_management.forms \
    import UploadPatchForm as AdminPatchForm

LOG = logging.getLogger(__name__)


class UploadPatchForm(AdminPatchForm):
    failure_url = 'horizon:dc_admin:dc_software_management:index'


class CreateCloudPatchStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_software_management:index'

    SUBCLOUD_APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    subcloud_apply_type = forms.ChoiceField(
        label=_("Subcloud Apply Type"),
        required=True,
        choices=SUBCLOUD_APPLY_TYPES,
        widget=forms.Select())

    max_parallel_subclouds = forms.IntegerField(
        label=_("Maximum Parallel Subclouds"),
        initial=20,
        min_value=2,
        max_value=100,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Subclouds must be '
                                     'between 2 and 100.')},
        widget=forms.TextInput())

    stop_on_failure = forms.BooleanField(
        label=_("Stop on Failure"),
        required=False,
        initial=True,
        help_text=_("Determines whether patch orchestration failure in a "
                    "subcloud prevents application to subsequent subclouds"))

    def handle(self, request, data):
        try:
            # convert keys to use dashes
            for k in data.keys():
                if '_' in k:
                    data[k.replace('_', '-')] = data[k]
                    del data[k]

            data['stop-on-failure'] = str(data['stop-on-failure']).lower()

            response = api.dc_manager.strategy_create(request, data)
            if not response:
                messages.error(request, "Strategy creation failed")
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, "Strategy creation failed",
                              redirect=redirect)
        return True


class CreateCloudPatchConfigForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_software_management:index'

    APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    INSTANCE_ACTIONS = (
        ('migrate', _("Migrate")),
        ('stop-start', _("Stop-Start")),
    )

    ALARM_RESTRICTION_TYPES = (
        ('relaxed', _("Relaxed")),
        ('strict', _("Strict")),
    )

    subcloud = forms.ChoiceField(
        label=_("Subcloud"),
        required=True,
        widget=forms.Select())

    storage_apply_type = forms.ChoiceField(
        label=_("Storage Apply Type"),
        required=True,
        choices=APPLY_TYPES,
        widget=forms.Select())

    worker_apply_type = forms.ChoiceField(
        label=_("Worker Apply Type"),
        required=True,
        choices=APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'worker_apply_type'}))

    max_parallel_workers = forms.IntegerField(
        label=_("Maximum Parallel Worker Hosts"),
        initial=2,
        min_value=2,
        max_value=100,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Worker Hosts must be '
                                     'between 2 and 100.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'worker_apply_type',
                'data-worker_apply_type-parallel':
                    'Maximum Parallel Worker Hosts'}))

    default_instance_action = forms.ChoiceField(
        label=_("Default Instance Action"),
        required=True,
        choices=INSTANCE_ACTIONS,
        widget=forms.Select())

    alarm_restriction_type = forms.ChoiceField(
        label=_("Alarm Restrictions"),
        required=True,
        choices=ALARM_RESTRICTION_TYPES,
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(CreateCloudPatchConfigForm, self).__init__(request, *args,
                                                         **kwargs)
        subcloud_list = [(api.dc_manager.DEFAULT_CONFIG_NAME,
                          api.dc_manager.DEFAULT_CONFIG_NAME), ]
        subclouds = api.dc_manager.subcloud_list(self.request)
        subcloud_list.extend([(c.name, c.name) for c in subclouds])
        self.fields['subcloud'].choices = subcloud_list

        if self.initial.get('subcloud', None):
            self.fields['subcloud'].widget.attrs['disabled'] = 'disabled'

    def handle(self, request, data):
        try:
            for k in data.keys():
                if '_' in k:
                    data[k.replace('_', '-')] = data[k]
                    del data[k]

            subcloud = data['subcloud']
            if subcloud == api.dc_manager.DEFAULT_CONFIG_NAME:
                subcloud = None
            del data['subcloud']

            response = api.dc_manager.config_update(request, subcloud, data)
            if not response:
                messages.error(request, "Cloud Patching Configuration "
                                        "creation failed")

        except exc.APIException as e:
            LOG.error(e.error_message)
            messages.error(request, e.error_message)

            redirect = reverse(self.failure_url)
            exceptions.handle(request, e.error_message, redirect=redirect)
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              "Cloud Patching Configuration creation failed",
                              redirect=redirect)
        return True
