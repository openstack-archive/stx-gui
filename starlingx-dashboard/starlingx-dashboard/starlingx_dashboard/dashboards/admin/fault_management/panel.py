# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#

from django.utils.translation import ugettext_lazy as _  # noqa

import horizon
from openstack_dashboard.api import base
from openstack_dashboard.dashboards.admin import dashboard


class FaultManagement(horizon.Panel):
    name = _("Fault Management")
    slug = 'fault_management'
    permissions = ('openstack.services.platform',)

    def allowed(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return super(FaultManagement, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        if not base.is_service_enabled(context['request'], 'platform'):
            return False
        else:
            return True


dashboard.Admin.register(FaultManagement)
