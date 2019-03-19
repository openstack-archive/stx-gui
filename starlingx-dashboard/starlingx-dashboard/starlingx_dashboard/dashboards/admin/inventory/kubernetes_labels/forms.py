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

    labelkey = forms.CharField(
        label=_("Label Key"),
        required=True)

    labelvalue = forms.CharField(
        label=_("Label Value"),
        required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AssignLabel, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AssignLabel, self).clean()
        return cleaned_data

    def handle(self, request, data):
        labelkey = data['labelkey']
        labelvalue = data['labelvalue']
        attributes = {}
        attributes[labelkey] = labelvalue
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
