#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from starlingx_dashboard import api
from starlingx_dashboard.dashboards.dc_admin.dc_software_management \
    import tables as tables

LOG = logging.getLogger(__name__)


class PatchesTab(tabs.TableTab):
    table_classes = (tables.PatchesTable,)
    name = _("Patches")
    slug = "patches"
    template_name = ("dc_admin/dc_software_management/_patches.html")

    def get_dc_patches_data(self):
        request = self.request
        patches = []
        try:
            patches = api.patch.get_patches(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve patch list.'))

        return patches


class CloudPatchOrchestrationTab(tabs.TableTab):
    table_classes = (tables.CloudPatchStepsTable,)
    name = _("Cloud Patching Orchestration")
    slug = "cloud_patch_orchestration"
    template_name = ("dc_admin/dc_software_management/"
                     "_cloud_patch_orchestration.html")

    def get_context_data(self, request):
        context = super(CloudPatchOrchestrationTab, self).\
            get_context_data(request)

        strategy = None
        try:
            strategy = api.dc_manager.get_strategy(request)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(request,
                              _('Unable to retrieve current strategy.'))
        context['strategy'] = strategy
        return context

    def get_cloudpatchsteps_data(self):
        request = self.request
        steps = []
        try:
            steps = api.dc_manager.step_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve steps list.'))

        return steps


class CloudPatchConfigTab(tabs.TableTab):
    table_classes = (tables.CloudPatchConfigTable,)
    name = _("Cloud Patching Configuration")
    slug = "cloud_patch_config"
    template_name = ("dc_admin/dc_software_management/"
                     "_cloud_patch_config.html")

    def get_cloudpatchconfig_data(self):
        request = self.request
        steps = []
        try:
            steps = api.dc_manager.config_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve configuration list.'))

        return steps


class DCSoftwareManagementTabs(tabs.TabGroup):
    slug = "dc_software_management_tabs"
    tabs = (PatchesTab, CloudPatchOrchestrationTab, CloudPatchConfigTab)
    sticky = True
