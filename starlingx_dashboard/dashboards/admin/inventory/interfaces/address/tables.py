# Copyright 2015-2018 Wind River Systems, Inc
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
from openstack_dashboard import api

LOG = logging.getLogger(__name__)

ALLOWED_INTERFACE_TYPES = ['infra', 'data', 'control']


class DeleteAddress(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Address",
            u"Delete Addresses",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Address",
            u"Deleted Addresses",
            count
        )

    def get_redirect_url(self):
        host_id = self.table.kwargs['host_id']
        interface_id = self.table.kwargs['interface_id']
        return reverse('horizon:admin:inventory:viewinterface',
                       args=[host_id, interface_id])

    def delete(self, request, obj_id):
        try:
            api.sysinv.address_delete(request, obj_id)
        except Exception:
            exceptions.handle(request, redirect=self.get_redirect_url())


class CreateAddress(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Address")
    url = "horizon:admin:inventory:addaddress"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum=None):
        interface_id = self.table.kwargs['interface_id']
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, interface_id))

    def allowed(self, request, datum=None):
        interface = self.table.get_interface()
        if not interface:
            return False

        if interface.networktype:
            supported = interface.networktype.split(',')
            if any(t in supported for t in ALLOWED_INTERFACE_TYPES):
                return True
        if getattr(interface, 'ipv4_mode', '') == 'static':
            return True
        if getattr(interface, 'ipv6_mode', '') == 'static':
            return True
        return False


def get_address_column(address):
    ip_address = getattr(address, 'address')
    prefix = getattr(address, 'prefix')
    return ip_address + '/' + str(prefix)


class AddressTable(tables.DataTable):
    address = tables.Column(get_address_column,
                            verbose_name=_("Address"))
    enable_dad = tables.Column("enable_dad",
                               verbose_name=_("DAD"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return ("%(address)s/%(prefix)s" %
                {'address': datum.address,
                 'prefix': datum.prefix})

    class Meta(object):
        name = "addresses"
        verbose_name = _("Address List")
        table_actions = (CreateAddress, DeleteAddress)
        row_actions = (DeleteAddress,)

    def get_interface(self):
        if not hasattr(self, "_interface"):
            try:
                interface_id = self.kwargs["interface_id"]
                self._interface = api.sysinv.host_interface_get(
                    self.request, interface_id)
            except Exception:
                redirect = reverse(self.failure_url,
                                   args=(self.kwargs['host_id'],
                                         self.kwargs['interface_id'],))
                msg = _("Unable to retrieve interface details.")
                exceptions.handle(self.request, msg, redirect=redirect)
                return
        return self._interface

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(AddressTable, self).__init__(
            request, data=data, needs_form_wrapper=needs_form_wrapper,
            **kwargs)
