# Copyright (c) 2015-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url  # noqa

from starlingx_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import views

urlpatterns = [
    url(r'^(?P<key>[^/]+)/edit/$', views.EditView.as_view(),
        name='edit')]
