#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.inventory.interfaces.address import \
    tables as address_tables
from openstack_dashboard.dashboards.admin.inventory.interfaces.forms import \
    AddInterface
from openstack_dashboard.dashboards.admin.inventory.interfaces.forms import \
    AddInterfaceProfile
from openstack_dashboard.dashboards.admin.inventory.interfaces.forms import \
    UpdateInterface
from openstack_dashboard.dashboards.admin.inventory.interfaces.route import \
    tables as route_tables

LOG = logging.getLogger(__name__)


def get_port_data(request, host_id, interface=None):
    port_data = []
    show_all_ports = True

    try:
        if not interface:
            # Create case, host id is not UUID. Need to get the UUID in order
            # to retrieve the ports for this host
            host = api.sysinv.host_get(request, host_id)
            host_id = host.uuid
        else:
            if not interface.uses:
                show_all_ports = False

        port_list = \
            api.sysinv.host_port_list(request, host_id)

        if show_all_ports:
            # This is either a create or edit non-default interface
            # operation. Get the list of available ports and their
            # neighbours
            neighbour_list = \
                api.sysinv.host_lldpneighbour_list(request, host_id)
            interface_list = api.sysinv.host_interface_list(request, host_id)

            for p in port_list:
                port_info = "%s (%s, %s, " % (p.get_port_display_name(),
                                              p.mac, p.pciaddr)
                interface_name = ''
                for i in interface_list:
                    if p.interface_uuid == i.uuid:
                        interface_name = i.ifname

                if interface_name:
                    port_info += interface_name + ")"
                else:
                    port_info += _("none") + ")"

                if p.bootp:
                    port_info += " - bootif"

                neighbour_info = []
                for n in neighbour_list:
                    if p.uuid == n.port_uuid:
                        if n.port_description:
                            neighbour = "%s (%s)" % (
                                n.port_identifier, n.port_description)
                        else:
                            neighbour = "%s" % n.port_identifier
                        neighbour_info.append(neighbour)
                neighbour_info.sort()
                port_data_item = port_info, neighbour_info
                port_data.append(port_data_item)
        else:
            # Edit default-interface operation
            for p in port_list:
                # Since the port->default interface mapping is now strictly
                # 1:1, the below condition can only be met at most once for
                # the available ports
                if p.interface_uuid == interface.uuid:
                    port_info = "%s (%s, %s, %s)" % (
                        p.get_port_display_name(), p.mac, p.pciaddr,
                        interface.ifname)

                    if p.bootp:
                        port_info += " - bootif"
                    # Retrieve the neighbours for the port
                    neighbours = \
                        api.sysinv.port_lldpneighbour_list(request, p.uuid)
                    neighbour_info = []
                    if neighbours:
                        for n in neighbours:
                            if n.port_description:
                                neighbour = "%s (%s)" % (
                                    n.port_identifier, n.port_description)
                            else:
                                neighbour = "%s\n" % n.port_identifier
                            neighbour_info.append(neighbour)
                    neighbour_info.sort()
                    port_data_item = port_info, neighbour_info
                    port_data.append(port_data_item)
    except Exception:
        redirect = reverse('horizon:admin:inventory:index')
        exceptions.handle(request,
                          _('Unable to retrieve port info details for host '
                            '"%s".') % host_id, redirect=redirect)

    return port_data


