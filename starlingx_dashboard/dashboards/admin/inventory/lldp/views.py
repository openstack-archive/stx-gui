#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon.utils import memoized
from horizon import views

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class DetailNeighbourView(views.HorizonTemplateView):
    template_name = 'admin/inventory/_detail_neighbour.html'
    page_title = "{{ localportname }}"

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            neighbour_uuid = self.kwargs['neighbour_uuid']
            try:
                self._object = \
                    stx_api.sysinv.host_lldpneighbour_get(self.request,
                                                          neighbour_uuid)

            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                msg = _('Unable to retrieve LLDP neighbor details "%s".') \
                    % neighbour_uuid
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(DetailNeighbourView, self).get_context_data(**kwargs)
        # Context "neighbour" is referenced in _detail_neighbour.html
        # Reformat some attributes for better display
        neighbour = self._get_object()
        context['localportname'] = neighbour.get_local_port_display_name()
        if neighbour.system_capabilities:
            context['systemcaps'] = \
                neighbour.system_capabilities.replace(',', '\n')
        if neighbour.dot1_proto_vids:
            context['dot1provids'] = \
                neighbour.dot1_proto_vids.replace(',', '\n')
        if neighbour.dot1_vlan_names:
            context['vlannames'] = neighbour.dot1_vlan_names.replace(',', '\n')
        if neighbour.dot1_proto_ids:
            context['dot1protoids'] = \
                neighbour.dot1_proto_ids.replace(',', '\n')
        if neighbour.dot1_lag:
            context['dot1lag'] = neighbour.dot1_lag.replace(',', '\n')
        if neighbour.dot3_mac_status:
            # The dot3_mac_status has irregular format. An example is
            # auto-negotiation-capable=y,auto-negotiation-enabled=y,capability
            # =10-base-t-fd,100-base-t4,1000-base-t-fd,mau-type=4-pair-
            # category-5-utp-fd
            status_list = neighbour.dot3_mac_status.split(',')
            if status_list:
                mac_status = []
                for i in status_list:
                    if "=" in i:
                        mac_status.append(i)
                    else:
                        mac_status[-1] += "," + i
                context['dot3macstatus'] = "\n".join(mac_status)
        if neighbour.dot3_power_mdi:
            context['dot3powermdi'] = \
                neighbour.dot3_power_mdi.replace(',', '\n')
        context['neighbour'] = neighbour

        hostname = self.get_hostname(neighbour.host_uuid)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(neighbour.host_uuid,))),
            (_("Neighbors"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        return context

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = stx_api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname
