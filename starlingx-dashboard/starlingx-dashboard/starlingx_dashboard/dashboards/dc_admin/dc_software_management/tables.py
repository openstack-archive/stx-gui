#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.template.defaultfilters import safe, title  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from starlingx_dashboard import api
from starlingx_dashboard.dashboards.admin.software_management import tables \
    as AdminTables

LOG = logging.getLogger(__name__)


# Patching
class UploadPatch(AdminTables.UploadPatch):
    url = "horizon:dc_admin:dc_software_management:dc_patchupload"


class PatchesTable(AdminTables.PatchesTable):
    patch_id = tables.Column('patch_id',
                             link="horizon:dc_admin:dc_software_management:"
                                  "dc_patchdetail",
                             verbose_name=_('Patch ID'))

    class Meta(object):
        name = "dc_patches"
        multi_select = True
        row_class = AdminTables.UpdatePatchRow
        status_columns = ['patchstate']
        row_actions = (AdminTables.ApplyPatch, AdminTables.RemovePatch,
                       AdminTables.DeletePatch)
        table_actions = (
            AdminTables.PatchFilterAction, UploadPatch, AdminTables.ApplyPatch,
            AdminTables.RemovePatch, AdminTables.DeletePatch)
        verbose_name = _("Patches")
        hidden_title = False


# Cloud Patch Orchestration
def get_cached_cloud_strategy(request, table):
    if 'cloudpatchstrategy' not in table.kwargs:
        table.kwargs['cloudpatchstrategy'] = \
            api.dc_manager.get_strategy(request)
    return table.kwargs['cloudpatchstrategy']


class CreateCloudPatchStrategy(tables.LinkAction):
    name = "createcloudpatchstrategy"
    url = "horizon:dc_admin:dc_software_management:createcloudpatchstrategy"
    verbose_name = _("Create Strategy")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)

            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
            if strategy:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
        except Exception as ex:
            LOG.exception(ex)
        return True


class DeleteCloudPatchStrategy(tables.Action):
    name = "delete_patch_strategy"
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
            strategy = get_cached_cloud_strategy(request, self.table)
            self.disabled = True
            if strategy and strategy.state in ['initial', 'complete', 'failed',
                                               'aborted']:
                self.disabled = False
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(DeleteCloudPatchStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.dc_manager.strategy_delete(request)
            if result:
                messages.success(request, "Strategy Deleted")
            else:
                messages.error(request, "Strategy delete failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))


class ApplyCloudPatchStrategy(tables.Action):
    name = "apply_cloud_patch_strategy"
    requires_input = False
    disabled = False
    verbose_name = _("Apply Strategy")

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)
            self.disabled = False
            if not strategy or strategy.state != 'initial':
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(ApplyCloudPatchStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.dc_manager.strategy_apply(request)
            if result:
                messages.success(request, "Strategy apply in progress")
            else:
                messages.error(request, "Strategy apply failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))


class AbortCloudPatchStrategy(tables.Action):
    name = "abort_cloud_patch_strategy"
    requires_input = False
    disabled = False
    action_type = 'danger'
    verbose_name = _("Abort Strategy")
    confirm_message = "You have selected Abort Strategy. " \
                      "Please confirm your selection"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)
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
            return super(AbortCloudPatchStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.dc_manager.strategy_abort(request)
            if result:
                messages.success(request, "Strategy abort in progress")
            else:
                messages.error(request, "Strategy abort failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))


STEP_STATE_CHOICES = (
    (None, True),
    ("", True),
    ("none", True),
    ("complete", True),
    ("initial", True),
    ("failed", False),
    ("timed-out", False),
    ("aborted", False),
)


def get_apply_percent(cell):
    if '(' in cell and '%)' in cell:
        percent = cell.split('(')[1].split('%)')[0]
        return {'percent': "%d%%" % float(percent)}
    return {}


def get_state(step):
    state = step.state
    if '%' in step.details:
        percent = [s for s in step.details.split(' ') if '%' in s]
        if percent and len(percent):
            percent = percent[0]
            state += " (%s)" % percent
    return state


class CloudPatchStepsTable(tables.DataTable):
    cloud = tables.Column('cloud', verbose_name=_('Cloud'))
    stage = tables.Column('stage', verbose_name=_('Stage'))
    state = tables.Column(get_state,
                          verbose_name=_('State'),
                          status=True,
                          status_choices=STEP_STATE_CHOICES,
                          filters=(safe,),
                          cell_attributes_getter=get_apply_percent)
    details = tables.Column('details',
                            verbose_name=_("Details"),)
    started_at = tables.Column('started_at',
                               verbose_name=_('Started At'))
    finished_at = tables.Column('finished_at',
                                verbose_name=_('Finished At'))

    def get_object_id(self, obj):
        return "%s" % obj.cloud

    class Meta(object):
        name = "cloudpatchsteps"
        multi_select = False
        status_columns = ['state', ]
        table_actions = (CreateCloudPatchStrategy, ApplyCloudPatchStrategy,
                         AbortCloudPatchStrategy, DeleteCloudPatchStrategy)
        verbose_name = _("Steps")
        hidden_title = False


# Cloud Patch Config
class CreateCloudPatchConfig(tables.LinkAction):
    name = "createcloudpatchconfig"
    url = "horizon:dc_admin:dc_software_management:createcloudpatchconfig"
    verbose_name = _("Create New Cloud Patching Configuration")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class EditCloudPatchConfig(tables.LinkAction):
    name = "editcloudpatchconfig"
    url = "horizon:dc_admin:dc_software_management:editcloudpatchconfig"
    verbose_name = _("Edit Configuration")
    classes = ("ajax-modal",)


class DeleteCloudPatchConfig(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Cloud Patching Configuration",
            "Delete Cloud Patching Configurations",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Cloud Patching Configuration",
            "Deleted Cloud Patching Configurations",
            count
        )

    def allowed(self, request, config=None):
        if config and config.cloud == api.dc_manager.DEFAULT_CONFIG_NAME:
            return False
        return True

    def delete(self, request, config):
        try:
            api.dc_manager.config_delete(request, config)
        except Exception:
            msg = _('Failed to delete configuration for subcloud %(cloud)') % \
                {'cloud': config, }
            redirect = reverse('horizon:dc_admin:dc_software_management:index')
            exceptions.handle(request, msg, redirect=redirect)


class CloudPatchConfigTable(tables.DataTable):
    cloud = tables.Column('cloud', verbose_name=_('Cloud'))
    storage_apply_type = tables.Column('storage_apply_type',
                                       verbose_name=_('Storage Apply Type'))
    compute_apply_type = tables.Column('compute_apply_type',
                                       verbose_name=_('Compute Apply Type'))
    max_parallel_computes = tables.Column(
        'max_parallel_computes', verbose_name=_('Max Parallel Computes'))
    default_instance_action = tables.Column(
        'default_instance_action', verbose_name=_('Default Instance Action'))
    alarm_restriction_type = tables.Column(
        'alarm_restriction_type', verbose_name=_('Alarm Restrictions'))

    def get_object_id(self, obj):
        return "%s" % obj.cloud

    def get_object_display(self, obj):
        return obj.cloud

    class Meta(object):
        name = "cloudpatchconfig"
        multi_select = False
        table_actions = (CreateCloudPatchConfig,)
        row_actions = (EditCloudPatchConfig, DeleteCloudPatchConfig,)
        verbose_name = _("Cloud Patching Configurations")
        hidden_title = False
