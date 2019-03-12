# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['starlingx_dashboard']

FEATURE = ['starlingx_dashboard']

ADD_HEADER_SECTIONS = \
    ['starlingx_dashboard.dashboards.admin.active_alarms.views.BannerView', ]

ADD_SCSS_FILES = ['dashboard/scss/styles.scss',
                  'dashboard/scss/_host_topology.scss']

AUTO_DISCOVER_STATIC_FILES = True
