#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# Copyright 2012 Nebula, Inc.
# All rights reserved.

"""
Views for managing volumes.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.project.instances import tables

from starlingx_dashboard.api import nova as stx_nova

class CreateForm(forms.SelfHandlingForm):
    tenantP = forms.ChoiceField(label=_("Project"), required=True)
    name = forms.CharField(max_length="255", label=_("Server Group Name"))
    policy = forms.ChoiceField(label=_("Policy"),
                               required=False,
                               widget=forms.Select(
                                   attrs={
                                       'class': 'switchable',
                                       'data-slug': 'policy_ht'}))

    is_best_effort = forms.BooleanField(label=_("Best Effort"), required=False)

    group_size = forms.IntegerField(
        min_value=1,
        label=_("Max Group Size (Instances)"),
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'switchable switched',
                'data-switch-on': 'policy_ht',
                'data-policy_ht-anti-affinity': 'Max Group Size (Instances)',
                'data-policy_ht-affinity': 'Max Group Size (Instances)'}))

    group_size_ht = forms.IntegerField(
        label=_("Max Group Size (Instances)"),
        required=False,
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
                'class': 'switchable switched',
                'data-switch-on': 'policy_ht',
                'data-policy_ht-affinity-hyperthread':
                'Max Group Size (Instances)'}))

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        self.fields['policy'].choices = [("anti-affinity", "anti-affinity"),
                                         ("affinity", "affinity")]

        # Populate available project_id/name choices
        all_projects = []
        try:
            # Get list of available projects.
            all_projects, has_more = api.keystone.tenant_list(request)

            projects_list = [(project.id, project.name)
                             for project in all_projects]

        except Exception:
            projects_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve list of tenants.'))

        self.fields['tenantP'].choices = projects_list

    def handle(self, request, data):
        try:
            policy = data['policy']
            policies = []
            if policy:
                policies.append(policy)
            metadata = {}
            if data['is_best_effort']:
                metadata['wrs-sg:best_effort'] = "true"
            group_size = data['group_size']
            group_size_ht = data['group_size_ht']
            if group_size:
                metadata['wrs-sg:group_size'] = str(group_size)
            elif group_size_ht:
                metadata['wrs-sg:group_size'] = str(group_size_ht)

            project_id = None
            if data['tenantP']:
                project_id = data['tenantP']

            server_group = stx_nova.server_group_create(
                request, data['name'], project_id, metadata, policies)
            return server_group

        except ValidationError as e:
            self.api_error(e.messages[0])
            return False
        except Exception as e:
            exceptions.handle(request, ignore=True)
            self.api_error(_("Unable to create server group."))
            return False


class AttachForm(forms.SelfHandlingForm):
    instance = forms.ChoiceField(label=_("Attach to Server Group"),
                                 help_text=_("Select an server group to "
                                             "attach to."))
    device = forms.CharField(label=_("Device Name"))

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)

        # Hide the device field if the hypervisor doesn't support it.
        hypervisor_features = getattr(settings,
                                      "OPENSTACK_HYPERVISOR_FEATURES", {})
        can_set_mount_point = hypervisor_features.get("can_set_mount_point",
                                                      True)
        if not can_set_mount_point:
            self.fields['device'].widget = forms.widgets.HiddenInput()
            self.fields['device'].required = False

        # populate volume_id
        volume = kwargs.get('initial', {}).get("volume", None)
        if volume:
            volume_id = volume.id
        else:
            volume_id = None
        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
                                                   initial=volume_id)

        # Populate instance choices
        instance_list = kwargs.get('initial', {}).get('instances', [])
        instances = []
        for instance in instance_list:
            if instance.status in tables.ACTIVE_STATES and \
                    not any(instance.id == att["server_id"]
                            for att in volume.attachments):
                instances.append((instance.id, '%s (%s)' % (instance.name,
                                                            instance.id)))
        if instances:
            instances.insert(0, ("", _("Select an instance")))
        else:
            instances = (("", _("No instances available")),)
        self.fields['instance'].choices = instances

    def handle(self, request, data):
        instance_choices = dict(self.fields['instance'].choices)
        instance_name = instance_choices.get(data['instance'],
                                             _("Unknown instance (None)"))
        # The name of the instance in the choices list has the ID appended to
        # it, so let's slice that off...
        instance_name = instance_name.rsplit(" (")[0]
        try:
            attach = api.nova.instance_volume_attach(request,
                                                     data['volume_id'],
                                                     data['instance'],
                                                     data.get('device', ''))
            volume = cinder.volume_get(request, data['volume_id'])
            if not volume.display_name:
                volume_name = volume.id
            else:
                volume_name = volume.display_name
            message = _('Attaching volume %(vol)s to instance '
                        '%(inst)s on %(dev)s.') % {"vol": volume_name,
                                                   "inst": instance_name,
                                                   "dev": attach.device}
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:volumes:index")
            exceptions.handle(request,
                              _('Unable to attach volume.'),
                              redirect=redirect)
