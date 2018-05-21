#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


from django.conf.urls import url
from openstack_dashboard.dashboards.admin.storage_overview import views

urlpatterns = [
    url(r'^$', views.StorageOverview.as_view(), name='index')
]
