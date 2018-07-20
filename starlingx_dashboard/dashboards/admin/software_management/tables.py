#
# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import logging

from django.core.urlresolvers import reverse  # noqa
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import messages
from horizon import tables
from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class UploadPatch(tables.LinkAction):
    name = "patchupload"
    verbose_name = _("Upload Patches")
    url = "horizon:admin:software_management:patchupload"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class ApplyPatch(tables.BatchAction):
    name = "apply"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Apply Patch",
            u"Apply Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Applied Patch",
            u"Applied Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True
        return patch.repostate == "Available"

    def handle(self, table, request, obj_ids):
        try:
            result = api.patch.patch_apply_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, ex.message)


class RemovePatch(tables.BatchAction):
    name = "remove"
    classes = ()

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Remove Patch",
            u"Remove Patchs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Removed Patch",
            u"Removed Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True

        if patch.unremovable == "Y":
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
        else:
            self.classes = [c for c in self.classes if c != "disabled"]

        return patch.repostate == "Applied"

    def handle(self, table, request, obj_ids):
        try:
            result = api.patch.patch_remove_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, ex.message)


class DeletePatch(tables.BatchAction):
    name = "delete"
    icon = 'trash'
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Patch",
            u"Delete Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Patch",
            u"Deleted Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True
        return patch.repostate == "Available"

    def handle(self, table, request, obj_ids):
        try:
            result = api.patch.patch_delete_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, ex.message)


class UpdatePatchRow(tables.Row):
    ajax = True

    def get_data(self, request, patch_id):
        patch = api.patch.get_patch(request, patch_id)
        return patch


