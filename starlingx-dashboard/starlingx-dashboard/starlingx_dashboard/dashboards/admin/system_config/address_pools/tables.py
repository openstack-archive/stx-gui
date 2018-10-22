# Copyright 2015 Wind River Systems, Inc
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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class DeleteAddressPool(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Address Pool",
            "Delete Address Pools",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Address Pool",
            "Deleted Address Pools",
            count
        )

    def get_redirect_url(self):
        return reverse('horizon:admin:system_config:index')

    def delete(self, request, obj_id):
        try:
            stx_api.sysinv.address_pool_delete(request, obj_id)
        except Exception:
            exceptions.handle(request, redirect=self.get_redirect_url())


class CreateAddressPool(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Address Pool")
    url = "horizon:admin:system_config:addaddrpool"
    classes = ("ajax-modal",)
    icon = "plus"


class UpdateAddressPool(tables.LinkAction):
    name = "update"
    verbose_name = _("Update Address Pool")
    url = "horizon:admin:system_config:updateaddrpool"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, pool):
        return reverse(self.url, args=(pool.uuid,))


def get_network_column(pool):
    ip_network = getattr(pool, 'network')
    prefix = getattr(pool, 'prefix')
    return ip_network + '/' + str(prefix)


def get_ranges_column(pool):
    return ", ".join(['%s-%s' % (str(r[0]), str(r[1])) for r in pool.ranges])


class AddressPoolsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    network = tables.Column(get_network_column,
                            verbose_name=_("Network"))
    order = tables.Column("order", verbose_name=_("Allocation Order"))
    ranges = tables.Column(get_ranges_column, verbose_name=_("Address Ranges"))

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return ("%(network)s/%(prefix)s" %
                {'network': datum.network,
                 'prefix': datum.prefix})

    class Meta(object):
        name = "address_pools"
        verbose_name = _("Address Pools")
        table_actions = (CreateAddressPool, DeleteAddressPool)
        row_actions = (UpdateAddressPool, DeleteAddressPool)
