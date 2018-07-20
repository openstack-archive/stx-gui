# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2015-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.core.urlresolvers import reverse  # noqa
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables
from openstack_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import forms

from openstack_dashboard.api import sysinv


class ParamEdit(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:inventory:storages:lvg:edit"
    classes = ("btn-edit", "ajax-modal")

    def get_link_url(self, params):
        return reverse(self.url, args=[self.table.kwargs['lvg_id'],
                                       params.key])


def get_parameters_name(datum):
    return forms.get_param_key_name(datum.key)


def get_parameters_value(datum):
    if datum is None or datum.value is None:
        return None
    if datum.key == sysinv.LVG_NOVA_PARAM_INSTANCES_SIZE_MIB:
        value = datum.value
    if datum.key == sysinv.LVG_NOVA_PARAM_BACKING:
        value = datum.value
    if datum.key == sysinv.LVG_NOVA_PARAM_DISK_OPS:
        value = datum.value
    if datum.key == sysinv.LVG_CINDER_PARAM_LVM_TYPE:
        value = datum.value
    return value


class ParamsTable(tables.DataTable):
    name = tables.Column(get_parameters_name,
                         verbose_name=_('Name'))
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column(get_parameters_value,
                          verbose_name=_('Value'),
                          filters=[filters.linebreaksbr])

    class Meta(object):
        name = "params"
        verbose_name = _("Parameters")
        row_actions = (ParamEdit,)

    def get_object_id(self, datum):
        return datum.key

    def get_object_display(self, datum):
        return datum.key
