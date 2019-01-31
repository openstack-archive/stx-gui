#
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import include
from django.conf.urls import url

from starlingx_dashboard.dashboards.admin.datanets.datanets \
    import urls as datanet_urls
from starlingx_dashboard.dashboards.admin.datanets import views


NETWORKS = r'^(?P<network_id>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', views.IndexViewTabbed.as_view(), name='index'),
    url(r'^datanets/',
        include(datanet_urls, namespace='datanets'))
]
