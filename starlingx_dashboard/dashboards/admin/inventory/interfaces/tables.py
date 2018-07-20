#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api

LOG = logging.getLogger(__name__)

NETWORK_TYPES = ["oam", "infra", "mgmt", "pxeboot"]


class DeleteInterface(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Interface",
            u"Delete Interfaces",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Interface",
            u"Deleted Interfaces",
            count
        )

    def allowed(self, request, interface=None):
        host = self.table.kwargs['host']
        return (host._administrative == 'locked' and
                interface.iftype != 'ethernet')

    def delete(self, request, interface_id):
        host_id = self.table.kwargs['host_id']
        try:
            api.sysinv.host_interface_delete(request, interface_id)
        except Exception:
            msg = _('Failed to delete host %(hid)s interface %(iid)s') % {
                'hid': host_id, 'iid': interface_id}
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class CreateInterfaceProfile(tables.LinkAction):
    name = "createProfile"
    verbose_name = _("Create Interface Profile")
    url = "horizon:admin:inventory:addinterfaceprofile"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        return not api.sysinv.is_system_mode_simplex(request)


class CreateInterface(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Interface")
    url = "horizon:admin:inventory:addinterface"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']

        if host._administrative != 'locked':
            return False

        count = 0
        for i in host.interfaces:
            if i.networktype:
                count = count + 1

        if host.subfunctions and 'compute' not in host.subfunctions and \
                count >= len(NETWORK_TYPES):
            return False

        return True


class EditInterface(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Interface")
    url = "horizon:admin:inventory:editinterface"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, interface=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, interface.uuid))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        return host._administrative == 'locked'


def get_attributes(interface):
    attr_str = "MTU=%s" % interface.imtu
    if interface.iftype == 'ae':
        attr_str = "%s, AE_MODE=%s" % (attr_str, interface.aemode)
        if interface.aemode in ['balanced', '802.3ad']:
            attr_str = "%s, AE_XMIT_HASH_POLICY=%s" % (
                attr_str, interface.txhashpolicy)
    if (interface.networktype and
            any(network in ['data', 'data-external'] for network in
                interface.networktype.split(","))):
        attrs = [attr.strip() for attr in attr_str.split(",")]
        for a in attrs:
            if 'accelerated' in a:
                attrs.remove(a)
        attr_str = ",".join(attrs)

        if False in interface.dpdksupport:
            attr_str = "%s, accelerated=%s" % (attr_str, 'False')
        else:
            attr_str = "%s, accelerated=%s" % (attr_str, 'True')
    return attr_str


def get_ports(interface):
    port_str_list = ", ".join(interface.portNameList)
    return port_str_list


def get_port_neighbours(interface):
    return interface.portNeighbourList


def get_uses(interface):
    uses_list = ", ".join(interface.uses)
    return uses_list


def get_used_by(interface):
    used_by_list = ", ".join(interface.used_by)
    return used_by_list


def get_link_url(interface):
    return reverse("horizon:admin:inventory:viewinterface",
                   args=(interface.host_id, interface.uuid))


class InterfacesTable(tables.DataTable):
    ifname = tables.Column('ifname',
                           verbose_name=_('Name'),
                           link=get_link_url)

    networktype = tables.Column('networktype',
                                verbose_name=_('Network Type'))

    iftype = tables.Column('iftype',
                           verbose_name=_('Type'))

    vlan_id = tables.Column('vlan_id',
                            verbose_name=_('Vlan ID'))

    ports = tables.Column(get_ports,
                          verbose_name=_('Port'))

    port_neighbours = tables.Column(get_port_neighbours,
                                    verbose_name=_('Neighbors'),
                                    wrap_list=True,
                                    filters=(filters.unordered_list,))

    uses = tables.Column(get_uses,
                         verbose_name=_('Uses'))

    used_by = tables.Column(get_used_by,
                            verbose_name=_('Used By'))

    providernetworks = tables.Column('providernetworks',
                                     verbose_name=_('Provider Network(s)'))
    attributes = tables.Column(get_attributes,
                               verbose_name=_('Attributes'))

    def __init__(self, *args, **kwargs):
        super(InterfacesTable, self).__init__(*args, **kwargs)

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.ifname

    class Meta(object):
        name = "interfaces"
        verbose_name = _("Interfaces")
        multi_select = False
        table_actions = (CreateInterfaceProfile, CreateInterface,)
        row_actions = (EditInterface, DeleteInterface,)
