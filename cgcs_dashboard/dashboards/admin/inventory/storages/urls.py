# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2015 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

from django.conf.urls import include  # noqa
from django.conf.urls import url  # noqa

from openstack_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import urls as lvg_params_urls

urlpatterns = [
    url(r'lvg/',
        include(lvg_params_urls, namespace='lvg'))
]
