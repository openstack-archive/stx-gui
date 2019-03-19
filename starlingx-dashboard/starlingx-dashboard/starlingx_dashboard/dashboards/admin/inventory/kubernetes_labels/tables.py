#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2019 Wind River Systems, Inc.
# Copyright (C) 2019 Intel Corporation
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


def host_locked(host=None):
    if not host:
        return False
    return host._administrative == 'locked'


class AssignKubeLabel(tables.LinkAction):
    name = "assignKubelabel"
    verbose_name = _("Assign Kube Label")
    url = "horizon:admin:inventory:assignlabel"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        return host_locked(host)


class RemoveLabel(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Label",
            "Delete Labels",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Label",
            "Deleted Labels",
            count
        )

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        return host_locked(host)

    def delete(self, request, label_id):
        host_id = self.table.kwargs['host_id']
        try:
            stx_api.sysinv.host_label_remove(request, label_id)
        except Exception:
            msg = _('Failed to delete host %(hid)s label %(lid)s') % {
                'hid': host_id, 'lid': label_id}
            LOG.error(msg)
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class LabelTable(tables.DataTable):
    uuid = tables.Column('uuid',
                         verbose_name=_('UUID'))

    label_key = tables.Column('label_key',
                              verbose_name=_('Label Key'))

    label_value = tables.Column('label_value',
                                verbose_name=_('Label Value'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "labels"
        verbose_name = _("Label")
        multi_select = False
        row_actions = (RemoveLabel, )
        table_actions = (AssignKubeLabel, )
