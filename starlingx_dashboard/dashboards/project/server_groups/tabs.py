# Copyright 2012 Nebula, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import nova


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/server_groups/"
                     "_detail_overview.html")

    def get_context_data(self, request):
        server_group_id = self.tab_group.kwargs['server_group_id']
        try:
            server_group = nova.server_group_get(request, server_group_id)
            server_group.members_display = []
            for member in server_group.members:
                server_group.members_display.append(
                    dict(id=member, instance=nova.server_get(request, member)))
        except Exception:
            redirect = reverse('horizon:project:server_groups:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve server group details.'),
                              redirect=redirect)
        return {'server_group': server_group}


class ServerGroupDetailTabs(tabs.TabGroup):
    slug = "server_group_details"
    tabs = (OverviewTab,)
