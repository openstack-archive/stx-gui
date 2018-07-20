#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'dc_admin/cloud_overview/index.html'
