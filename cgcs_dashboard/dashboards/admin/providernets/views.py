#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard.dashboards.admin.providernets \
    import tabs as project_tabs


class IndexViewTabbed(tabs.TabbedTableView):
    tab_group_class = project_tabs.NetworkTabs
    template_name = 'admin/providernets/tabs.html'
    page_title = _("Provider Networks")
