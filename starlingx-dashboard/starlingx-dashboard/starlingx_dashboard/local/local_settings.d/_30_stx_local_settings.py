import os

from openstack_dashboard.local import configss
from openstack_dashboard.settings import HORIZON_CONFIG
from tsconfig.tsconfig import distributed_cloud_role


# WEBROOT is the location relative to Webserver root
# should end with a slash.
WEBROOT = '/'

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))
ALLOWED_HOSTS = ["*"]
HORIZON_CONFIG["password_autocomplete"] = "off"

# The OPENSTACK_HEAT_STACK settings can be used to disable password
# field required while launching the stack.
OPENSTACK_HEAT_STACK = {
    'enable_user_pass': False,
}

OPENSTACK_HOST = "controller"
OPENSTACK_KEYSTONE_URL = "http://%s:5000/v3" % OPENSTACK_HOST
OPENSTACK_API_VERSIONS = {"identity": 3}

OPENSTACK_NEUTRON_NETWORK['enable_distributed_router'] = True  # noqa


# Load Region Config params, if present
# Config OPENSTACK_HOST is still required in region mode since Titanium Cloud
# does not use the local_settings populated via packstack
try:
    if os.path.exists('/etc/openstack-dashboard/region-config.ini'):
        if not configss.CONFSS:
            configss.load('/etc/openstack-dashboard/region-config.ini')

            OPENSTACK_HOST = \
                configss.CONFSS['shared_services']['openstack_host']
            OPENSTACK_KEYSTONE_URL = "http://%s:5000/v3" % OPENSTACK_HOST
            AVAILABLE_REGIONS = [
                (OPENSTACK_KEYSTONE_URL,
                 configss.CONFSS['shared_services']['region_name'])]
            REGION_NAME = configss.CONFSS['shared_services']['region_name']
            SS_ENABLED = "True"
        else:
            SS_ENABLED = "Failed"
    else:
        SS_ENABLED = "False"
except Exception:
    SS_ENABLED = "Exception"

# Load Horizon region exclusion list
REGION_EXCLUSIONS = []
try:
    if os.path.exists('/opt/branding/horizon-region-exclusions.csv'):
        with open('/opt/branding/horizon-region-exclusions.csv') as f:
            for line in f:
                if line.startswith('#') or line.startswith(' '):
                    continue
                REGION_EXCLUSIONS = line.rstrip('\n').rstrip('\r').split(',')
except Exception:
    pass

# check if it is in distributed cloud
DC_MODE = False
if distributed_cloud_role and distributed_cloud_role in ['systemcontroller',
                                                         'subcloud']:
    DC_MODE = True

OPENSTACK_ENDPOINT_TYPE = "internalURL"


# Override Django tempory file upload directory
# Directory in which upload streamed files will be temporarily saved. A value
# of `None` will make Django use the operating system's default temporary
# directory
FILE_UPLOAD_TEMP_DIR = "/scratch/horizon"

# Override openstack-dashboard NG_CACHE_TEMPLATE_AGE
NG_TEMPLATE_CACHE_AGE = 300

# Conf file location on CentOS
POLICY_FILES_PATH = "/etc/openstack-dashboard"


# Settings for OperationLogMiddleware
OPERATION_LOG_ENABLED = True
OPERATION_LOG_OPTIONS = {
    'mask_fields': ['password', 'bm_password', 'bm_confirm_password',
                    'current_password', 'confirm_password', 'new_password',
                    'fake_password'],
    'target_methods': ['POST', 'PUT', 'DELETE'],
    'format': ("[%(project_name)s %(project_id)s] [%(user_name)s %(user_id)s]"
               " [%(method)s %(request_url)s %(http_status)s]"
               " parameters:[%(param)s] message:[%(message)s]"),
}


# Wind River CGCS Branding Settings
SITE_BRANDING = "StarlingX"

# Note (Eddie Ramirez): The theme name will be updated after r0
AVAILABLE_THEMES = [
    ('default', 'Default', 'themes/default'),
    ('material', 'Material', 'themes/material'),
    ('starlingx', 'StarlingX', 'themes/starlingx'),
]
DEFAULT_THEME = 'starlingx'

