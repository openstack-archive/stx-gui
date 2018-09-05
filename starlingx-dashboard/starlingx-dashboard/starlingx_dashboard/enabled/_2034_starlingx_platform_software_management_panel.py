# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'software_management'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'platform'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'starlingx_dashboard.dashboards.admin.software_management.' \
            'panel.SoftwareManagement'
