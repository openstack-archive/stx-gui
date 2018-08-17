# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#

from django.core.urlresolvers import NoReverseMatch
from django.core.urlresolvers import reverse
from django.utils import html
from django.utils import safestring
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.project.volumes.tables \
    import get_attachment_name
from openstack_dashboard.usage import quotas

from starlingx_dashboard.api import nova as stx_nova

DELETABLE_STATES = ("available", "error")


class DeleteServerGroup(tables.DeleteAction):
    data_type_singular = _("Server Group")
    data_type_plural = _("Server Groups")
    action_past = _("Scheduled deletion of")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Server Group",
            u"Delete Server Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Server Group",
            u"Deleted Server Groups",
            count
        )

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)

        try:
            stx_nova.server_group_delete(request, obj_id)
        except Exception:
            msg = _('Unable to delete group "%s" because it is not empty. '
                    'Either delete the member '
                    'instances or remove them from the group.')
            exceptions.check_message(["group", "not", "empty."], msg % name)
            raise

    # maybe do a precheck to see if the group is empty first?
    def allowed(self, request, server_group=None):
        return True


class CreateServerGroup(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Server Group")
    url = "horizon:project:server_groups:create"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def allowed(self, request, volume=None):
        usages = quotas.tenant_quota_usages(request)
        if usages['server_groups']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = _("Create Server Group")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True


class EditAttachments(tables.LinkAction):
    name = "attachments"
    verbose_name = _("Edit Attachments")
    url = "horizon:project:server_groups:attach"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, server_group=None):
        return True  # volume.status in ("available", "in-use")


class CreateSnapshot(tables.LinkAction):
    name = "snapshots"
    verbose_name = _("Create Snapshot")
    url = "horizon:project:server_groups:create_snapshot"
    classes = ("ajax-modal", "btn-camera")

    def allowed(self, request, server_group=None):
        return True  # server_group.status == "available"


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, server_group_id):
        server_group = stx_nova.server_group_get(request, server_group_id)
        if not server_group.name:
            server_group.name = server_group_id
        return server_group


def get_policies(server_group):
    policies = ', '.join(server_group.policies)
    return policies


def get_metadata(server_group):
    metadata_items = ['{}:{}'.format(x, y) for x, y in
                      server_group.metadata.items()]
    metadata = ', '.join(metadata_items)
    return metadata


def get_member_name(request, server_id):
    try:
        server = api.nova.server_get(request, server_id)
        name = server.name
    except Exception:
        name = None
        exceptions.handle(request, _("Unable to retrieve "
                                     "member information."))
    # try and get a URL
    try:
        url = reverse("horizon:project:instances:detail", args=(server_id,))
        instance = '<a href="%s">%s</a>' % (url, html.escape(name))
    except NoReverseMatch:
        instance = name
    return instance


class MemberColumn(tables.Column):
    """Customized column class

    Customized column class that does complex processing on the instances
    in a server group.  This was substantially copied
    from the volume equivalent.
    """

    def get_raw_data(self, server_group):
        request = self.table.request
        link = _('%(name)s (%(id)s)')
        members = []
        for member in server_group.members:
            member_id = member
            name = get_member_name(request, member)
            vals = {"name": name, "id": member_id}
            members.append(link % vals)
        return safestring.mark_safe(", ".join(members))


def get_server_group_type(server_group):
    return server_group.volume_type if server_group.volume_type != "None" \
        else None


class ServerGroupsFilterAction(tables.FilterAction):
    def filter(self, table, server_groups, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [group for group in server_groups
                if q in group.display_name.lower()]


class ServerGroupsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Group Name"),
                         link="horizon:project:server_groups:detail")
    policies = tables.Column(get_policies,
                             verbose_name=_("Policies"))
    members = MemberColumn("members",
                           verbose_name=_("Members"))
    metadata = tables.Column(get_metadata,
                             verbose_name=_("Metadata"))

    class Meta(object):
        name = "server_groups"
        verbose_name = _("Server Groups")
        row_class = UpdateRow
        table_actions = (
            CreateServerGroup, DeleteServerGroup, ServerGroupsFilterAction)
        row_actions = (DeleteServerGroup,)

    def get_object_display(self, obj):
        return obj.name


class DetachServerGroup(tables.BatchAction):
    name = "detach"
    action_present = _("Detach")
    action_past = _("Detaching")  # This action is asynchronous.
    data_type_singular = _("Server Group")
    data_type_plural = _("Server Groups")
    classes = ('btn-danger', 'btn-detach')

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Server Group",
            u"Server Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Group",
            u"Deleted Groups",
            count
        )

    def action(self, request, obj_id):
        attachment = self.table.get_object_by_id(obj_id)
        api.nova.instance_server_group_detach(
            request,
            attachment.get('server_id', None),
            obj_id)

    def get_success_url(self, request):
        return reverse('horizon:project:server_groups:index')


class AttachedInstanceColumn(tables.Column):
    """Customized column class

    Customized column class that does complex processing on the attachments
    for a server group.
    """

    def get_raw_data(self, attachment):
        request = self.table.request
        return safestring.mark_safe(get_attachment_name(request, attachment))


class AttachmentsTable(tables.DataTable):
    instance = AttachedInstanceColumn(get_member_name,
                                      verbose_name=_("Instance"))
    device = tables.Column("device",
                           verbose_name=_("Device"))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, attachment):
        instance_name = get_attachment_name(self.request, attachment)
        vals = {"dev": attachment['device'],
                "instance_name": html.strip_tags(instance_name)}
        return _("%(dev)s on instance %(instance_name)s") % vals

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            if self.get_object_id(obj) == obj_id:
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    class Meta(object):
        name = "attachments"
        verbose_name = _("Attachments")
        table_actions = (DetachServerGroup,)
        row_actions = (DetachServerGroup,)
