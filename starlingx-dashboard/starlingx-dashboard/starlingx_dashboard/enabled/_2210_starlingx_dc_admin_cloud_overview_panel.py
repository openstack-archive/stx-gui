# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'dc_admin'

# The slug of the panel group the PANEL is associated with.
# If you want the panel to show up without a panel group,
# use the panel group "default".
PANEL_GROUP = 'default'

# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'cloud_overview'

# If set to True, this settings file will not be added to the settings.
DISABLED = False

# Python panel class of the PANEL to be added.
ADD_PANEL = 'starlingx_dashboard.dashboards.' \
            'dc_admin.cloud_overview.panel.CloudOverview'