class PatchFilterAction(tables.FilterAction):
    def filter(self, table, patches, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(patch):
            if q in patch.patch_id.lower():
                return True
            return False

        return filter(comp, patches)


class PatchesTable(tables.DataTable):
    PATCH_STATE_CHOICES = (
        (None, True),
        ("", True),
        ("none", True),
        ("Available", True),
        ("Partial-Apply", True),
        ("Partial-Remove", True),
        ("Applied", True),
        ("Committed", True)
    )

    patch_id = tables.Column('patch_id',
                             link="horizon:admin:software_management:"
                                  "patchdetail",
                             verbose_name=_('Patch ID'))
    reboot_required = tables.Column('reboot_required',
                                    verbose_name=_('RR'))
    sw_version = tables.Column('sw_version',
                               verbose_name=_('Release'))
    patchstate = tables.Column('patchstate',
                               verbose_name=_('Patch State'),
                               status=True,
                               status_choices=PATCH_STATE_CHOICES)
    summary = tables.Column('summary',
                            verbose_name=_('Summary'))

    def get_object_id(self, obj):
        return obj.patch_id

    def get_object_display(self, obj):
        return obj.patch_id

    class Meta(object):
        name = "patches"
        multi_select = True
        row_class = UpdatePatchRow
        status_columns = ['patchstate']
        row_actions = (ApplyPatch, RemovePatch, DeletePatch)
        table_actions = (
            PatchFilterAction, UploadPatch, ApplyPatch, RemovePatch,
            DeletePatch)
        verbose_name = _("Patches")
        hidden_title = False


# Patch Orchestration
def get_cached_strategy(request, strategy_name, table):
    if api.vim.STRATEGY_SW_PATCH == strategy_name:
        if 'patchstrategy' not in table.kwargs:
            table.kwargs['patchstrategy'] = api.vim.get_strategy(
                request, strategy_name)
        return table.kwargs['patchstrategy']
    elif api.vim.STRATEGY_SW_UPGRADE == strategy_name:
        if 'upgradestrategy' not in table.kwargs:
            table.kwargs['upgradestrategy'] = api.vim.get_strategy(
                request, strategy_name)
        return table.kwargs['upgradestrategy']


class CreateStrategy(tables.LinkAction):
    verbose_name = _("Create Strategy")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def allowed(self, request, datum):
        try:
            # Only a single strategy (patch or upgrade) can exist at a time.
            strategy = get_cached_strategy(request, api.vim.STRATEGY_SW_PATCH,
                                           self.table)
            if not strategy:
                strategy = get_cached_strategy(request,
                                               api.vim.STRATEGY_SW_UPGRADE,
                                               self.table)

            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes

            if strategy:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
        except Exception as ex:
            LOG.exception(ex)
        return True


class CreatePatchStrategy(CreateStrategy):
    name = "createpatchstrategy"
    url = "horizon:admin:software_management:createpatchstrategy"


class CreateUpgradeStrategy(CreateStrategy):
    name = "createupgradestrategy"
    url = "horizon:admin:software_management:createupgradestrategy"


class DeleteStrategy(tables.Action):
    force = False
    disabled = False
    requires_input = False
    icon = 'trash'
    action_type = 'danger'
    verbose_name = _("Delete Strategy")
    confirm_message = "You have selected Delete Strategy. " \
                      "Please confirm your selection"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            self.disabled = False
            if not strategy or strategy.state in ['aborting', 'applying']:
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(DeleteStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.vim.delete_strategy(request, self.strategy_name,
                                             self.force)
            if result:
                messages.success(request, "Strategy Deleted")
            else:
                messages.error(request, "Strategy delete failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, ex.message)


class DeletePatchStrategy(DeleteStrategy):
    name = "delete_patch_strategy"
    strategy_name = api.vim.STRATEGY_SW_PATCH


class DeleteUpgradeStrategy(DeleteStrategy):
    name = "delete_upgrade_strategy"
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class ApplyStrategy(tables.Action):
    requires_input = False
    disabled = False
    verbose_name = _("Apply Strategy")

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            self.disabled = False
            if not strategy or strategy.current_phase == 'abort' or \
                    strategy.state in ['build-failed', 'applying',
                                       'applied', 'aborting', 'aborted']:
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(ApplyStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.vim.apply_strategy(request, self.strategy_name)
            if result:
                messages.success(request, "Strategy apply in progress")
            else:
                messages.error(request, "Strategy apply failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, ex.message)


class ApplyPatchStrategy(ApplyStrategy):
    name = "apply_patch_strategy"
    strategy_name = api.vim.STRATEGY_SW_PATCH


class ApplyUpgradeStrategy(ApplyStrategy):
    name = "apply_upgrade_strategy"
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class AbortStrategy(tables.Action):
    requires_input = False
    disabled = False
    action_type = 'danger'
    verbose_name = _("Abort Strategy")
    confirm_message = "You have selected Abort Strategy. " \
                      "Please confirm your selection"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            self.disabled = False
            if not strategy or strategy.state != 'applying':
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(AbortStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.vim.abort_strategy(request, self.strategy_name)
            if result:
                messages.success(request, "Strategy abort in progress")
            else:
                messages.error(request, "Strategy abort failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, ex.message)


class AbortPatchStrategy(AbortStrategy):
    name = "abort_patch_strategy"
    strategy_name = api.vim.STRATEGY_SW_PATCH


class AbortUpgradeStrategy(AbortStrategy):
    name = "abort_upgrade_strategy"
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class ApplyStage(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Apply Stage",
            u"Apply Stages",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Applied Stage",
            u"Applied Stages",
            count
        )

    def allowed(self, request, stage=None):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            if stage.result != "initial" or stage.inprogress \
                    or not strategy or strategy.current_phase == 'abort' \
                    or strategy.state in ['aborted', 'aborting']:
                return False
            # Loop through the stages and ensure this is the first in 'line'
            stages = api.vim.get_stages(request, self.strategy_name)
            for s in stages:
                if s.phase.phase_name == stage.phase.phase_name and \
                        s.stage_id == stage.stage_id and \
                        stage.result == 'initial':
                    return True
                if s.result == 'initial' or s.inprogress:
                    return False
        except Exception as ex:
            LOG.exception(ex)
        return False

    def handle(self, table, request, obj_ids):
        for obj_id in obj_ids:
            try:
                stage_id = obj_id.split('-', 1)[1]
                result = api.vim.apply_strategy(request, self.strategy_name,
                                                stage_id)
                if result is None:
                    messages.error(request, "Strategy stage %s apply failed" %
                                   stage_id)
                else:
                    messages.success(request,
                                     "Strategy stage %s apply in progress" %
                                     stage_id)
            except Exception as ex:
                LOG.exception(ex)
                messages.error(request, ex.message)


class ApplyPatchStage(ApplyStage):
    name = "apply_patch_stage"
    strategy_name = api.vim.STRATEGY_SW_PATCH


class ApplyUpgradeStage(ApplyStage):
    name = "apply_upgrade_stage"
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class AbortStage(tables.BatchAction):
    name = "abort_stage"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Abort Stage",
            u"Abort Stages",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Aborted Stage",
            u"Aborted Stages",
            count
        )

    def allowed(self, request, stage=None):
        if not stage:
            return True
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            if not strategy or strategy.current_phase == 'abort' \
                    or strategy.state in ['aborted', 'aborting']:
                return False
        except Exception as ex:
            LOG.exception(ex)
        return stage.inprogress and stage.phase.phase_name == 'apply'

    def handle(self, table, request, obj_ids):
        for obj_id in obj_ids:
            try:
                stage_id = obj_id.split('-', 1)[1]
                result = api.vim.abort_strategy(request, self.strategy_name,
                                                stage_id)
                if result is None:
                    messages.error(request,
                                   "Strategy stage %s abort in progress" %
                                   stage_id)
                else:
                    messages.success(request, "Strategy stage %s aborted" %
                                     stage_id)
            except Exception as ex:
                LOG.exception(ex)
                messages.error(request, ex.message)


class AbortPatchStage(AbortStage):
    name = "abort_patch_stage"
    strategy_name = api.vim.STRATEGY_SW_PATCH


class AbortUpgradeStage(AbortStage):
    name = "abort_upgrade_stage"
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


def get_current_step_time(stage):
    if stage.current_step >= len(stage.steps):
        return "N/A"
    return get_time(stage.steps[stage.current_step])


def get_time(entity):
    try:
        return datetime.timedelta(seconds=entity.timeout)
    except Exception:
        return "N/A"


def get_current_step_name(stage):
    if stage.current_step >= len(stage.steps):
        return "N/A"
    return stage.steps[stage.current_step].step_name


def get_entities(stage):
    for step in stage.steps:
        if step.step_name == 'sw-patch-hosts':
            return ", ".join(step.entity_names)
        elif step.step_name == 'upgrade-hosts':
            return ", ".join(step.entity_names)
    return "N/A"


FAILURE_STATUSES = ('failed', 'aborted')
STAGE_STATE_CHOICES = (
    (None, True),
    ("", True),
    ("none", True),
    ("success", True),
    ("initial", True),
    ("failed", False),
    ("timed-out", False),
    ("aborted", False),
)


def get_result(stage):
    if stage.phase.phase_name == 'build' and stage.phase.result == 'failed':
        # Special case for build failures
        return stage.phase.result
    if stage.inprogress:
        return "In Progress (Step " + str(stage.current_step + 1) + "/" + \
               str(stage.total_steps) + ")"
    return stage.result


def get_reason(stage):
    if stage.phase.phase_name == 'build' and stage.phase.reason:
        # Special case for build failures
        return stage.phase.reason
    if stage.reason or \
            stage.current_step >= len(stage.steps):
        return stage.reason
    return stage.steps[stage.current_step].reason


def get_phase_name(stage):
    return title(stage.phase.phase_name)


class UpdateStageRow(tables.Row):
    ajax = True

    def get_data(self, request, row_id):
        phase = row_id.split('-', 1)[0]
        stage_id = row_id.split('-', 1)[1]
        stage = api.vim.get_stage(request, self.strategy_name, phase, stage_id)
        return stage


class UpdatePatchStageRow(UpdateStageRow):
    strategy_name = api.vim.STRATEGY_SW_PATCH


class UpdateUpgradeStageRow(UpdateStageRow):
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class StagesTable(tables.DataTable):

    phase = tables.Column(get_phase_name, verbose_name=_('Phase'))
    stage_name = tables.Column('stage_name')
    entities = tables.Column(get_entities, verbose_name=_('Hosts'))
    current_step = tables.Column(get_current_step_name,
                                 verbose_name=_('Current Step Name'))
    step_timeout = tables.Column(get_current_step_time,
                                 verbose_name=_('Current Step Timeout'),)
    status = tables.Column(get_result,
                           status=True,
                           status_choices=STAGE_STATE_CHOICES,
                           verbose_name=_('Status'))
    reason = tables.Column(get_reason,
                           verbose_name=_('Reason'))

    def get_object_id(self, obj):
        return "%s-%s" % (obj.phase.phase_name, obj.stage_id)

    def get_object_display(self, obj):
        return "Stage %s of %s Phase" % (obj.stage_id, obj.phase.phase_name)


def get_patchstage_link_url(stage):
    return reverse("horizon:admin:software_management:patchstagedetail",
                   args=(stage.stage_id, stage.phase.phase_name))


class PatchStagesTable(StagesTable):
    stage_name = tables.Column('stage_name',
                               link=get_patchstage_link_url,
                               verbose_name=_('Stage Name'))

    class Meta(object):
        name = "patchstages"
        multi_select = False
        status_columns = ['status', ]
        row_class = UpdatePatchStageRow
        row_actions = (ApplyPatchStage, AbortPatchStage)
        table_actions = (CreatePatchStrategy, ApplyPatchStrategy,
                         AbortPatchStrategy, DeletePatchStrategy)
        verbose_name = _("Stages")
        hidden_title = False


def get_upgradestage_link_url(stage):
    return reverse("horizon:admin:software_management:upgradestagedetail",
                   args=(stage.stage_id, stage.phase.phase_name))


class UpgradeStagesTable(StagesTable):
    stage_name = tables.Column('stage_name',
                               link=get_upgradestage_link_url,
                               verbose_name=_('Stage Name'))

    class Meta(object):
        name = "upgradestages"
        multi_select = False
        status_columns = ['status', ]
        row_class = UpdateUpgradeStageRow
        row_actions = (ApplyUpgradeStage, AbortUpgradeStage)
        table_actions = (CreateUpgradeStrategy, ApplyUpgradeStrategy,
                         AbortUpgradeStrategy, DeleteUpgradeStrategy)
        verbose_name = _("Stages")
        hidden_title = False


def display_entities(step):
    return ", ".join(step.entity_names)


class UpdateStepRow(tables.Row):
    ajax = True

    def get_data(self, request, row_id):
        phase_name = row_id.split('-', 2)[0]
        stage_id = row_id.split('-', 2)[1]
        step_id = row_id.split('-', 2)[2]
        step = api.vim.get_step(
            request, self.strategy_name, phase_name, stage_id, step_id)
        step.phase_name = phase_name
        step.stage_id = stage_id
        return step


class UpdatePatchStepRow(UpdateStepRow):
    strategy_name = api.vim.STRATEGY_SW_PATCH


class UpdateUpgradeStepRow(UpdateStepRow):
    strategy_name = api.vim.STRATEGY_SW_UPGRADE


class StepsTable(tables.DataTable):
    step_id = tables.Column('step_id', verbose_name=_('Step ID'))
    step_name = tables.Column('step_name', verbose_name=_('Step Name'))
    entities = tables.Column(display_entities, verbose_name=_('Entities'))
    start = tables.Column('start_date_time', verbose_name=_('Start Time'),)
    end = tables.Column('end_date_time', verbose_name=_('End Time'),)
    timeout = tables.Column(get_time, verbose_name=_('Timeout'),)
    result = tables.Column('result',
                           status=True,
                           status_choices=STAGE_STATE_CHOICES,
                           verbose_name=_('Status'))
    reason = tables.Column('reason', verbose_name=_('Reason'))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj.phase_name, obj.stage_id, obj.step_id)


class PatchStepsTable(StepsTable):
    class Meta(object):
        name = "steps"
        status_columns = ['result', ]
        row_class = UpdatePatchStepRow
        verbose_name = _("Steps")
        hidden_title = False


class UpgradeStepsTable(StepsTable):
    class Meta(object):
        name = "steps"
        status_columns = ['result', ]
        row_class = UpdateUpgradeStepRow
        verbose_name = _("Steps")
        hidden_title = False
