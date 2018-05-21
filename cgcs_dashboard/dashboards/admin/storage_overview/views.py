#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


from django.utils.translation import ugettext_lazy as _
from horizon import tabs

from openstack_dashboard.dashboards.admin.storage_overview import (
    tabs as project_tabs
)
from openstack_dashboard.dashboards.admin.storage_overview import constants


class StorageOverview(tabs.TabbedTableView):
    tab_group_class = project_tabs.StorageOverviewTabs
    template_name = constants.STORAGE_OVERVIEW_TEMPLATE_NAME
    page_title = _("Storage Overview")
