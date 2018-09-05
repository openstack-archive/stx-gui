#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.utils.translation import ugettext_lazy as _

import horizon


class CloudOverview(horizon.Panel):
    name = _("Cloud Overview")
    slug = 'cloud_overview'
