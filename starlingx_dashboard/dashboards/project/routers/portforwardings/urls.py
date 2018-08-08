# Copyright (c) 2013-2015 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.routers.portforwardings \
    import views

PORTFORWARDINGS = r'^(?P<portforwarding_id>[^/]+)/%s$'

urlpatterns = patterns(
    'horizon.dashboards.project.networks.portforwardings.views',
    url(PORTFORWARDINGS % 'detail', views.DetailView.as_view(), name='detail'))
