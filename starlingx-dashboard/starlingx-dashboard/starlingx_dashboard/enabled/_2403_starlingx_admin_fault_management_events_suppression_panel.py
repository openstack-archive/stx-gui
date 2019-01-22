# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'events_suppression'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'fault_management'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'

# Python panel class of the PANEL to be added.
#ADD_PANEL = 'starlingx_dashboard.content.events_suppression.panel.EventsSuppression'
ADD_PANEL = 'starlingx_dashboard.dashboards.admin.events_suppression.panel.EventsSuppression'