#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django import template
from django.template.defaultfilters import safe, timesince  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import functions
from openstack_dashboard import api
from openstack_dashboard.api.sysinv import Host
from openstack_dashboard.dashboards.admin.inventory.cpu_functions \
    import utils as cpufunctions_utils

import cgcs_patch.constants as patch_constants

LOG = logging.getLogger(__name__)


def host_locked(host=None):
    if not host:
        return False
    return host._administrative == 'locked'


def host_board_management(host=None):
    if not host:
        return False
    return True if host.bm_type else False


def host_controller(host=None):
    if not host:
        return False
    return host._personality == api.sysinv.PERSONALITY_CONTROLLER


def host_powered_off(host=None):
    if not host:
        return False
    return host._availability == 'power-off'


def host_offline(host=None):
    if not host:
        return False
    return host._availability == 'offline'


def handle_sysinv(self, table, request, obj_ids):
    action_success = []
    action_failure = []
    action_not_allowed = []
    emessage = ""
    for datum_id in obj_ids:
        datum = table.get_object_by_id(datum_id)
        datum_display = table.get_object_display(datum) or _("N/A")
        if not table._filter_action(self, request, datum):
            action_not_allowed.append(datum_display)
            LOG.info('Permission denied to %s: "%s"',
                     self._get_action_name(past=True).lower(), datum_display)
            continue
        try:
            self.action(request, datum_id)
            # Call update to invoke changes if needed
            self.update(request, datum)
            action_success.append(datum_display)
            self.success_ids.append(datum_id)
            LOG.info('%s: "%s"',
                     self._get_action_name(past=True), datum_display)
        except Exception as ex:
            # Handle the exception but silence it since we'll display
            # an aggregate error message later. Otherwise we'd get
            # multiple error messages displayed to the user.
            if not getattr(ex, "_safe_message", None):
                action_failure.append(datum_display)
                emessage = ex

    # Begin with success message class, downgrade to info if problems.
    success_message_level = messages.success
    if action_not_allowed:
        msg = _('Unable to %(action)s in current state: %(objs)s')
        params = {"action": self._get_action_name(action_not_allowed).lower(),
                  "objs": functions.lazy_join(", ", action_not_allowed)}
        messages.error(request, msg % params)
        success_message_level = messages.info
    if action_failure:
        msg = _('Unable to %(action)s: %(objs)s. Reason/Action: %(emessage)s')
        params = {"action": self._get_action_name(action_failure).lower(),
                  "objs": functions.lazy_join(", ", action_failure),
                  "emessage": emessage}
        messages.error(request, msg % params)
        success_message_level = messages.info
    if action_success:
        msg = _('%(action)s: %(objs)s')
        params = {"action": self._get_action_name(action_success, True),
                  "objs": functions.lazy_join(", ", action_success)}
        success_message_level(request, msg % params)

    return shortcuts.redirect(self.get_success_url(request))


class AddHost(tables.LinkAction):
    name = "create"
    verbose_name = _("Add Host")
    url = "horizon:admin:inventory:create"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"
    ajax = True

    def allowed(self, request, host=None):
        return not api.sysinv.is_system_mode_simplex(request)


