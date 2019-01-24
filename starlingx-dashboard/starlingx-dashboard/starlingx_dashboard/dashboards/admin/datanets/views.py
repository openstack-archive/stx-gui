#
# Copyright (c) 2016-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from starlingx_dashboard.dashboards.admin.datanets \
    import tabs as project_tabs


class IndexViewTabbed(tabs.TabbedTableView):
    tab_group_class = project_tabs.NetworkTabs
    template_name = 'admin/datanets/tabs.html'
    page_title = _("Data Networks")
