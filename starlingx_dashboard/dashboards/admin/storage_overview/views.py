#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _
from horizon import tabs

from starlingx_dashboard.dashboards.admin.storage_overview import (
    tabs as project_tabs
)
from starlingx_dashboard.dashboards.admin.storage_overview import constants


class StorageOverview(tabs.TabbedTableView):
    tab_group_class = project_tabs.StorageOverviewTabs
    template_name = constants.STORAGE_OVERVIEW_TEMPLATE_NAME
    page_title = _("Storage Overview")
