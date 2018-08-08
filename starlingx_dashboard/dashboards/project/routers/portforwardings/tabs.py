# Copyright (c) 2013-2015 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/networks/portforwardings/_detail_overview.html"
    failure_url = 'horizon:project:routers:index'

    def get_context_data(self, request):
        portforwarding_id = self.tab_group.kwargs['portforwarding_id']
        try:
            rule = api.neutron.portforwarding_get(self.request,
                                                  portforwarding_id)
        except Exception:
            redirect = reverse(self.failure_url)
            msg = _('Unable to retrieve port forwarding details.')
            exceptions.handle(request, msg, redirect=redirect)
        return {'portforwarding': rule}


class PortForwardingDetailTabs(tabs.TabGroup):
    slug = "portforwarding_details"
    tabs = (OverviewTab,)
