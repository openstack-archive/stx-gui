# Copyright (c) 2015-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import include  # noqa
from django.conf.urls import url  # noqa

from starlingx_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import urls as lvg_params_urls

urlpatterns = [
    url(r'lvg/',
        include(lvg_params_urls, namespace='lvg'))
]
