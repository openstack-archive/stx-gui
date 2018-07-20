#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

import cpu_functions.utils as icpu_utils
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon import workflows
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.inventory.tabs import HostDetailTabs
from openstack_dashboard.dashboards.admin.inventory.tabs import InventoryTabs
from openstack_dashboard.dashboards.admin.inventory.workflows import AddHost
from openstack_dashboard.dashboards.admin.inventory.workflows import UpdateHost


LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = InventoryTabs
    template_name = 'admin/inventory/index.html'
    page_title = _("Host Inventory")

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)


class AddView(workflows.WorkflowView):
    workflow_class = AddHost
    template_name = 'admin/inventory/create.html'
    success_url = reverse_lazy('horizon:admin:inventory:index')

    def get_initial(self):

        return {'hostname': "",
                'personality': "",
                'subfunctions': "",
                'mgmt_mac': "",
                'bm_type': api.sysinv.BM_TYPE_NULL,
                'bm_ip': "",
                'bm_username': ""}


class UpdateView(workflows.WorkflowView):
    workflow_class = UpdateHost
    template_name = 'admin/inventory/update.html'
    success_url = reverse_lazy('horizon:admin:inventory:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        try:
            host = api.sysinv.host_get(self.request, self.kwargs['host_id'])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve host data."))

        return {'host_id': host.id,
                'hostname': host.hostname,
                'personality': host._personality,
                'subfunctions': host._subfunctions,
                'location': host.location,
                'bm_type': host.bm_type,
                'bm_ip': host.bm_ip,
                'bm_username': host.bm_username,
                'ttys_dcd': host.ttys_dcd,
                'pers_subtype': getattr(host,
                                        'capabilities',
                                        {}).get('pers_subtype', "")}


class DetailView(tabs.TabbedTableView):
    tab_group_class = HostDetailTabs
    template_name = 'admin/inventory/detail.html'
    page_title = '{{ _("Host Detail: ")|add:host.hostname' \
                 '|default:_("Unprovisioned Host Detail") }}'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["host"] = self.get_data()
        return context

    # Make the LVG/PV state data clearer to the end user
    def _adjust_state_data(self, state, name):
        adjustment = ''
        if state in [api.sysinv.PV_ADD, api.sysinv.PV_DEL]:
            if name == api.sysinv.LVG_CGTS_VG:
                adjustment = ' (now)'
            elif name == api.sysinv.LVG_CINDER_VOLUMES:
                adjustment = ' (with backend)'
            elif name == api.sysinv.LVG_NOVA_LOCAL:
                adjustment = ' (on unlock)'
        return state + adjustment

    def get_data(self):
        if not hasattr(self, "_host"):
            host_id = self.kwargs['host_id']
            try:
                host = api.sysinv.host_get(self.request, host_id)

                host.nodes = api.sysinv.host_node_list(self.request, host.uuid)
                host.cpus = api.sysinv.host_cpu_list(self.request, host.uuid)
                icpu_utils.restructure_host_cpu_data(host)

                host.memorys = api.sysinv.host_memory_list(self.request,
                                                           host.uuid)
                for m in host.memorys:
                    for n in host.nodes:
                        if m.inode_uuid == n.uuid:
                            m.numa_node = n.numa_node
                            break

                host.ports = api.sysinv.host_port_list(self.request, host.uuid)
                host.interfaces = api.sysinv.host_interface_list(self.request,
                                                                 host.uuid)
                host.devices = api.sysinv.host_device_list(self.request,
                                                           host.uuid)
                host.disks = api.sysinv.host_disk_list(self.request, host.uuid)
                host.stors = api.sysinv.host_stor_list(self.request, host.uuid)
                host.pvs = api.sysinv.host_pv_list(self.request, host.uuid)
                host.partitions = api.sysinv.host_disk_partition_list(
                    self.request, host.uuid)

                # Translate partition state codes:
                for p in host.partitions:
                    p.status = api.sysinv.PARTITION_STATUS_MSG[p.status]

                host.lldpneighbours = \
                    api.sysinv.host_lldpneighbour_list(self.request, host.uuid)

                # Set the value for neighbours field for each port in the host.
                # This will be referenced in Interfaces table
                for p in host.ports:
                    p.neighbours = \
                        [n.port_identifier for n in host.lldpneighbours
                         if n.port_uuid == p.uuid]

                # Adjust pv state to be more "user friendly"
                for pv in host.pvs:
                    pv.pv_state = self._adjust_state_data(pv.pv_state,
                                                          pv.lvm_vg_name)

                host.lvgs = api.sysinv.host_lvg_list(self.request, host.uuid,
                                                     get_params=True)

                # Adjust lvg state to be more "user friendly"
                for lvg in host.lvgs:
                    lvg.vg_state = self._adjust_state_data(lvg.vg_state,
                                                           lvg.lvm_vg_name)

                host.sensors = api.sysinv.host_sensor_list(self.request,
                                                           host.uuid)
                host.sensorgroups = api.sysinv.host_sensorgroup_list(
                    self.request, host.uuid)

                # Add patching status data to hosts
                phost = api.patch.get_host(self.request, host.hostname)
                if phost is not None:
                    if phost.interim_state is True:
                        host.patch_current = "Pending"
                    elif phost.patch_failed is True:
                        host.patch_current = "Failed"
                    else:
                        host.patch_current = phost.patch_current
                    host.requires_reboot = "Yes" if phost.requires_reboot \
                        else "No"
                    host._patch_state = phost.state
                    host.allow_insvc_patching = phost.allow_insvc_patching

            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'host "%s".') % host_id,
                                  redirect=redirect)
            self._host = host
        return self._host

    def get_tabs(self, request, *args, **kwargs):
        host = self.get_data()
        return self.tab_group_class(request, host=host, **kwargs)
