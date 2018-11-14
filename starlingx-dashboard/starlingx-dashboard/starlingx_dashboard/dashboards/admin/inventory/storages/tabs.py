# Copyright (c) 2015-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import tables as params_table

LOG = logging.getLogger(__name__)


class LocalVolumeGroupOverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "lvg_overview"
    template_name = ("admin/inventory/"
                     "_detail_local_volume_group_overview.html")

    def get_context_data(self, request):
        lvg_id = self.tab_group.kwargs['lvg_id']
        try:
            lvg = stx_api.sysinv.host_lvg_get(request, lvg_id)
        except Exception:
            redirect = reverse('horizon:admin:storages:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve flavor details.'),
                              redirect=redirect)
        return {'lvg': lvg}


class LocalVolumeGroupParametersTab(tabs.TableTab):
    table_classes = (params_table.ParamsTable,)
    name = _("Parameters")
    slug = "lvg_params"
    template_name = ("horizon/common/_detail_table.html")

    def get_params_data(self):
        request = self.tab_group.request
        lvg_id = self.tab_group.kwargs['lvg_id']
        try:
            params = stx_api.sysinv.host_lvg_get_params(request, lvg_id)
            params.sort(key=lambda es: (es.key,))
        except Exception:
            params = []
            exceptions.handle(self.request,
                              _('Unable to retrieve parameter list.'))
        return params


class LocalVolumeGroupDetailTabs(tabs.TabGroup):
    slug = "lvg_details"
    tabs = (LocalVolumeGroupOverviewTab, LocalVolumeGroupParametersTab)
    sticky = True
