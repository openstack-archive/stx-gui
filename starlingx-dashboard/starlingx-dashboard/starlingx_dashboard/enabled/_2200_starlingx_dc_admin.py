# The slug of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'dc_admin'
# If set to True, this dashboard will be set as the default dashboard.
DEFAULT = False
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {}
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['starlingx_dashboard.dashboards.dc_admin', ]
ADD_ANGULAR_MODULES = [
    'horizon.dashboard.dc_admin',
]

AUTO_DISCOVER_STATIC_FILES = True
