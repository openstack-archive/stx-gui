# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
# Copyright (c) 2013-2015 Wind River Systems, Inc.
#


from django.conf.urls import include  # noqa
from django.conf.urls import url  # noqa

from openstack_dashboard.dashboards.admin.providernets.providernets.ranges \
    import urls as range_urls
from openstack_dashboard.dashboards.admin.providernets.providernets.ranges \
    import views as range_views
from openstack_dashboard.dashboards.admin.providernets.providernets import \
    views

PROVIDERNETS = r'^(?P<providernet_id>[^/]+)/%s$'
VIEW_MOD = 'openstack_dashboard.dashboards.admin.providernets.providernets.' \
           'views'

urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(),
        name='create'),
    url(PROVIDERNETS % 'addrange',
        views.CreateRangeView.as_view(), name='addrange'),
    url(PROVIDERNETS % 'update', views.UpdateView.as_view(),
        name='update'),
    url(PROVIDERNETS % 'detail', views.DetailView.as_view(),
        name='detail')]
urlpatterns += [
    url(PROVIDERNETS % 'ranges/create',
        range_views.CreateView.as_view(),
        name='createrange'),
    url(
        r'^(?P<providernet_id>[^/]+)/ranges/'
        r'(?P<providernet_range_id>[^/]+)/update$',
        range_views.UpdateView.as_view(), name='editrange'),
    url(r'^ranges/',
        include(range_urls, namespace='ranges'))]
