#
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class UpdateMemory(forms.SelfHandlingForm):
    host = forms.CharField(label=_("host"),
                           required=False,
                           widget=forms.widgets.HiddenInput)

    host_id = forms.CharField(label=_("host_id"),
                              required=False,
                              widget=forms.widgets.HiddenInput)

    platform_memory = forms.CharField(
        label=_("Platform Memory for Node 0"),
        required=False)

    vm_hugepages_nr_2M = forms.CharField(
        label=_("# of VM 2M Hugepages Node 0"),
        required=False)

    vm_hugepages_nr_1G = forms.CharField(
        label=_("# of VM 1G Hugepages Node 0"),
        required=False)

    platform_memory_two = forms.CharField(
        label=_("Platform Memory for Node 1"),
        required=False)

    vm_hugepages_nr_2M_two = forms.CharField(
        label=_("# of VM 2M Hugepages Node 1"),
        required=False)

    vm_hugepages_nr_1G_two = forms.CharField(
        label=_("# of VM 1G Hugepages Node 1"),
        required=False)

    platform_memory_three = forms.CharField(
        label=_("Platform Memory for Node 2"),
        required=False)

    vm_hugepages_nr_2M_three = forms.CharField(
        label=_("# of VM 2M Hugepages Node 2"),
        required=False)

    vm_hugepages_nr_1G_three = forms.CharField(
        label=_("# of VM 1G Hugepages Node 2"),
        required=False)

    platform_memory_four = forms.CharField(
        label=_("Platform Memory for Node 3"),
        required=False)

    vm_hugepages_nr_2M_four = forms.CharField(
        label=_("# of VM 2M Hugepages Node 3"),
        required=False)

    vm_hugepages_nr_1G_four = forms.CharField(
        label=_("# of VM 1G Hugepages Node 3"),
        required=False)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, request, *args, **kwargs):
        super(UpdateMemory, self).__init__(request, *args, **kwargs)

        self.host = kwargs['initial']['host']

        memory_fieldsets = [
            {
                'platform_memory': self.fields['platform_memory'],
                'vm_hugepages_nr_2M': self.fields['vm_hugepages_nr_2M'],
                'vm_hugepages_nr_1G': self.fields['vm_hugepages_nr_1G']
            },
            {
                'platform_memory': self.fields['platform_memory_two'],
                'vm_hugepages_nr_2M': self.fields['vm_hugepages_nr_2M_two'],
                'vm_hugepages_nr_1G': self.fields['vm_hugepages_nr_1G_two']
            },
            {
                'platform_memory': self.fields['platform_memory_three'],
                'vm_hugepages_nr_2M': self.fields['vm_hugepages_nr_2M_three'],
                'vm_hugepages_nr_1G': self.fields['vm_hugepages_nr_1G_three']
            },
            {
                'platform_memory': self.fields['platform_memory_four'],
                'vm_hugepages_nr_2M': self.fields['vm_hugepages_nr_2M_four'],
                'vm_hugepages_nr_1G': self.fields['vm_hugepages_nr_1G_four']
            }
        ]

        count = 0
        for m in self.host.memorys:
            count = count + 1
            for n in self.host.nodes:
                if m.inode_uuid == n.uuid:
                    field_set = memory_fieldsets[int(n.numa_node)]
                    platform_field = field_set['platform_memory']
                    platform_field.help_text = \
                        'Minimum platform memory(MiB): ' + \
                        str(m.minimum_platform_reserved_mib)

                    platform_field.initial = str(m.platform_reserved_mib)

                    vm_2M_field = field_set['vm_hugepages_nr_2M']
                    vm_2M_field.help_text = \
                        'Maximum 2M pages: ' + \
                        str(m.vm_hugepages_possible_2M)

                    if m.vm_hugepages_nr_2M_pending:
                        vm_2M_field.initial = str(m.vm_hugepages_nr_2M_pending)
                    elif m.vm_hugepages_nr_2M:
                        vm_2M_field.initial = str(m.vm_hugepages_nr_2M)
                    else:
                        vm_2M_field.initial = '0'

                    vm_1G_field = field_set['vm_hugepages_nr_1G']
                    vm_1g_supported = m.vm_hugepages_use_1G != 'False'
                    if vm_1g_supported:
                        help_msg = 'Maximum 1G pages: ' + \
                                   str(m.vm_hugepages_possible_1G)
                    else:
                        help_msg = 'This node does not support 1G hugepages'

                    vm_1G_field.help_text = help_msg

                    if m.vm_hugepages_nr_1G_pending:
                        vm_1G_field.initial = str(m.vm_hugepages_nr_1G_pending)
                    elif m.vm_hugepages_nr_1G:
                        vm_1G_field.initial = str(m.vm_hugepages_nr_1G)
                    elif vm_1g_supported:
                        vm_1G_field.initial = '0'
                    else:
                        vm_1G_field.initial = ''

                    if not vm_1g_supported:
                        vm_1G_field.widget.attrs['disabled'] = 'disabled'

                    break

        while count < 4:
            field_set = memory_fieldsets[count]
            field_set['platform_memory'].widget = \
                forms.widgets.HiddenInput()
            field_set['vm_hugepages_nr_2M'].widget = \
                forms.widgets.HiddenInput()
            field_set['vm_hugepages_nr_1G'].widget = \
                forms.widgets.HiddenInput()
            count += 1

    def clean(self):
        cleaned_data = super(UpdateMemory, self).clean()
        # host_id = cleaned_data.get('host_id')
        return cleaned_data

    def handle(self, request, data):

        host_id = data['host_id']
        del data['host_id']
        del data['host']

        node = []
        node.append('node0')

        if data['platform_memory_two'] or \
           data['vm_hugepages_nr_2M_two'] or \
           data['vm_hugepages_nr_1G_two']:
            node.append('node1')

        if data['platform_memory_three'] or \
           data['vm_hugepages_nr_2M_three'] or \
           data['vm_hugepages_nr_1G_three']:
            node.append('node2')

        if data['platform_memory_four'] or \
           data['vm_hugepages_nr_2M_four'] or \
           data['vm_hugepages_nr_1G_four']:
            node.append('node3')

        # host = api.sysinv.host_get(request, host_id)
        pages_1G = {}
        pages_2M = {}
        plat_mem = {}

        # Node 0 arguments
        if not data['platform_memory']:
            del data['platform_memory']
        else:
            plat_mem['node0'] = data['platform_memory']

        if not data['vm_hugepages_nr_2M']:
            del data['vm_hugepages_nr_2M']
        else:
            pages_2M['node0'] = data['vm_hugepages_nr_2M']

        if not data['vm_hugepages_nr_1G']:
            del data['vm_hugepages_nr_1G']
        else:
            pages_1G['node0'] = data['vm_hugepages_nr_1G']

        # Node 1 arguments
        if not data['platform_memory_two']:
            del data['platform_memory_two']
        else:
            plat_mem['node1'] = data['platform_memory_two']

        if not data['vm_hugepages_nr_2M_two']:
            del data['vm_hugepages_nr_2M_two']
        else:
            pages_2M['node1'] = data['vm_hugepages_nr_2M_two']

        if not data['vm_hugepages_nr_1G_two']:
            del data['vm_hugepages_nr_1G_two']
        else:
            pages_1G['node1'] = data['vm_hugepages_nr_1G_two']

        # Node 2 arguments
        if not data['platform_memory_three']:
            del data['platform_memory_three']
        else:
            plat_mem['node2'] = data['platform_memory_three']

        if not data['vm_hugepages_nr_2M_three']:
            del data['vm_hugepages_nr_2M_three']
        else:
            pages_2M['node2'] = data['vm_hugepages_nr_2M_three']

        if not data['vm_hugepages_nr_1G_three']:
            del data['vm_hugepages_nr_1G_three']
        else:
            pages_1G['node2'] = data['vm_hugepages_nr_1G_three']

        # Node 3 arguments
        if not data['platform_memory_four']:
            del data['platform_memory_four']
        else:
            plat_mem['node3'] = data['platform_memory_four']

        if not data['vm_hugepages_nr_2M_four']:
            del data['vm_hugepages_nr_2M_four']
        else:
            pages_2M['node3'] = data['vm_hugepages_nr_2M_four']

        if not data['vm_hugepages_nr_1G_four']:
            del data['vm_hugepages_nr_1G_four']
        else:
            pages_1G['node3'] = data['vm_hugepages_nr_1G_four']

        try:
            for nd in node:
                node_found = False
                for m in self.host.memorys:
                    for n in self.host.nodes:
                        if m.inode_uuid == n.uuid:
                            if int(n.numa_node) == int(node.index(nd)):
                                node_found = True
                            break
                    if node_found:
                        break

                if node_found:
                    new_data = {}
                    if nd in plat_mem:
                        new_data['platform_reserved_mib'] = plat_mem[nd]
                    if nd in pages_2M:
                        new_data['vm_hugepages_nr_2M_pending'] = pages_2M[nd]
                    if nd in pages_1G:
                        new_data['vm_hugepages_nr_1G_pending'] = pages_1G[nd]

                    if new_data:
                        api.sysinv.host_memory_update(request, m.uuid,
                                                      **new_data)

                else:
                    msg = _('Failed to find %s') % nd
                    messages.error(request, msg)
                    LOG.error(msg)
                    # Redirect to failure pg
                    redirect = reverse(self.failure_url, args=[host_id])
                    return shortcuts.redirect(redirect)

            msg = _('Memory allocation has been successfully '
                    'updated.')
            LOG.debug(msg)
            messages.success(request, msg)
            return self.host.memorys
        except exc.ClientException as ce:
            # Allow REST API error message to appear on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)

        except Exception:
            msg = _('Failed to update memory allocation')
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)


class AddMemoryProfile(forms.SelfHandlingForm):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)
    profilename = forms.CharField(label=_("Memory Profile Name"),
                                  required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddMemoryProfile, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddMemoryProfile, self).clean()
        # host_id = cleaned_data.get('host_id')
        return cleaned_data

    def handle(self, request, data):

        memoryProfileName = data['profilename']
        try:
            memoryProfile = api.sysinv.host_memprofile_create(request, **data)
            msg = _('Memory Profile "%s" was successfully created.') % \
                memoryProfileName
            LOG.debug(msg)
            messages.success(request, msg)
            return memoryProfile
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[data['host_id']])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _('Failed to create memory profile "%s".') % \
                memoryProfileName
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)