class AddInterfaceView(forms.ModalFormView):
    form_class = AddInterface
    template_name = 'admin/inventory/interfaces/create.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddInterfaceView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        context['ports'] = get_port_data(self.request, self.kwargs['host_id'])
        return context

    def get_initial(self):
        initial = super(AddInterfaceView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = api.sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['host'] = host

        # get SDN configuration status
        try:
            sdn_enabled = api.sysinv.get_sdn_enabled(self.request)
            sdn_l3_mode = api.sysinv.get_sdn_l3_mode_enabled(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve SDN configuration.'))
        initial['sdn_enabled'] = sdn_enabled
        initial['sdn_l3_mode_enabled'] = sdn_l3_mode
        return initial


class AddInterfaceProfileView(forms.ModalFormView):
    form_class = AddInterfaceProfile
    template_name = 'admin/inventory/interfaces/createprofile.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_myhost_data(self):
        if not hasattr(self, "_host"):
            host_id = self.kwargs['host_id']
            try:
                host = api.sysinv.host_get(self.request, host_id)

                all_ports = api.sysinv.host_port_list(self.request, host.uuid)
                host.ports = [p for p in all_ports if p.interface_uuid]
                for p in host.ports:
                    p.namedisplay = p.get_port_display_name()

                host.interfaces = api.sysinv.host_interface_list(self.request,
                                                                 host.uuid)
                for i in host.interfaces:
                    i.ports = [p.get_port_display_name()
                               for p in all_ports if
                               p.interface_uuid and p.interface_uuid == i.uuid]
                    i.ports = ", ".join(i.ports)
                    i.uses = ", ".join(i.uses)

            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'host "%s".') % host_id,
                                  redirect=redirect)
            self._host = host
        return self._host

    def get_context_data(self, **kwargs):
        context = super(AddInterfaceProfileView, self).get_context_data(
            **kwargs)
        context['host_id'] = self.kwargs['host_id']
        context['host'] = self.get_myhost_data()
        return context

    def get_initial(self):
        initial = super(AddInterfaceProfileView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        return initial


class UpdateView(forms.ModalFormView):
    form_class = UpdateInterface
    template_name = 'admin/inventory/interfaces/update.html'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            interface_id = self.kwargs['interface_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = api.sysinv.host_interface_get(self.request,
                                                             interface_id)
                self._object.host_id = host_id

            except Exception:
                redirect = reverse("horizon:project:networks:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve interface details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        interface = self._get_object()
        context['interface_id'] = interface.uuid
        context['host_id'] = interface.host_id
        ports = get_port_data(self.request, interface.ihost_uuid, interface)
        if ports:
            context['ports'] = ports
        return context

    def get_initial(self):
        interface = self._get_object()
        networktype = []
        if interface.networktype:
            for network in interface.networktype.split(","):
                networktype.append(str(network))
        providernetworks = []
        if interface.providernetworks:
            for pn in interface.providernetworks.split(","):
                providernetworks.append(str(pn))
        try:
            host = api.sysinv.host_get(self.request, interface.host_id)
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))

        # get SDN configuration status
        try:
            sdn_enabled, sdn_l3_mode = False, False
            sdn_enabled = api.sysinv.get_sdn_enabled(self.request)
            sdn_l3_mode = api.sysinv.get_sdn_l3_mode_enabled(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve SDN configuration.'))

        return {'id': interface.uuid,
                'host_id': interface.host_id,
                'host': host,
                'ihost_uuid': interface.ihost_uuid,
                'ifname': interface.ifname,
                'iftype': interface.iftype,
                'aemode': interface.aemode,
                'txhashpolicy': interface.txhashpolicy,
                # 'ports': interface.ports,
                # 'uses': interface.uses,
                'networktype': networktype,
                'providernetworks_data': providernetworks,
                'providernetworks_data-external': providernetworks,
                'providernetworks_pci': providernetworks,
                'providernetworks_sriov': providernetworks,
                'sriov_numvfs': interface.sriov_numvfs,
                'imtu': interface.imtu,
                'ipv4_mode': getattr(interface, 'ipv4_mode', 'disabled'),
                'ipv4_pool': getattr(interface, 'ipv4_pool', None),
                'ipv6_mode': getattr(interface, 'ipv6_mode', 'disabled'),
                'ipv6_pool': getattr(interface, 'ipv6_pool', None),
                'sdn_enabled': sdn_enabled,
                'sdn_l3_mode_enabled': sdn_l3_mode}


class DetailView(tables.MultiTableView):
    table_classes = (address_tables.AddressTable,
                     route_tables.RouteTable)
    template_name = 'admin/inventory/interfaces/detail.html'
    failure_url = reverse_lazy('horizon:admin:inventory:detail')
    page_title = "{{ interface.ifname }}"

    def get_addresses_data(self):
        try:
            interface_id = self.kwargs['interface_id']
            addresses = api.sysinv.address_list_by_interface(
                self.request, interface_id=interface_id)
            addresses.sort(key=lambda f: (f.address, f.prefix))
        except Exception:
            addresses = []
            msg = _('Address list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return addresses

    def get_routes_data(self):
        try:
            interface_id = self.kwargs['interface_id']
            routes = api.sysinv.route_list_by_interface(
                self.request, interface_id=interface_id)
            routes.sort(key=lambda f: (f.network, f.prefix))
        except Exception:
            routes = []
            msg = _('Route list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return routes

    def _get_address_pools(self):
        pools = api.sysinv.address_pool_list(self.request)
        return {p.uuid: p for p in pools}

    def _add_pool_names(self, interface):
        pools = self._get_address_pools()
        if getattr(interface, 'ipv4_mode', '') == 'pool':
            interface.ipv4_pool_name = pools[interface.ipv4_pool].name
        if getattr(interface, 'ipv6_mode', '') == 'pool':
            interface.ipv6_pool_name = pools[interface.ipv6_pool].name
        return interface

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            interface_id = self.kwargs['interface_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = api.sysinv.host_interface_get(self.request,
                                                             interface_id)
                self._object.host_id = host_id
                self._object = self._add_pool_names(self._object)
            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve interface details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        interface = self._get_object()

        hostname = self.get_hostname(interface.host_id)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(interface.host_id,))),
            (_("Interfaces"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context['interface_id'] = interface.uuid
        context['host_id'] = interface.host_id
        context['interface'] = interface
        return context
