#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


from django.conf.urls import url

from openstack_dashboard.dashboards.dc_admin.cloud_overview import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
]
