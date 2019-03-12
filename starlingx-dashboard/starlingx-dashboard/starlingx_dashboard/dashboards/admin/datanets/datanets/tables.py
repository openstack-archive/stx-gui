# Copyright 2012 NEC Corporation
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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from cgtsclient import exc as sysinv_exceptions

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class DeleteDataNetwork(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Data Network",
            "Delete Data Networks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Data Network",
            "Deleted Data Networks",
            count
        )

    def delete(self, request, obj_id):
        try:
            stx_api.sysinv.data_network_delete(request, obj_id)
        except sysinv_exceptions.CgtsclientException as e:
            LOG.info(str(e))
            redirect = reverse('horizon:admin:datanets:index')
            exceptions.handle(request, str(e), redirect=redirect)
        except Exception:
            msg = _('Failed to delete data network %s') % obj_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:datanets:index')
            exceptions.handle(request, msg, redirect=redirect)


class CreateDataNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Data Network")
    url = "horizon:admin:datanets:datanets:create"
    classes = ("ajax-modal", "btn-create")


class EditDataNetwork(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Data Network")
    url = "horizon:admin:datanets:datanets:update"
    classes = ("ajax-modal", "btn-edit")


class DataNetworksFilterAction(tables.FilterAction):
    def filter(self, table, datanets, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [dn for dn in datanets if q in dn.name.lower()]


def _format_providernet_ranges(data):
    # TODO(datanetworks): update ranges based upon Stein spec
    return '-'


class DataNetworksTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Network Name"),
                         link='horizon:admin:datanets:datanets:detail')
    type = tables.Column("network_type", verbose_name=_("Type"))
    mtu = tables.Column("mtu", verbose_name=_("MTU"))
    ranges = tables.Column(transform=_format_providernet_ranges,
                           verbose_name=_("Segmentation Ranges"))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "data_networks"
        verbose_name = _("Data Networks")
        table_actions = (CreateDataNetwork, DeleteDataNetwork,
                         DataNetworksFilterAction)
        row_actions = (EditDataNetwork,
                       DeleteDataNetwork)


def _get_link_url(datum):
    link = 'horizon:admin:networks:detail'
    return reverse(link, args=(datum.id,))


def _get_segmentation_id(datum):
    if datum.providernet_type.lower() == "flat":
        return _("n/a")
    return datum.segmentation_id


class ProviderNetworkTenantNetworkTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"),
                         link=_get_link_url)
    vlan_id = tables.Column("vlan_id", verbose_name=_("VLAN"))
    type = tables.Column("providernet_type", verbose_name=_("Type"))
    segmentation_id = tables.Column(_get_segmentation_id,
                                    verbose_name=_("Segmentation ID"))

    def get_object_id(self, datum):
        # Generate a unique object id that takes in to consideration the
        # providernet type, the vlan_id as well as the network id
        return "{}-{}-{}".format(datum.id, datum.providernet_type,
                                 datum.vlan_id)

    class Meta(object):
        name = "tenant_networks"
        verbose_name = _("Tenant Networks")