class EditHost(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Host")
    url = "horizon:admin:inventory:update"
    classes = ("ajax-modal", "btn-edit")


class DeleteHost(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Host",
            u"Delete Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Host",
            u"Deleted Hosts",
            count
        )

    def allowed(self, request, host=None):
        return host_locked(host)

    def delete(self, request, host_id):
        api.sysinv.host_delete(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class LockHost(tables.BatchAction):
    name = "lock"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Lock Host",
            u"Lock Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Locking Host",
            u"Locking Hosts",
            count
        )

    def allowed(self, request, host=None):
        if host is None:
            return True
        return not host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_lock(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class ForceLockHost(tables.BatchAction):
    name = "forcelock"
    action_type = 'danger'
    confirm_class = 'btn-danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Force Lock Host",
            u"Force Lock Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Forced Lock Host",
            u"Forced Lock Hosts",
            count
        )

    def allowed(self, request, host=None):
        return not host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_force_lock(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)

    def get_confirm_message(self, request, datum):
        if datum._personality == api.sysinv.PERSONALITY_CONTROLLER:
            return _(
                "<b>WARNING</b>: This will cause an uncontrolled switch"
                " of services on host '%s'.\n\n"
                "To avoid service outages, click 'Cancel' and use "
                "'Lock Host' to "
                "gracefully migrate resources away from this host. "
                "ONLY use 'Force Lock Host' if 'Lock Host' is "
                "unsuccessful and this host MUST be locked.\n\n"
                "If you proceed, then this action will be logged"
                " and cannot be undone.") % datum.hostname
        elif datum._personality == api.sysinv.PERSONALITY_COMPUTE:
            return _(
                "<b>WARNING</b>: This will cause a service OUTAGE"
                " for all VMs currently using resources on '%s'.\n\n"
                "To avoid service outages, click 'Cancel' and use"
                " 'Lock Host' to gracefully migrate "
                "resources away from this host. "
                "ONLY use 'Force Lock Host' if 'Lock Host' is"
                " unsuccessful and this host MUST be locked.\n\n"
                "If you proceed, then this action will be logged"
                " and cannot be undone.") % datum.hostname
        elif datum._personality == api.sysinv.PERSONALITY_STORAGE:
            return _(
                "<b>WARNING</b>: This will cause an uncontrolled"
                " loss of storage services on host '%s'.\n\n"
                "To avoid service outages, click 'Cancel' and use"
                " 'Lock Host' to "
                "gracefully migrate resources away from this host. "
                "ONLY use 'Force Lock Host' if 'Lock Host' is "
                "unsuccessful and this host MUST be locked.\n\n"
                "If you proceed, then this action will be logged"
                " and cannot be undone.") % datum.hostname
        else:
            return None


class UnlockHost(tables.BatchAction):
    name = "unlock"
    redirect_url = "horizon:admin:inventory:index"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Unlock Host",
            u"Unlock Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Unlocked Host",
            u"Unlocked Hosts",
            count
        )

    def allowed(self, request, host=None):
        if host is None:
            return True
        return host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_unlock(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class ForceUnlockHost(tables.BatchAction):
    name = "forceunlock"
    action_type = 'danger'
    confirm_class = 'btn-danger'
    redirect_url = "horizon:admin:inventory:index"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Force Unlock Host",
            u"Force Unlock Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Forced Unlock Host",
            u"Forced Unlock Hosts",
            count
        )

    def allowed(self, request, host=None):
        return host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_force_unlock(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)

    def get_confirm_message(self, request, datum):
        return _("<b>WARNING</b>: This will render '%s' in a bad state "
                 "which may require a reinstall or wipedisk.\n\n"
                 "To avoid it, click 'Cancel' and use 'Unlock Host'. "
                 "ONLY use 'Force Unlock Host' if 'Unlock Host' is "
                 "unsuccessful and this host MUST be unlocked.\n\n"
                 "If you proceed, then this action will be logged "
                 "and cannot be undone.") % datum.hostname


class PowerOnHost(tables.BatchAction):
    name = "poweron"
    classes = ('btn-power-on',)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Power On Host",
            u"Power On Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Powered On Host",
            u"Powered On Hosts",
            count
        )

    def allowed(self, request, host=None):
        return (host_board_management(host) and host_locked(host) and
                not api.sysinv.is_system_mode_simplex(request))

    def action(self, request, host_id):
        api.sysinv.host_power_on(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class PowerOffHost(tables.BatchAction):
    name = "poweroff"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Power Off Host",
            u"Power Off Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Powered Off Host",
            u"Powered Off Hosts",
            count
        )

    def allowed(self, request, host=None):
        return (host_board_management(host) and host_locked(host) and
                not host_powered_off(host) and
                not api.sysinv.is_system_mode_simplex(request))

    def action(self, request, host_id):
        api.sysinv.host_power_off(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class ResetHost(tables.BatchAction):
    name = "reset"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Reset Host",
            u"Reset Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Reset Host",
            u"Reset Hosts",
            count
        )

    def allowed(self, request, host=None):
        return (host_board_management(host) and host_locked(host) and
                not api.sysinv.is_system_mode_simplex(request))

    def action(self, request, host_id):
        api.sysinv.host_reset(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class RebootHost(tables.BatchAction):
    name = "reboot"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Reboot Host",
            u"Reboot Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Rebooted Host",
            u"Rebooted Hosts",
            count
        )

    def allowed(self, request, host=None):
        return host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_reboot(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class ReinstallHost(tables.BatchAction):
    name = "reinstall"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Reinstall Host",
            u"Reinstall Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Reinstalled Host",
            u"Reinstalled Hosts",
            count
        )

    def allowed(self, request, host=None):
        return host_locked(host)

    def action(self, request, host_id):
        api.sysinv.host_reinstall(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class SwactHost(tables.BatchAction):
    name = "swact"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Swact Host",
            u"Swact Hosts",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Swact Initiated Host",
            u"Swact Initiated Hosts",
            count
        )

    def allowed(self, request, host=None):
        return (host_controller(host) and not host_locked(host) and
                not api.sysinv.is_system_mode_simplex(request))

    def action(self, request, host_id):
        api.sysinv.host_swact(request, host_id)

    def handle(self, table, request, obj_ids):
        return handle_sysinv(self, table, request, obj_ids)


