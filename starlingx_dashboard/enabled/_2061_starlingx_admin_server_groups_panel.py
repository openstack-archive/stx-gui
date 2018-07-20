# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'server_groups'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'compute'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'starlingx_dashboard.dashboards.admin.server_groups.panel.ServerGroups'
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['starlingx_dashboard', ]