#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.api import base
from openstack_dashboard.dashboards.admin import dashboard


class Inventory(horizon.Panel):
    name = _("Host Inventory")
    slug = 'inventory'
    # permissions = ('openstack.roles.admin',)
    permissions = ('openstack.services.platform',)

    def allowed(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return super(Inventory, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return True


dashboard.Admin.register(Inventory)