for root, _dirs, files in os.walk('/opt/branding/applied'):
    if 'manifest.py' in files:
        with open(os.path.join(root, 'manifest.py')) as f:
            code = compile(f.read(), os.path.join(root, 'manifest.py'), 'exec')
            exec(code)

        AVAILABLE_THEMES = [
            ('default', 'Default', 'themes/default'),
            ('material', 'Material', 'themes/material'),
            ('starlingx', 'StarlingX', 'themes/starlingx'),
            ('custom', 'Custom', '/opt/branding/applied'),
        ]
        DEFAULT_THEME = 'custom'

STATIC_ROOT = "/www/pages/static"
COMPRESS_OFFLINE = True

# Secure site configuration
SESSION_COOKIE_HTTPONLY = True

# Size of thread batch
THREAD_BATCH_SIZE = 100

try:
    if os.path.exists('/etc/openstack-dashboard/horizon-config.ini'):
        if not configss.CONFSS or 'horizon_params' not in configss.CONFSS:
            configss.load('/etc/openstack-dashboard/horizon-config.ini')

        if configss.CONFSS['horizon_params']['https_enabled'] == 'true':
            CSRF_COOKIE_SECURE = True
            SESSION_COOKIE_SECURE = True

        if configss.CONFSS['auth']['lockout_period']:
            LOCKOUT_PERIOD_SEC = float(
                configss.CONFSS['auth']['lockout_period'])
        if configss.CONFSS['auth']['lockout_retries']:
            LOCKOUT_RETRIES_NUM = int(
                configss.CONFSS['auth']['lockout_retries'])

        ENABLE_MURANO_TAB = False
        try:
            if configss.CONFSS['optional_tabs']['murano_enabled'] == 'True':
                ENABLE_MURANO_TAB = True
        except Exception:
            # disable murano tab if we cannot find the murano_enabled param
            pass

        ENABLE_MAGNUM_TAB = False
        try:
            if configss.CONFSS['optional_tabs']['magnum_enabled'] == 'True':
                ENABLE_MAGNUM_TAB = True
        except Exception:
            # disable magnum tab if we cannot find the magnum_enabled param
            pass

except Exception:
    pass


LOGGING = {
    'version': 1,
    # When set to True this will disable all logging except
    # for loggers specified in this configuration dictionary. Note that
    # if nothing is specified here and disable_existing_loggers is True,
    # django.db.backends will still log unless it is disabled explicitly.
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelno)s %(levelname)s %(message)s',
        },
        'standard': {
            'format': '%(levelno)s %(asctime)s [%(levelname)s] '
                      '%(name)s: %(message)s',
        },
        'verbose': {
            'format': '%(levelno)s %(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s',
        },
        'operation': {
            # The format of "%(message)s" is defined by
            # OPERATION_LOG_OPTIONS['format']
            'format': '%(asctime)s %(message)s',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            # Set the level to "DEBUG" for verbose output logging.
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'syslog': {
            # Set the level to "DEBUG" for verbose output logging.
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.SysLogHandler',
            'facility': 'local7',
            'address': '/dev/log',
        },
        'operation': {
            'level': 'INFO',
            'formatter': 'operation',
            'class': 'logging.handlers.SysLogHandler',
            'facility': 'local7',
            'address': '/dev/log',
        },
    },
    'loggers': {
        # Logging from django.db.backends is VERY verbose, send to null
        # by default.
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
        },
        'requests': {
            'handlers': ['null'],
            'propagate': False,
        },
        'horizon': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'horizon.operation_log': {
            'handlers': ['syslog'],
            'level': 'INFO',
            'propagate': False,
        },
        'openstack_dashboard': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'starlingx_dashboard': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cinderclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'glanceclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'neutronclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'heatclient': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'swiftclient': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openstack_auth': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'nose.plugins.manager': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['syslog'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'iso8601': {
            'handlers': ['null'],
            'propagate': False,
        },
        'scss': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# Session timeout overrides

# SESSION_TIMEOUT is a method to supersede the token timeout with a shorter
# horizon session timeout (in seconds).  So if your token expires in 60
# minutes, a value of 1800 will log users out after 30 minutes
SESSION_TIMEOUT = 3000

# TOKEN_TIMEOUT_MARGIN ensures the user is logged out before the token
# expires. This parameter specifies the number of seconds before the
# token expiry to log users out. If the token expires in 60 minutes, a
# value of 600 will log users out after 50 minutes.
TOKEN_TIMEOUT_MARGIN = 600

# The timezone of the server. This should correspond with the timezone
# of your entire OpenStack installation, and hopefully be in UTC.
# In this case, we set the value to None so that the interface uses the system
# timezone by default
TIME_ZONE = None
