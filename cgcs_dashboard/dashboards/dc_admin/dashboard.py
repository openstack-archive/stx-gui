#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
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
        # Must be in SystemController region or in RegionOne (and in DC mode)
        if context['request'].user.services_region != 'SystemController':
            # TODO(tsmith) enhance criteria?
            return False

        return super(DCAdmin, self).allowed(context)

horizon.register(DCAdmin)
