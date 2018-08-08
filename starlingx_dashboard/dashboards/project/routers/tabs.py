from horizon import tabs

from starlingx_dashboard.api import base as stx_base
from starlingx_dashboard.dashboards.project.routers.portforwardings\
    import tables


class PortForwardingTab(tabs.TableTab):
    table_classes = (tables.PortForwardingRulesTable,)
    name = _("Port Forwarding")
    slug = "portforwardings"
    template_name = "horizon/common/_detail_table.html"

    def get_portforwardings_data(self):
        return self.tab_group.kwargs['portforwardings']

    def allowed(self, request):
        return stx_base.base.is_TiS_region(request)