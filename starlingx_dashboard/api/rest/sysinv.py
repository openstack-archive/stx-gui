#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2017 Wind River Systems, Inc.
#


from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from starlingx_dashboard.api import sysinv


@urls.register
class System(generic.View):
    """API for retrieving the system."""
    url_regex = r'sysinv/system/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get the system entity"""
        result = sysinv.system_get(request)
        return result.to_dict()
