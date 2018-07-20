#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from openstack_dashboard.dashboards.admin.system_config.address_pools import \
    views as address_pool_views
from openstack_dashboard.dashboards.admin.system_config.views import \
    CreateSDNControllerView
from openstack_dashboard.dashboards.admin.system_config.views import \
    DetailSDNControllerView
from openstack_dashboard.dashboards.admin.system_config.views \
    import IndexView
from openstack_dashboard.dashboards.admin.system_config.views \
    import UpdatecDNSView
from openstack_dashboard.dashboards.admin.system_config.views \
    import UpdatecEXT_OAMView
from openstack_dashboard.dashboards.admin.system_config.views \
    import UpdatecNTPView
from openstack_dashboard.dashboards.admin.system_config.views import \
    UpdateiStoragePoolsView
from openstack_dashboard.dashboards.admin.system_config.views import \
    UpdateiStorageView
from openstack_dashboard.dashboards.admin.system_config.views import \
    UpdatePipelineView
from openstack_dashboard.dashboards.admin.system_config.views import \
    UpdateSDNControllerView
from openstack_dashboard.dashboards.admin.system_config.views import \
    UpdateSystemView

UUID = r'^(?P<uuid>[^/]+)/%s$'
PIPELINE = r'^(?P<pipeline_name>[^/]+)/%s$'
TIER = r'^(?P<tier_name>[^/]+)/%s$'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^(?P<system_id>[^/]+)/update_system/$',
        UpdateSystemView.as_view(), name='update_system'),

    url(r'^addaddrpool/$',
        address_pool_views.CreateAddressPoolView.as_view(),
        name='addaddrpool'),
    url(r'^(?P<address_pool_uuid>[^/]+)/updateaddrpool/$',
        address_pool_views.UpdateAddressPoolView.as_view(),
        name='updateaddrpool'),

    url(r'^update_cdns_table/$', UpdatecDNSView.as_view(),
        name='update_cdns_table'),
    url(r'^update_cntp_table/$', UpdatecNTPView.as_view(),
        name='update_cntp_table'),
    url(r'^update_coam_table/$', UpdatecEXT_OAMView.as_view(),
        name='update_coam_table'),

    url(r'^update_istorage_table/$', UpdateiStorageView.as_view(),
        name='update_storage_table'),

    url(TIER % 'update_istorage_pools_table',
        UpdateiStoragePoolsView.as_view(),
        name='update_storage_pools_table'),
    url(UUID % 'update_sdn_controller_table',
        UpdateSDNControllerView.as_view(),
        name='update_sdn_controller_table'),
    url(UUID % 'detail_sdn_controller_table',
        DetailSDNControllerView.as_view(),
        name='detail_sdn_controller_table'),
    url(r'^create_sdn_controller_table/$',
        CreateSDNControllerView.as_view(),
        name='create_sdn_controller_table'),

    url(PIPELINE % 'update', UpdatePipelineView.as_view(),
        name='update')
]
