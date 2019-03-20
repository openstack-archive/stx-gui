#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2019 Wind River Systems, Inc.
# Copyright (C) 2019 Intel Corporation
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


LABEL_KEY_CUSTOM = "customized_label"
LABEL_KEY_CHOICES = (
    (stx_api.sysinv.K8S_LABEL_OPENSTACK_CONTROL_PLANE,
        _("openstack-control-plane")),
    (stx_api.sysinv.K8S_LABEL_OPENSTACK_COMPUTE_NODE,
        _("openstack-compute-node")),
    (stx_api.sysinv.K8S_LABEL_OPENVSWITCH,
        _("openvswitch")),
    (stx_api.sysinv.K8S_LABEL_SRIOV,
        _("sriov")),
    (LABEL_KEY_CUSTOM, _("customized label")),
)


class AssignLabel(forms.SelfHandlingForm):
    host_uuid = forms.CharField(
        label=_("host_uuid"),
        initial='host_uuid',
        required=False,
        widget=forms.widgets.HiddenInput)

    host_id = forms.CharField(
        label=_("host_id"),
        initial='host_id',
        required=False,
        widget=forms.widgets.HiddenInput)

    labelkey = forms.ChoiceField(
        label=_("Label Key"),
        required=True,
        choices=LABEL_KEY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'labelkey'}))

    clabelkey = forms.CharField(
        label=_("Customized Label Key"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'labelkey',
            'data-slug': 'clabelkey',
            'data-labelkey-customized_label': _("Customized Label Key")}))

    clabelvalue = forms.CharField(
        label=_("Customized Label Value"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'labelkey',
            'data-slug': 'clabelvalue',
            'data-labelkey-customized_label': _("Customized Label Value")}))

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AssignLabel, self).__init__(*args, **kwargs)

        # Populate available labels
        host_uuid = kwargs['initial']['host_uuid']

        labels = stx_api.sysinv.host_label_list(self.request,
                                                host_uuid)

        current_labels = [label.label_key for label in labels]
        available_labels_list = []
        for label_key in LABEL_KEY_CHOICES:
            if label_key[0] not in current_labels:
                available_labels_list.append(label_key)
        self.fields['labelkey'].choices = available_labels_list

    def clean(self):
        cleaned_data = super(AssignLabel, self).clean()
        return cleaned_data

    def handle(self, request, data):
        labelkey = data['labelkey'][:]
        clabelkey = data['clabelkey']
        clabelvalue = data['clabelvalue']

        attributes = {}
        if labelkey == LABEL_KEY_CUSTOM:
            if not clabelvalue:
                clabelvalue = "enabled"
            attributes[clabelkey] = clabelvalue
        else:
            attributes[labelkey] = "enabled"
        try:
            new_labels = stx_api.sysinv.host_label_assign(
                request,
                data['host_uuid'],
                attributes)

            # Check if the label is successfully assigned
            if not new_labels.labels:
                raise exc.ClientException(
                    "Label Not Created: %s" % labelkey)
            uuid = new_labels.labels[0]['uuid']
            label_obj = stx_api.sysinv.host_label_get(
                request,
                uuid)

            msg = _('Label "%s" was successfully created.') % \
                getattr(label_obj, 'label_key')
            LOG.debug(msg)
            messages.success(request, msg)
            return label_obj
        except exc.HTTPNotFound:
            msg = _("Label Not Created: %s") % labelkey
            LOG.error(msg)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[data['host_id']])
            return shortcuts.redirect(redirect)
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[data['host_id']])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _('Failed to assign label "%(label)s" to "%(uuid)s".') % \
                {'label': labelkey, 'uuid': data['host_uuid']}
            LOG.error(msg)
            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)