class PatchInstallAsync(tables.BatchAction):
    name = "install-async"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Install Patch",
            u"Install Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Installed Patch",
            u"Installed Patches",
            count
        )

    def allowed(self, request, host=None):
        if host is None:
            return True
        return (host.patch_current is not True and
                (host_locked(host) or host.allow_insvc_patching))

    def handle(self, table, request, obj_ids):

        for host_id in obj_ids:
            try:
                ihost = api.sysinv.host_get(request, host_id)
            except Exception:
                exceptions.handle(request,
                                  _('Unable to retrieve host.'))

            try:
                LOG.info("Installing patch for host %s ...", ihost.hostname)
                api.patch.host_install_async(request, ihost.hostname)
            except Exception as ex:
                messages.error(request, ex)
                return

        LOG.info("End of host-install-async")


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, host_id):
        host = api.sysinv.host_get(request, host_id)

        phost = api.patch.get_host(request, host.hostname)
        if phost is not None:
            if phost.interim_state is True:
                host.patch_current = "Pending"
            elif phost.patch_failed is True:
                host.patch_current = "Failed"
            else:
                host.patch_current = phost.patch_current
            host.requires_reboot = phost.requires_reboot
            host._patch_state = phost.state
            host.allow_insvc_patching = phost.allow_insvc_patching

        return host


