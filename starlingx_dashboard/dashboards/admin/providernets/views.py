#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard.dashboards.admin.providernets \
    import tabs as project_tabs


class IndexViewTabbed(tabs.TabbedTableView):
    tab_group_class = project_tabs.NetworkTabs
    template_name = 'admin/providernets/tabs.html'
    page_title = _("Provider Networks")
