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
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#

from __future__ import absolute_import

import logging

from django.conf import settings
import sm_client as smc
from openstack_dashboard.api import base

# Swap out with SM API
LOG = logging.getLogger(__name__)
SM_API_SERVICENAME = "smapi"


def sm_client(request):
    # o = urlparse.urlparse(url_for(request, 'inventory'))
    # url = "://".join((o.scheme, o.netloc))
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)

    sm_api_path = base.url_for(request, SM_API_SERVICENAME)
    return smc.Client('1', sm_api_path,
                       token=request.user.token.id,
                       insecure=insecure)


def sm_sda_list(request):
    sdas = sm_client(request).sm_sda.list()
    LOG.debug("SM sdas list %s", sdas)

    # fields = ['uuid', 'service_group_name', 'node_name', 'state', 'status',
    #           'condition']
    return sdas


def sm_nodes_list(request):
    nodes = sm_client(request).sm_nodes.list()
    LOG.debug("SM nodes list %s", nodes)

    # fields = ['id', 'name', 'state', 'online']
    return nodes
