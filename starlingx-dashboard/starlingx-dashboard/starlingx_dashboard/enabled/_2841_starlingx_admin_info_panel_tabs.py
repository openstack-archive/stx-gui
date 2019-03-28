# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'info'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'admin'

ADD_INSTALLED_APPS = \
    ['starlingx_dashboard.dashboards.admin.controller_services', ]

EXTRA_TABS = {
    'openstack_dashboard.dashboards.admin.info.tabs.SystemInfoTabs': (
        'starlingx_dashboard.dashboards.admin.controller_services.tabs.'
        'ControllerServicesTab',
    ),
}
