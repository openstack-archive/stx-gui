#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#


from django.utils.translation import ugettext_lazy as _

import horizon


class CloudOverview(horizon.Panel):
    name = _("Cloud Overview")
    slug = 'cloud_overview'
