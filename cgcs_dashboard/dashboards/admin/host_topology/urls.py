#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
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
