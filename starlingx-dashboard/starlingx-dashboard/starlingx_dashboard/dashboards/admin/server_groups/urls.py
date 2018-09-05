# Copyright 2012 Nebula, Inc.
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
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.admin.server_groups import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<server_group_id>[^/]+)/attach/$',
        views.EditAttachmentsView.as_view(),
        name='attach'),
    url(r'^(?P<server_group_id>[^/]+)/$',
        views.DetailView.as_view(),
        name='detail')
]
