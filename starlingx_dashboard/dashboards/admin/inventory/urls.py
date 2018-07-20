#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls import include  # noqa
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.inventory.cpu_functions import \
    views as cpu_functions_views
from openstack_dashboard.dashboards.admin.inventory.devices import \
    views as device_views
from openstack_dashboard.dashboards.admin.inventory.interfaces.address import \
    views as address_views
from openstack_dashboard.dashboards.admin.inventory.interfaces.route import \
    views as route_views
from openstack_dashboard.dashboards.admin.inventory.interfaces import \
    views as interface_views
from openstack_dashboard.dashboards.admin.inventory.lldp import \
    views as lldp_views
from openstack_dashboard.dashboards.admin.inventory.memorys import \
    views as memory_views
from openstack_dashboard.dashboards.admin.inventory.ports import \
    views as port_views
from openstack_dashboard.dashboards.admin.inventory.sensors import \
    views as sensor_views
from openstack_dashboard.dashboards.admin.inventory.storages import \
    views as storage_views
from openstack_dashboard.dashboards.admin.inventory.views import \
    AddView
from openstack_dashboard.dashboards.admin.inventory.views import \
    DetailView
from openstack_dashboard.dashboards.admin.inventory.views import \
    IndexView
from openstack_dashboard.dashboards.admin.inventory.views import \
    UpdateView

from openstack_dashboard.dashboards.admin.inventory.storages \
    import urls as storages_urls


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<host_id>[^/]+)/detail/$',
        DetailView.as_view(), name='detail'),
    url(r'^create/$', AddView.as_view(), name='create'),
    url(r'^(?P<host_id>[^/]+)/update/$',
        UpdateView.as_view(), name='update'),
    url(r'^(?P<host_id>[^/]+)/editcpufunctions/$',
        cpu_functions_views.UpdateCpuFunctionsView.as_view(),
        name='editcpufunctions'),
    url(r'^(?P<host_id>[^/]+)/addcpuprofile/$',
        cpu_functions_views.AddCpuProfileView.as_view(),
        name='addcpuprofile'),
    url(r'^(?P<host_id>[^/]+)/addinterface/$',
        interface_views.AddInterfaceView.as_view(),
        name='addinterface'),
    url(r'^(?P<host_id>[^/]+)/addinterfaceprofile/$',
        interface_views.AddInterfaceProfileView.as_view(),
        name='addinterfaceprofile'),
    url(
        r'^(?P<host_id>[^/]+)/interfaces/(?P<interface_id>[^/]+)/update/$',
        interface_views.UpdateView.as_view(),
        name='editinterface'),
    url(
        r'^(?P<host_id>[^/]+)/interfaces/(?P<interface_id>[^/]+)/detail/$',
        interface_views.DetailView.as_view(),
        name='viewinterface'),
    url(
        r'^(?P<host_id>[^/]+)/interfaces/(?P<interface_id>[^/]+)/addaddress/$',
        address_views.CreateView.as_view(),
        name='addaddress'),
    url(
        r'^(?P<host_id>[^/]+)/interfaces/(?P<interface_id>[^/]+)/addroute/$',
        route_views.CreateView.as_view(),
        name='addroute'),
    url(
        r'^(?P<host_id>[^/]+)/ports/(?P<port_id>[^/]+)/update/$',
        port_views.UpdateView.as_view(), name='editport'),
    url(
        r'^(?P<host_id>[^/]+)/ports/(?P<port_id>[^/]+)/detail/$',
        port_views.DetailView.as_view(),
        name='viewport'),
    url(r'^(?P<host_id>[^/]+)/addstoragevolume/$',
        storage_views.AddStorageVolumeView.as_view(),
        name='addstoragevolume'),
    url(r'^(?P<host_id>[^/]+)/adddiskprofile/$',
        storage_views.AddDiskProfileView.as_view(),
        name='adddiskprofile'),
    url(r'^(?P<host_id>[^/]+)/updatememory/$',
        memory_views.UpdateMemoryView.as_view(),
        name='updatememory'),
    url(r'^(?P<host_id>[^/]+)/addmemoryprofile/$',
        memory_views.AddMemoryProfileView.as_view(),
        name='addmemoryprofile'),

    url(r'^(?P<host_id>[^/]+)/addlocalvolumegroup/$',
        storage_views.AddLocalVolumeGroupView.as_view(),
        name='addlocalvolumegroup'),
    url(r'^(?P<host_id>[^/]+)/addphysicalvolume/$',
        storage_views.AddPhysicalVolumeView.as_view(),
        name='addphysicalvolume'),
    url(r'^(?P<pv_id>[^/]+)/physicalvolumedetail/$',
        storage_views.DetailPhysicalVolumeView.as_view(),
        name='physicalvolumedetail'),
    url(r'^(?P<lvg_id>[^/]+)/localvolumegroupdetail/$',
        storage_views.DetailLocalVolumeGroupView.as_view(),
        name='localvolumegroupdetail'),
    url(r'^(?P<lvg_id>[^/]+)/storages/',
        include(storages_urls, namespace='storages')),

    url(r'^(?P<host_id>[^/]+)/addsensorgroup/$',
        sensor_views.AddSensorGroupView.as_view(),
        name='addsensorgroup'),
    url(r'^(?P<host_id>[^/]+)/sensorgroups/(?P<sensorgroup_id>[^/]+)/'
        'updatesensorgroup/$',
        sensor_views.UpdateSensorGroupView.as_view(),
        name='editsensorgroup'),
    url(r'^(?P<sensor_id>[^/]+)/sensordetail/$',
        sensor_views.DetailSensorView.as_view(),
        name='sensordetail'),
    url(r'^(?P<sensorgroup_id>[^/]+)/sensorgroupdetail/$',
        sensor_views.DetailSensorGroupView.as_view(),
        name='sensorgroupdetail'),

    url(
        r'^(?P<host_id>[^/]+)/devices/(?P<device_uuid>[^/]+)/update/$',
        device_views.UpdateView.as_view(),
        name='editdevice'),
    url(
        r'^(?P<host_id>[^/]+)/devices/(?P<device_uuid>[^/]+)/detail/$',
        device_views.DetailView.as_view(),
        name='viewdevice'),
    url(
        r'^(?P<device_id>[^/]+)/devices/usage/$',
        device_views.UsageView.as_view(),
        name='viewusage'),
    url(
        r'^(?P<neighbour_uuid>[^/]+)/viewneighbour/$',
        lldp_views.DetailNeighbourView.as_view(), name='viewneighbour'),
    url(r'^(?P<host_id>[^/]+)/storages/(?P<stor_uuid>[^/]+)/'
        'editstoragevolume/$',
        storage_views.EditStorageVolumeView.as_view(),
        name='editstoragevolume'),
    url(r'^(?P<host_id>[^/]+)/createpartition/$',
        storage_views.CreatePartitionView.as_view(),
        name='createpartition'),
    url(r'^(?P<host_id>[^/]+)/storages/(?P<partition_uuid>[^/]+)/'
        'editpartition/$',
        storage_views.EditPartitionView.as_view(),
        name='editpartition')
]
