#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from cgtsclient.common import constants
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.software_management import \
    tables as toplevel_tables

LOG = logging.getLogger(__name__)


class PatchesTab(tabs.TableTab):
    table_classes = (toplevel_tables.PatchesTable,)
    name = _("Patches")
    slug = "patches"
    template_name = ("admin/software_management/_patches.html")

    def get_context_data(self, request):
        context = super(PatchesTab, self).get_context_data(request)

        phosts = []
        try:
            phosts = stx_api.patch.get_hosts(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve host list.'))

        context['patch_current'] = all(
            phost.patch_current is True for phost in phosts)

        return context

    def get_patches_data(self):
        request = self.request
        patches = []
        try:
            patches = stx_api.patch.get_patches(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve patch list.'))

        return patches


class PatchOrchestrationTab(tabs.TableTab):
    table_classes = (toplevel_tables.PatchStagesTable,)
    name = _("Patch Orchestration")
    slug = "patch_orchestration"
    template_name = ("admin/software_management/_patch_orchestration.html")

    def get_context_data(self, request):
        context = super(PatchOrchestrationTab, self).get_context_data(request)

        strategy = None
        try:
            strategy = stx_api.vim.get_strategy(request,
                                                stx_api.vim.STRATEGY_SW_PATCH)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(request,
                              _('Unable to retrieve current strategy.'))

        context['strategy'] = strategy
        return context

    def get_patchstages_data(self):
        request = self.request
        stages = []
        try:
            stages = stx_api.vim.get_stages(request,
                                            stx_api.vim.STRATEGY_SW_PATCH)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve stages list.'))

        return stages

    def allowed(self, request):
        if request.user.services_region == 'SystemController':
            return False
        return True


class UpgradeOrchestrationTab(tabs.TableTab):
    table_classes = (toplevel_tables.UpgradeStagesTable,)
    name = _("Upgrade Orchestration")
    slug = "upgrade_orchestration"
    template_name = ("admin/software_management/_upgrade_orchestration.html")

    def get_context_data(self, request):
        context = super(UpgradeOrchestrationTab, self).get_context_data(
            request)

        strategy = None
        try:
            strategy = stx_api.vim.get_strategy(
                request, stx_api.vim.STRATEGY_SW_UPGRADE)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(request,
                              _('Unable to retrieve current strategy.'))

        context['strategy'] = strategy
        return context

    def get_upgradestages_data(self):
        request = self.request
        stages = []
        try:
            stages = stx_api.vim.get_stages(request,
                                            stx_api.vim.STRATEGY_SW_UPGRADE)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve stages list.'))

        return stages

    def allowed(self, request):
        if request.user.services_region == 'SystemController':
            return False
        # Upgrade orchestration not available on CPE deployments
        systems = stx_api.sysinv.system_list(request)
        system_type = systems[0].to_dict().get('system_type')
        if system_type == constants.TS_AIO:
            return False
        return True


class SoftwareManagementTabs(tabs.TabGroup):
    slug = "software_management_tabs"
    tabs = (PatchesTab, PatchOrchestrationTab, UpgradeOrchestrationTab)
    sticky = True
