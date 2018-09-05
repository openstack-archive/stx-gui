#
# Copyright (c) 2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.api import base
from openstack_dashboard.dashboards.admin import dashboard


class Providernets(horizon.Panel):
    name = _("Provider Networks")
    slug = 'providernets'
    permissions = ('openstack.services.platform', 'openstack.services.network')

    def allowed(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return super(Providernets, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return True


dashboard.Admin.register(Providernets)
