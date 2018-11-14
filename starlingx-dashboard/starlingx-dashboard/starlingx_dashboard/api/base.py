#
# Copyright (c) 2018 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0
#
from django.conf import settings

from openstack_dashboard.api import base


def get_request_page_size(request, limit=None):
    default_limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    try:
        return min(int(limit), default_limit)
    except Exception:
        default_page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        return request.session.get('horizon_pagesize', default_page_size)


def is_stx_region(request):
    if not base.is_service_enabled(request, 'platform'):
        return False
    return True
