#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import CreateCloudPatchConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import CreateCloudPatchStrategyView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import DetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import EditCloudPatchConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import IndexView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import UploadPatchView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<patch_id>[^/]+)/patchdetail/$',
        DetailPatchView.as_view(), name='dc_patchdetail'),
    url(r'^dc_patchupload/$', UploadPatchView.as_view(),
        name='dc_patchupload'),
    url(r'^createcloudpatchstrategy/$', CreateCloudPatchStrategyView.as_view(),
        name='createcloudpatchstrategy'),
    url(r'^createcloudpatchconfig/$', CreateCloudPatchConfigView.as_view(),
        name='createcloudpatchconfig'),
    url(r'^(?P<subcloud>[^/]+)/editcloudpatchconfig/$',
        EditCloudPatchConfigView.as_view(),
        name='editcloudpatchconfig'),
]