class HostsStorageFilterAction(tables.FilterAction):
    def filter(self, table, hosts, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(host):
            if q in host.hostname.lower():
                return True
            return False

        return filter(comp, hosts)


class HostsComputeFilterAction(tables.FilterAction):
    def filter(self, table, hosts, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(host):
            if q in host.hostname.lower():
                return True
            return False

        return filter(comp, hosts)


def get_install_percent(cell):
    if '(' in cell and '%)' in cell:
        percent = cell.split('(')[1].split('%)')[0]
        adj_percent = 5 + 0.85 * float(percent)
        return {'percent': "%d%%" % adj_percent}
    elif 'Pre-install' in cell:
        return {'percent': '5%'}
    elif 'Post-install' in cell:
        return {'percent': '90%'}
    return {}


def get_task_or_status(host):
    task_or_status = ""
    patch_current = ""
    reboot_required = ""
    patch_state = ""

    # '+' maybe appended to the install_state_info to mark audit iterations
    if host.install_state and host.install_state != "Installed" and \
            host.install_state != "Completed":
        if host.availability != "Offline":
            # If the node is not offline then booting or failed install_state
            # does not apply
            if host.install_state == "Booting" or \
                    host.install_state == "Install Failed":
                task_or_status = ""
        else:
            task_or_status = str(host.install_state)
            if host.install_state_info and '/' in \
                    host.install_state_info.rstrip('+'):
                values = (host.install_state_info.rstrip('+')).split('/')
                percent = (float(values[0]) / float(values[1])) * 100
                task_or_status += " (%d%%)" % percent
    elif host.task:
        if '-' in host.task:
            task_or_status = host.task.strip('-')
        else:
            task_or_status = host.task
    elif host.config_status:
        task_or_status = host.config_status
    elif host.vim_progress_status:
        if host.vim_progress_status != 'services-enabled' and \
           host.vim_progress_status != 'services-disabled':
            task_or_status = host.vim_progress_status

    if host.requires_reboot is True:
        reboot_required = "Reboot Required"
    if host.patch_current == "Failed":
        patch_current = "Patch Install Failed"
    elif host.patch_current == "Pending":
        patch_current = "Checking Patch State..."
        # Clear the reboot_required for the Pending state
        reboot_required = ""
    elif host.patch_current is False:
        patch_current = "Not Patch Current"

    if host._patch_state != patch_constants.PATCH_AGENT_STATE_IDLE:
        patch_state = unicode(host.patch_state)
        if host._patch_state == patch_constants.PATCH_AGENT_STATE_INSTALLING:
            # Clear the other patch status fields
            patch_current = ""
            reboot_required = ""

    # Unset duplicate
    if patch_current == patch_state:
        patch_state = ""

    return _("%s") % "<br />".join(
        filter(None, [task_or_status,
                      patch_current,
                      reboot_required,
                      patch_state]))


TASK_STATE_CHOICES = (
    (None, True),
    ("", True),
    ("none", True),
    ("Install Failed", False),
    ("Config out-of-date", False),
    ("Compute config required", False),
    ("Reinstall required", False),
    ("Config out-of-date<br />Not Patch Current<br />Reboot Required",
     False),
    ("Config out-of-date<br />Not Patch Current", False),
    ("Config out-of-date<br />Patch Install Failed<br />Reboot Required",
     False),
    ("Config out-of-date<br />Patch Install Failed", False),
    ("Config out-of-date<br />Reboot Required", False),
    ("Not Patch Current<br />Reboot Required", True),
    ("Not Patch Current", True),
    ("Patch Install Failed<br />Reboot Required", True),
    ("Patch Install Failed", True),
    ("Reboot Required", True),
    ("Patch Install Rejected", True),
    ("Config out-of-date<br />Patch Install Rejected", True),
    ("Not Patch Current<br />Patch Install Rejected", True),
    ("Not Patch Current<br />Reboot Required" +
     "<br />Patch Install Rejected", True),
    ("Config out-of-date<br />Not Patch Current" +
     "<br />Reboot Required<br />Patch Install Rejected", True),)


class Hosts(tables.DataTable):
    hostname = tables.Column('hostname',
                             link="horizon:admin:inventory:detail",
                             verbose_name=_('Host Name'))
    personality = tables.Column(
        "personality",
        verbose_name=_("Personality"),
        display_choices=Host.PERSONALITY_DISPLAY_CHOICES)
    admin = tables.Column("administrative",
                          verbose_name=_("Admin State"),
                          display_choices=Host.ADMIN_DISPLAY_CHOICES)
    oper = tables.Column("operational",
                         verbose_name=_("Operational State"),
                         display_choices=Host.OPER_DISPLAY_CHOICES)
    avail = tables.Column("availability",
                          verbose_name=_("Availability State"),
                          display_choices=Host.AVAIL_DISPLAY_CHOICES)
    uptime = tables.Column('boottime',
                           verbose_name=_('Uptime'),
                           filters=(timesince,),
                           attrs={'data-type': "uptime"})

    task = tables.Column(get_task_or_status,
                         cell_attributes_getter=get_install_percent,
                         verbose_name=_("Status"),
                         filters=(safe,),
                         status=True,
                         status_choices=TASK_STATE_CHOICES)

    def get_object_id(self, datum):
        return unicode(datum.id)

    def get_object_display(self, datum):
        return datum.hostname


class HostsController(Hosts):
    class Meta(object):
        name = "hostscontroller"
        verbose_name = _("Controller Hosts")
        status_columns = ["task"]
        row_class = UpdateRow
        multi_select = True
        row_actions = (
            EditHost, LockHost, ForceLockHost, UnlockHost, ForceUnlockHost,
            SwactHost,
            PowerOnHost,
            PowerOffHost, RebootHost,
            ResetHost, ReinstallHost, PatchInstallAsync, DeleteHost)
        table_actions = (AddHost,)
        hidden_title = False


class HostsStorage(Hosts):
    peers = tables.Column('peers',
                          verbose_name=_('Replication Group'))

    class Meta(object):
        name = "hostsstorage"
        verbose_name = _("Storage Hosts")
        status_columns = ["task"]
        row_class = UpdateRow
        multi_select = True
        columns = ('hostname', 'peers', 'admin', 'oper', 'avail',
                   'uptime', 'task')
        row_actions = (
            EditHost, LockHost, ForceLockHost, UnlockHost, ForceUnlockHost,
            SwactHost,
            PowerOnHost,
            PowerOffHost, RebootHost,
            ResetHost, ReinstallHost, PatchInstallAsync, DeleteHost)
        table_actions = (HostsStorageFilterAction, LockHost,
                         UnlockHost, PatchInstallAsync)
        hidden_title = False


class HostsCompute(Hosts):
    class Meta(object):
        name = "hostscompute"
        verbose_name = _("Compute Hosts")
        status_columns = ["task"]
        row_class = UpdateRow
        multi_select = True
        row_actions = (
            EditHost, LockHost, ForceLockHost, UnlockHost, ForceUnlockHost,
            SwactHost,
            PowerOnHost,
            PowerOffHost, RebootHost,
            ResetHost, ReinstallHost, PatchInstallAsync, DeleteHost)
        table_actions = (HostsComputeFilterAction, LockHost,
                         UnlockHost, PatchInstallAsync)
        hidden_title = False


class HostsUnProvisioned(Hosts):
    class Meta(object):
        name = "hostsunprovisioned"
        verbose_name = _("UnProvisioned Hosts")
        status_columns = ["task"]
        row_class = UpdateRow
        multi_select = True
        row_actions = (
            EditHost, LockHost, ForceLockHost, UnlockHost, SwactHost,
            PowerOnHost,
            PowerOffHost, RebootHost,
            ResetHost, ReinstallHost, DeleteHost)
        hidden_title = False


class DeleteInterfaceProfile(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Interface Profile",
            u"Delete Interface Profiles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Interface Profile",
            u"Deleted Interface Profiles",
            count
        )

    def delete(self, request, interfaceprofile_id):
        try:
            api.sysinv.host_interfaceprofile_delete(request,
                                                    interfaceprofile_id)
        except Exception:
            msg = _(
                'Failed to delete interface profile %s') % interfaceprofile_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(request, msg, redirect=redirect)


def get_interfaces(ifProfile):
    template_name = 'admin/inventory/_interfaceprofiles_interfaceconfig.html'
    context = {"ifProfile": ifProfile}
    return template.loader.render_to_string(template_name, context)


def get_ports(ifProfile):
    template_name = 'admin/inventory/_interfaceprofiles_portconfig.html'
    context = {"ifProfile": ifProfile}
    return template.loader.render_to_string(template_name, context)


class InterfaceProfilesTable(tables.DataTable):
    interfaceProfileName = tables.Column('profilename',
                                         verbose_name=_('Name'))

    ports = tables.Column(get_ports,
                          verbose_name=_("Port Configuration"))

    interfaces = tables.Column(get_interfaces,
                               verbose_name=_("Interface Configuration"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.profilename

    class Meta(object):
        name = "interfaceprofiles"
        verbose_name = _("Interface Profiles")
        multi_select = True
        table_actions = (DeleteInterfaceProfile, )


# Cpu Profile Table
class DeleteCpuProfile(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Cpu Profile",
            u"Delete Cpu Profiles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Cpu Profile",
            u"Deleted Cpu Profiles",
            count
        )

    def delete(self, request, cpuprofile_id):
        try:
            api.sysinv.host_cpuprofile_delete(request, cpuprofile_id)
        except Exception:
            msg = _('Failed to delete cpu profile %s') % cpuprofile_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(request, msg, redirect=redirect)


def get_cpuassignments(cpuProfile):
    template_name = 'admin/inventory/_cpuprofiles_cpuassignments.html'
    context = {"cpuProfile": cpuProfile,
               "cpuFormats": cpufunctions_utils.CPU_TYPE_FORMATS}
    return template.loader.render_to_string(template_name, context)


class CpuProfilesTable(tables.DataTable):
    cpuProfileName = tables.Column('profilename',
                                   verbose_name=_('Name'))

    cpuassignments = tables.Column(get_cpuassignments,
                                   verbose_name=_("CPU Assignments"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.profilename

    class Meta(object):
        name = "cpuprofiles"
        verbose_name = _("Cpu Profiles")
        multi_select = True
        table_actions = (DeleteCpuProfile, )


# Disk Profile Table

class DeleteDiskProfile(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Storage Profile",
            u"Delete Storage Profiles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Storage Profile",
            u"Deleted Storage Profiles",
            count
        )

    def delete(self, request, diskprofile_id):
        try:
            api.sysinv.host_diskprofile_delete(request, diskprofile_id)
        except Exception as e:
            msg = _('Failed to delete storage profile %s') % diskprofile_id
            LOG.info(msg)

            messages.error(request, e)

            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(request, e, redirect=redirect)


def get_disks(diskprofile):
    template_name = 'admin/inventory/_diskprofiles_diskconfig.html'
    context = {"diskprofile": diskprofile}
    return template.loader.render_to_string(template_name, context)


def get_partitions(diskprofile):
    template_name = 'admin/inventory/_diskprofiles_partitionconfig.html'
    context = {"diskprofile": diskprofile}
    return template.loader.render_to_string(template_name, context)


def get_stors(diskprofile):
    if diskprofile.lvgs:
        template_name = 'admin/inventory/_diskprofiles_lvgconfig.html'
    else:
        template_name = 'admin/inventory/_diskprofiles_storconfig.html'

    context = {"diskprofile": diskprofile}
    return template.loader.render_to_string(template_name, context)


def get_disk_profile_obs(diskprofile):
    template_name = 'admin/inventory/_diskprofiles_diskconfig_obs.html'
    message = ""
    for d in diskprofile.disks:
        if not d.device_path:
            message = _("This storage profile, from a previous release, is "
                        "missing the persistent disk name in the disk config "
                        "field. This profile needs to be deleted and "
                        "recreated.")
    context = {"obs_message": message}
    return template.loader.render_to_string(template_name, context)


class DiskProfilesTable(tables.DataTable):
    diskProfileName = tables.Column('profilename',
                                    verbose_name=_('Name'))

    disks = tables.Column(get_disks,
                          verbose_name=_("Disk Configuration"))

    partitions = tables.Column(get_partitions,
                               verbose_name=_("Partition Configuration"))

    stors = tables.Column(get_stors,
                          verbose_name=_("Storage Configuration"))

    obs = tables.Column(get_disk_profile_obs,
                        verbose_name=_('Observations'))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.profilename

    class Meta(object):
        name = "diskprofiles"
        verbose_name = _("Storage Profiles")
        multi_select = True
        table_actions = (DeleteDiskProfile, )


# Memory Profile Table

class DeleteMemoryProfile(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Memory Profile",
            u"Delete Memory Profiles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Memory Profile",
            u"Deleted Memory Profiles",
            count
        )

    def delete(self, request, memoryprofile_id):
        try:
            api.sysinv.host_memprofile_delete(request, memoryprofile_id)
        except Exception as e:
            msg = _('Failed to delete memory profile %s') % memoryprofile_id
            LOG.info(msg)

            messages.error(request, e)

            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(request, e, redirect=redirect)


def get_memory(memoryProfile):
    template_name = 'admin/inventory/_memoryprofiles_memoryassignments.html'

    memoryList = []
    for node in memoryProfile.nodes:
        for memory in memoryProfile.memory:
            if memory.inode_uuid == node.uuid:
                memory.numa_node = node.numa_node
                memoryList.append(memory)

    memoryProfile.memory = memoryList
    context = {"memoryProfile": memoryProfile}
    return template.loader.render_to_string(template_name, context)


class MemoryProfilesTable(tables.DataTable):
    memoryProfileName = tables.Column('profilename',
                                      verbose_name=_('Name'))

    memory = tables.Column(get_memory,
                           verbose_name=_("Memory Assignments"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.profilename

    class Meta(object):
        name = "memoryprofiles"
        verbose_name = _("Memory Profiles")
        multi_select = True
        table_actions = (DeleteMemoryProfile, )
