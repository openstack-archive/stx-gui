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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tabs


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "admin/datanets/datanets/ranges/" \
                    "_detail_overview.html"

    def get_context_data(self, request):
        providernet_range = self.tab_group.kwargs['providernet_range']
        return {'providernet_range': providernet_range}


class ProviderNetworkRangeDetailTabs(tabs.TabGroup):
    slug = "providernet_range_details"
    tabs = (OverviewTab,)
