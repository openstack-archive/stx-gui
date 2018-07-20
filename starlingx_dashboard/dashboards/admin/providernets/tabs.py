#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import logging

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.api import base
from openstack_dashboard.api import neutron
from openstack_dashboard.dashboards.admin.providernets.providernets import \
    tables as providernets_tables

LOG = logging.getLogger(__name__)


class ProviderNetworkTab(tabs.TableTab):
    table_classes = (providernets_tables.ProviderNetworksTable,)
    name = _("Provider Networks")
    slug = "provider_networks"
    template_name = ("horizon/common/_detail_table.html")

    def get_provider_networks_data(self):
        try:
            providernets = \
                neutron.provider_network_list(self.tab_group.request)
        except Exception:
            providernets = []
            msg = _('Unable to get provider network list.')
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        return providernets

    def allowed(self, request):
        return base.is_TiS_region(request)


class NetworkTabs(tabs.TabGroup):
    slug = "providernets"
    tabs = (ProviderNetworkTab,)
    sticky = True
