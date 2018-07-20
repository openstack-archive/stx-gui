#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.conf.urls import url
from openstack_dashboard.dashboards.admin.storage_overview import views

urlpatterns = [
    url(r'^$', views.StorageOverview.as_view(), name='index')
]
