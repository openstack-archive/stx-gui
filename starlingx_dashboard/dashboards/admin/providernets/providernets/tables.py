# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#


import logging
from operator import itemgetter  # noqa

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy

from neutronclient.common import exceptions as neutron_exceptions

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class DeleteProviderNetwork(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Provider Network",
            u"Delete Provider Networks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Provider Network",
            u"Deleted Provider Networks",
            count
        )

    def delete(self, request, obj_id):
        try:
            api.neutron.provider_network_delete(request, obj_id)
        except neutron_exceptions.NeutronClientException as e:
            LOG.info(e.message)
            redirect = reverse('horizon:admin:providernets:index')
            exceptions.handle(request, e.message, redirect=redirect)
        except Exception:
            msg = _('Failed to delete provider network %s') % obj_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:providernets:index')
            exceptions.handle(request, msg, redirect=redirect)


class CreateProviderNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Provider Network")
    url = "horizon:admin:providernets:providernets:create"
    classes = ("ajax-modal", "btn-create")


class EditProviderNetwork(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Provider Network")
    url = "horizon:admin:providernets:providernets:update"
    classes = ("ajax-modal", "btn-edit")


class AddProviderNetworkRange(tables.LinkAction):
    name = "addrange"
    verbose_name = _("Create Segmentation Range")
    url = "horizon:admin:providernets:providernets:addrange"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, providernet):
        if providernet:
            return providernet.type not in ('flat')
        return super(AddProviderNetworkRange, self).allowed(request,
                                                            providernet)


class ProviderNetworksFilterAction(tables.FilterAction):
    def filter(self, table, providernets, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [providernet for providernet in providernets
                if q in providernet.name.lower()]


def _format_providernet_ranges(data):
    ranges = data['ranges']
    if not ranges:
        return '-'
    return ", ".join(["{}-{}".format(r['minimum'], r['maximum'])
                      if r['minimum'] != r['maximum']
                      else "{}".format(r['minimum'])
                      for r in sorted(ranges, key=itemgetter('minimum'))])


class ProviderNetworksTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Network Name"),
                         link='horizon:admin:providernets:providernets:detail')
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True)
    type = tables.Column("type", verbose_name=_("Type"))
    mtu = tables.Column("mtu", verbose_name=_("MTU"))
    ranges = tables.Column(transform=_format_providernet_ranges,
                           verbose_name=_("Segmentation Ranges"))
    vlan_transparent = tables.Column("vlan_transparent",
                                     verbose_name=_("VLAN Transparent"))

    class Meta(object):
        name = "provider_networks"
        verbose_name = _("Provider Networks")
        status_columns = ["status"]
        table_actions = (CreateProviderNetwork, DeleteProviderNetwork,
                         ProviderNetworksFilterAction)
        row_actions = (EditProviderNetwork,
                       DeleteProviderNetwork,
                       AddProviderNetworkRange)


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
