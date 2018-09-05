#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.cloud_overview import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
]
