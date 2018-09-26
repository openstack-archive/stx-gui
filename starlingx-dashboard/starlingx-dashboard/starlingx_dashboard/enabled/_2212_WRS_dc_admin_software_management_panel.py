# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'dc_software_management'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'dc_admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'default'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'starlingx_dashboard.dashboards.' \
            'dc_admin.dc_software_management.panel.DCSoftwareManagement'
