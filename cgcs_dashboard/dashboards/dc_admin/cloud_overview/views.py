#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'dc_admin/cloud_overview/index.html'
