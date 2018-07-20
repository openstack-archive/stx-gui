#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class UploadPatchForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'
    patch_files = forms.FileField(label=_("Patch File(s)"),
                                  widget=forms.FileInput(attrs={
                                      'data-source-file': _('Patch File(s)'),
                                      'multiple': "multiple"}),
                                  required=True)

    def __init__(self, *args, **kwargs):
        super(UploadPatchForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(UploadPatchForm, self).clean()
        return data

    def handle(self, request, data):
        success_responses = []
        failure_responses = []

        for f in request.FILES.getlist('patch_files'):
            try:
                success_responses.append(
                    api.patch.upload_patch(request, f, f.name))
            except Exception as ex:
                failure_responses.append(str(ex))

        # Consolidate server responses into one success/error message
        # respectively
        if success_responses:
            if len(success_responses) == 1:
                messages.success(request, success_responses[0])
            else:
                success_msg = ""
                for i in range(len(success_responses)):
                    success_msg += str(i + 1) + ") " + success_responses[i]
                messages.success(request, success_msg)

        if failure_responses:
            if len(failure_responses) == 1:
                messages.error(request, failure_responses[0])
            else:
                error_msg = ""
                for i in range(len(failure_responses)):
                    error_msg += str(i + 1) + ") " + failure_responses[i]
                messages.error(request, error_msg)

        return True


class CreatePatchStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'

    CONTROLLER_APPLY_TYPES = (
        ('serial', _("Serial")),
        ('ignore', _("Ignore")),
    )

    AIO_APPLY_TYPES = (
        ('serial', _("Serial")),
    )

    GENERIC_APPLY_TYPES = (
        ('serial', _("Serial")),
        ('parallel', _("Parallel")),
        ('ignore', _("Ignore")),
    )

    INSTANCE_ACTIONS = (
        ('stop-start', _("Stop-Start")),
        ('migrate', _("Migrate")),
    )

    SIMPLEX_INSTANCE_ACTIONS = (
        ('stop-start', _("Stop-Start")),
    )

    ALARM_RESTRICTION_TYPES = (
        ('strict', _("Strict")),
        ('relaxed', _("Relaxed")),
    )

    controller_apply_type = forms.ChoiceField(
        label=_("Controller Apply Type"),
        required=True,
        choices=CONTROLLER_APPLY_TYPES,
        widget=forms.Select())

    storage_apply_type = forms.ChoiceField(
        label=_("Storage Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select())

    compute_apply_type = forms.ChoiceField(
        label=_("Compute Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'compute_apply_type'}))

    max_parallel_compute_hosts = forms.IntegerField(
        label=_("Maximum Parallel Compute Hosts"),
        initial=2,
        min_value=2,
        max_value=100,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Compute Hosts must be '
                                     'between 2 and 100.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'compute_apply_type',
                'data-compute_apply_type-parallel':
                    'Maximum Parallel Compute Hosts'}))

    default_instance_action = forms.ChoiceField(
        label=_("Default Instance Action"),
        required=True,
        choices=INSTANCE_ACTIONS,
        widget=forms.Select())

    alarm_restrictions = forms.ChoiceField(
        label=_("Alarm Restrictions"),
        required=True,
        choices=ALARM_RESTRICTION_TYPES,
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(CreatePatchStrategyForm, self).__init__(request, *args, **kwargs)

        cinder_backend = api.sysinv.get_cinder_backend(request)
        if api.sysinv.CINDER_BACKEND_CEPH not in cinder_backend:
            del self.fields['storage_apply_type']

        system_type = api.sysinv.get_system_type(request)
        if system_type == api.sysinv.SYSTEM_TYPE_AIO:
            del self.fields['controller_apply_type']
            self.fields['compute_apply_type'].choices = self.AIO_APPLY_TYPES

        if api.sysinv.is_system_mode_simplex(request):
            self.fields['default_instance_action'].choices = \
                self.SIMPLEX_INSTANCE_ACTIONS

    def clean(self):
        data = super(CreatePatchStrategyForm, self).clean()
        return data

    def handle(self, request, data):
        try:
            response = api.vim.create_strategy(
                request, api.vim.STRATEGY_SW_PATCH,
                data.get('controller_apply_type', 'ignore'),
                data.get('storage_apply_type', 'ignore'), 'ignore',
                data['compute_apply_type'],
                data['max_parallel_compute_hosts'],
                data['default_instance_action'],
                data['alarm_restrictions'])
            if not response:
                messages.error(request, "Strategy creation failed")
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, "Strategy creation failed",
                              redirect=redirect)
        return True


class CreateUpgradeStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'

    GENERIC_APPLY_TYPES = (
        ('serial', _("Serial")),
        ('parallel', _("Parallel")),
        ('ignore', _("Ignore")),
    )

    ALARM_RESTRICTION_TYPES = (
        ('strict', _("Strict")),
        ('relaxed', _("Relaxed")),
    )

    storage_apply_type = forms.ChoiceField(
        label=_("Storage Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select())

    compute_apply_type = forms.ChoiceField(
        label=_("Compute Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'compute_apply_type'}))

    max_parallel_compute_hosts = forms.IntegerField(
        label=_("Maximum Parallel Compute Hosts"),
        initial=2,
        min_value=2,
        max_value=10,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Compute Hosts must be '
                                     'between 2 and 10.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'compute_apply_type',
                'data-compute_apply_type-parallel':
                    'Maximum Parallel Compute Hosts'}))

    alarm_restrictions = forms.ChoiceField(
        label=_("Alarm Restrictions"),
        required=True,
        choices=ALARM_RESTRICTION_TYPES,
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(CreateUpgradeStrategyForm, self).__init__(request, *args,
                                                        **kwargs)
        cinder_backend = api.sysinv.get_cinder_backend(request)
        if api.sysinv.CINDER_BACKEND_CEPH not in cinder_backend:
            del self.fields['storage_apply_type']

    def clean(self):
        data = super(CreateUpgradeStrategyForm, self).clean()
        return data

    def handle(self, request, data):
        try:
            response = api.vim.create_strategy(
                request, api.vim.STRATEGY_SW_UPGRADE, 'ignore',
                data.get('storage_apply_type', 'ignore'), 'ignore',
                data['compute_apply_type'],
                data['max_parallel_compute_hosts'],
                'migrate',
                data['alarm_restrictions'])
            if not response:
                messages.error(request, "Strategy creation failed")
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, "Strategy creation failed",
                              redirect=redirect)
        return True
