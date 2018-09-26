#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.api import base
from openstack_dashboard.dashboards.admin import dashboard


class SoftwareManagement(horizon.Panel):
    name = _("Software Management")
    slug = 'software_management'
    permissions = ('openstack.services.platform',)

    def allowed(self, context):
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        elif context['request'].user.services_region == 'SystemController':
            return False
        else:
            return super(SoftwareManagement, self).allowed(context)

    def nav(self, context):
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        elif context['request'].user.services_region == 'SystemController':
            return False
        else:
            return True


dashboard.Admin.register(SoftwareManagement)
