#
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs

from starlingx_dashboard.api import base as stx_base
from starlingx_dashboard.api import sysinv as stx_sysinv
from starlingx_dashboard.dashboards.admin.datanets.datanets import \
    tables as datanets_tables


class DataNetworkTab(tabs.TableTab):
    table_classes = (datanets_tables.DataNetworksTable,)
    name = _("Data Networks")
    slug = "data_networks"
    template_name = ("horizon/common/_detail_table.html")

    def get_data_networks_data(self):
        try:
            datanets = \
                stx_sysinv.data_network_list(self.tab_group.request)
        except Exception:
            datanets = []
            msg = _('Unable to get provider network list.')
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        return datanets

    def allowed(self, request):
        return stx_base.is_stx_region(request)


class NetworkTabs(tabs.TabGroup):
    slug = "datanets"
    tabs = (DataNetworkTab,)
    sticky = True
