#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import include
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.providernets.providernets \
    import urls as providernet_urls
from openstack_dashboard.dashboards.admin.providernets import views


NETWORKS = r'^(?P<network_id>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', views.IndexViewTabbed.as_view(), name='index'),
    url(r'^providernets/',
        include(providernet_urls, namespace='providernets'))
]
