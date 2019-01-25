# Copyright 2012 NEC Corporation
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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


from django.conf.urls import url  # noqa

from starlingx_dashboard.dashboards.admin.datanets.datanets.ranges \
    import views

RANGES = r'^(?P<providernet_range_id>[^/]+)/%s$'

urlpatterns = [
    url(RANGES % 'detail', views.DetailView.as_view(),
        name='detail')]
