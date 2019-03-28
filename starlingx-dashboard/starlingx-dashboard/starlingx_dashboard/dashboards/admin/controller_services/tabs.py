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
#  Copyright (c) 2019 Wind River Systems, Inc.
#
#  SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from starlingx_dashboard.api import iservice
from starlingx_dashboard.api import sysinv as sysinv_api
from starlingx_dashboard.dashboards.admin.controller_services import tables
from starlingx_dashboard.utils import objectify

import logging

LOG = logging.getLogger(__name__)


class ControllerServicesTab(tabs.TableTab):
    table_classes = (tables.ControllerServicesTable,)
    name = _("Controller Services")
    slug = "controller_services"
    template_name = ("horizon/common/_detail_table.html")

    def _find_service_group_names(self, sdas):
        service_group_names_set = set()
        for sda in sdas:
            service_group_names_set.add(sda.service_group_name)

        service_group_names_list = list(service_group_names_set)

        return service_group_names_list

    def _update_service_group_states(self, service_group_name, sdas, nodes):
        entry = {}

        for sda in sdas:
            for n in nodes:
                if n.name == sda.node_name:
                    if n.administrative_state.lower() == "locked":
                        dstate = "locked"
                    elif n.operational_state.lower() == "enabled":
                        dstate = "standby"
                    else:
                        dstate = n.operational_state.lower()

            if sda.service_group_name == service_group_name:
                state_str = sda.state
                if sda.status != "":
                    state_str += '-' + sda.status
                    if sda.condition != "":
                        state_str += ' [' + sda.condition + ']'

                if sda.state == "active":
                    if sda.node_name == "controller-0":
                        entry.update({'c0_activity': 'active'})
                        entry.update({'c0_hostname': sda.node_name})
                        entry.update({'c0_state': state_str})
                    elif sda.node_name == "controller-1":
                        entry.update({'c1_activity': 'active'})
                        entry.update({'c1_hostname': sda.node_name})
                        entry.update({'c1_state': state_str})
                else:
                    if dstate == "standby":
                        dstate = state_str

                    if sda.node_name == "controller-0":
                        entry.update({'c0_activity': sda.state})
                        entry.update({'c0_hostname': sda.node_name})
                        entry.update({'c0_state': dstate})
                    elif sda.node_name == "controller-1":
                        entry.update({'c1_activity': sda.state})
                        entry.update({'c1_hostname': sda.node_name})
                        entry.update({'c1_state': dstate})

        return entry

    def get_controller_services_data(self):
        """Populate the data for the controller services tab"""

        # Here we filter the controller-1 column if we're a simplex system
        # We should make this data driven in the future. This would allow us to
        # more easily support n controllers
        if sysinv_api.is_system_mode_simplex(self.tab_group.request):
            controller1_col = self._tables['controller_services'].columns['c1']
            controller1_col.classes.append("hide")

        try:
            nodes = iservice.sm_nodes_list(self.tab_group.request)

            sdas = iservice.sm_sda_list(self.tab_group.request)

            services = []

            sgs = self._find_service_group_names(sdas)

            sdaid = 0
            for sg in sgs:
                sdaid += 1
                entry = {}
                entry.update({'id': sdaid})
                entry.update({'servicename': sg})
                sg_states = self._update_service_group_states(sg, sdas, nodes)
                entry.update(sg_states)

                # Need to latch if any sg is enabled
                if 'c0_activity' in entry.keys():
                    sgstate = entry['c0_activity']
                    if sgstate == "active":
                        entry.update({'sgstate': sgstate})
                elif 'c1_activity' in entry.keys():
                    sgstate = entry['c1_activity']
                    if sgstate == "active":
                        entry.update({'sgstate': sgstate})

                if sgstate != "active":
                    entry.update({'sgstate': sgstate})

                if entry != {}:
                    entry_object = objectify.objectify(entry)
                    services.append(entry_object)

        except Exception:
            msg = _('Unable to get controller services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

        return services
