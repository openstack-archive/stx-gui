#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.utils.translation import ugettext_lazy as _

import horizon
from starlingx_dashboard.dashboards.dc_admin import dashboard


class DCSoftwareManagement(horizon.Panel):
    name = _("Software Management")
    slug = 'dc_software_management'

    def allowed(self, context):
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCSoftwareManagement, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCSoftwareManagement, self).allowed(context)


dashboard.DCAdmin.register(DCSoftwareManagement)
