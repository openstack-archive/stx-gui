#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.utils.translation import ugettext_lazy as _

import horizon


class DCAdmin(horizon.Dashboard):
    name = _("Distributed Cloud Admin")
    slug = "dc_admin"
    default_panel = 'cloud_overview'

    # Must be admin and in the dcmanager's service region to manage
    # distributed cloud
    permissions = ('openstack.roles.admin',
                   'openstack.services.dcmanager',)

    def allowed(self, context):
        # Must be in SystemController region
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCAdmin, self).allowed(context)

horizon.register(DCAdmin)
