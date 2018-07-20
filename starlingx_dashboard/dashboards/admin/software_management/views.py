#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon import views
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.software_management.forms import \
    CreatePatchStrategyForm
from openstack_dashboard.dashboards.admin.software_management.forms import \
    CreateUpgradeStrategyForm
from openstack_dashboard.dashboards.admin.software_management.forms import \
    UploadPatchForm
from openstack_dashboard.dashboards.admin.software_management import \
    tables as toplevel_tables
from openstack_dashboard.dashboards.admin.software_management.tabs \
    import SoftwareManagementTabs

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = SoftwareManagementTabs
    template_name = 'admin/software_management/index.html'
    page_title = _("Software Management")

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)


class DetailPatchView(views.HorizonTemplateView):
    template_name = 'admin/software_management/_detail_patches.html'
    page_title = 'Patch Detail'

    def get_context_data(self, **kwargs):
        context = super(DetailPatchView, self).get_context_data(**kwargs)
        context["patch"] = self.get_data()
        return context

    def get_data(self):
        if not hasattr(self, "_patch"):
            patch_id = self.kwargs['patch_id']
            try:
                patch = api.patch.get_patch(self.request, patch_id)
                patch.contents_display = "%s" % "\n".join(
                    filter(None, patch.contents))
                patch.requires_display = "%s" % "\n".join(
                    filter(None, patch.requires))
            except Exception:
                redirect = reverse('horizon:admin:software_management:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'patch "%s".') % patch_id,
                                  redirect=redirect)

            self._patch = patch
        return self._patch


class UploadPatchView(forms.ModalFormView):
    form_class = UploadPatchForm
    template_name = 'admin/software_management/upload_patch.html'
    context_object_name = 'patch'
    success_url = reverse_lazy("horizon:admin:software_management:index")


class CreatePatchStrategyView(forms.ModalFormView):
    form_class = CreatePatchStrategyForm
    template_name = 'admin/software_management/create_patch_strategy.html'
    context_object_name = 'strategy'
    success_url = reverse_lazy("horizon:admin:software_management:index")

    def get_context_data(self, **kwargs):
        context = super(CreatePatchStrategyView, self).get_context_data(
            **kwargs)
        alarms = api.sysinv.alarm_list(self.request)
        affecting = \
            len([alarm for alarm in alarms if alarm.mgmt_affecting == 'True'])

        context['alarms'] = len(alarms)
        context['affecting'] = affecting
        return context


class CreateUpgradeStrategyView(forms.ModalFormView):
    form_class = CreateUpgradeStrategyForm
    template_name = 'admin/software_management/create_upgrade_strategy.html'
    context_object_name = 'strategy'
    success_url = reverse_lazy("horizon:admin:software_management:index")

    def get_context_data(self, **kwargs):
        context = super(CreateUpgradeStrategyView, self).get_context_data(
            **kwargs)
        alarms = api.sysinv.alarm_list(self.request)
        affecting = \
            len([alarm for alarm in alarms if alarm.mgmt_affecting == 'True'])

        context['alarms'] = len(alarms)
        context['affecting'] = affecting
        return context


class DetailStageView(tables.DataTableView):
    template_name = 'admin/software_management/_detail_stage.html'
    page_title = 'Stage Detail'

    def get_context_data(self, **kwargs):
        context = super(DetailStageView, self).get_context_data(**kwargs)
        context["stage"] = self.get_stage()
        return context

    def get_stage(self):
        if not hasattr(self, "_stage"):
            phase = self.kwargs['phase']
            stage_id = self.kwargs['stage_id']
            try:
                stage = api.vim.get_stage(self.request, self.strategy_name,
                                          phase, stage_id)
                stage.timeout_display = \
                    datetime.timedelta(seconds=stage.timeout)
            except Exception:
                redirect = reverse('horizon:admin:software_management:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'stage "%s".') % stage_id,
                                  redirect=redirect)

            self._stage = stage
        return self._stage

    def get_data(self):
        try:
            stage = self.get_stage()
            steps = stage.steps
            for step in steps:
                step.phase_name = stage.phase.phase_name
                step.stage_id = stage.stage_id
        except Exception:
            steps = []
            msg = _('Steps list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return steps


class DetailPatchStageView(DetailStageView):
    table_class = toplevel_tables.PatchStepsTable
    strategy_name = api.vim.STRATEGY_SW_PATCH


class DetailUpgradeStageView(DetailStageView):
    table_class = toplevel_tables.UpgradeStepsTable
    strategy_name = api.vim.STRATEGY_SW_UPGRADE
