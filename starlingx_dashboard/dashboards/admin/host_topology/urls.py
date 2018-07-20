#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.conf.urls import url

from openstack_dashboard.dashboards.admin.host_topology import views


urlpatterns = [
    url(r'^$', views.HostTopologyView.as_view(), name='index'),
    url(r'^json$', views.JSONView.as_view(), name='json'),

    url(r'^(?P<host_id>[^/]+)/host/$',
        views.HostDetailView.as_view(), name='host'),
    url(r'^(?P<providernet_id>[^/]+)/providernet/$',
        views.ProvidernetDetailView.as_view(), name='providernet')
]
