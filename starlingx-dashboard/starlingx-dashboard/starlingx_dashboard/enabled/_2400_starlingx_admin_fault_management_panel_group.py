from django.utils.translation import ugettext_lazy as _

# The slug of the panel group to be added to HORIZON_CONFIG. Required.
PANEL_GROUP = 'fault_management'
# The display name of the PANEL_GROUP. Required.
PANEL_GROUP_NAME = _('Fault Management')
# The slug of the dashboard the PANEL_GROUP associated with. Required.
PANEL_GROUP_DASHBOARD = 'admin'

ADD_ANGULAR_MODULES = [
    'horizon.dashboard.fault_management'
]

ADD_SCSS_FILES = [
    'dashboard/fault_management/fault_management.scss'
]

AUTO_DISCOVER_STATIC_FILES = True
