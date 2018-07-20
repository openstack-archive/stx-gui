#
# Copyright (c) 2013-2015 Wind River Systems, Inc.
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


class UpdateCpuFunctions(forms.SelfHandlingForm):
    host = forms.CharField(label=_("host"),
                           required=False,
                           widget=forms.widgets.HiddenInput)
    host_id = forms.CharField(label=_("host_id"),
                              required=False,
                              widget=forms.widgets.HiddenInput)

    platform = forms.CharField(
        label=_("------------------------ Function ------------------------"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    platform_processor0 = forms.DynamicIntegerField(
        label=_("# of Platform Physical Cores on Processor 0:"),
        min_value=0, max_value=99,
        required=False)
    platform_processor1 = forms.DynamicIntegerField(
        label=_("# of Platform Physical Cores on Processor 1:"),
        min_value=0, max_value=99,
        required=False)
    platform_processor2 = forms.DynamicIntegerField(
        label=_("# of Platform Physical Cores on Processor 2:"),
        min_value=0, max_value=99,
        required=False)
    platform_processor3 = forms.DynamicIntegerField(
        label=_("# of Platform Physical Cores on Processor 3:"),
        min_value=0, max_value=99,
        required=False)

    vswitch = forms.CharField(
        label=_("------------------------ Function ------------------------"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    num_cores_on_processor0 = forms.DynamicIntegerField(
        label=_("# of vSwitch Physical Cores on Processor 0:"),
        min_value=0, max_value=99,
        required=False)
    num_cores_on_processor1 = forms.DynamicIntegerField(
        label=_("# of vSwitch Physical Cores on Processor 1:"),
        min_value=0, max_value=99,
        required=False)
    num_cores_on_processor2 = forms.DynamicIntegerField(
        label=_("# of vSwitch Physical Cores on Processor 2:"),
        min_value=0, max_value=99,
        required=False)
    num_cores_on_processor3 = forms.DynamicIntegerField(
        label=_("# of vSwitch Physical Cores on Processor 3:"),
        min_value=0, max_value=99,
        required=False)

    shared_vcpu = forms.CharField(
        label=_("------------------------ Function ------------------------"),
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    num_shared_on_processor0 = forms.DynamicIntegerField(
        label=_("# of Shared Physical Cores on Processor 0:"),
        min_value=0, max_value=99,
        required=False)
    num_shared_on_processor1 = forms.DynamicIntegerField(
        label=_("# of Shared Physical Cores on Processor 1:"),
        min_value=0, max_value=99,
        required=False)
    num_shared_on_processor2 = forms.DynamicIntegerField(
        label=_("# of Shared Physical Cores on Processor 2:"),
        min_value=0, max_value=99,
        required=False)
    num_shared_on_processor3 = forms.DynamicIntegerField(
        label=_("# of Shared Physical Cores on Processor 3:"),
        min_value=0, max_value=99,
        required=False)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(UpdateCpuFunctions, self).__init__(*args, **kwargs)

        self.host = kwargs['initial']['host']

        if kwargs['initial']['platform_processor0'] == 99:  # No Processor
            self.fields[
                'platform_processor0'].widget = forms.widgets.HiddenInput()
        else:
            avail_socket_cores = self.host.physical_cores.get(0, 0)
            self.fields['platform_processor0'].set_max_value(
                avail_socket_cores)
            self.fields[
                'platform_processor0'].help_text = \
                "Processor 0 has %s physical cores." % avail_socket_cores

        if kwargs['initial']['platform_processor1'] == 99:  # No Processor
            self.fields[
                'platform_processor1'].widget = forms.widgets.HiddenInput()
        else:
            avail_socket_cores = self.host.physical_cores.get(1, 0)
            self.fields['platform_processor1'].set_max_value(
                avail_socket_cores)
            self.fields[
                'platform_processor1'].help_text =\
                "Processor 1 has %s physical cores." % avail_socket_cores

        if kwargs['initial']['platform_processor2'] == 99:  # No Processor
            self.fields[
                'platform_processor2'].widget = forms.widgets.HiddenInput()
        else:
            avail_socket_cores = self.host.physical_cores.get(2, 0)
            self.fields['platform_processor2'].set_max_value(
                avail_socket_cores)
            self.fields[
                'platform_processor2'].help_text = \
                "Processor 2 has %s physical cores." % avail_socket_cores

        if kwargs['initial']['platform_processor3'] == 99:  # No Processor
            self.fields[
                'platform_processor3'].widget = forms.widgets.HiddenInput()
        else:
            avail_socket_cores = self.host.physical_cores.get(3, 0)
            self.fields['platform_processor3'].set_max_value(
                avail_socket_cores)
            self.fields[
                'platform_processor3'].help_text = \
                "Processor 3 has %s physical cores." % avail_socket_cores

        if 'compute' not in self.host.subfunctions:
            self.fields['vswitch'].widget = forms.widgets.HiddenInput()
            self.fields[
                'num_cores_on_processor0'].widget = forms.widgets.HiddenInput()
            self.fields[
                'num_cores_on_processor1'].widget = forms.widgets.HiddenInput()
            self.fields[
                'num_cores_on_processor2'].widget = forms.widgets.HiddenInput()
            self.fields[
                'num_cores_on_processor3'].widget = forms.widgets.HiddenInput()
        else:
            if kwargs['initial'][
                    'num_cores_on_processor0'] == 99:  # No Processor
                self.fields[
                    'num_cores_on_processor0'].widget =\
                    forms.widgets.HiddenInput()
            else:
                avail_socket_cores = self.host.physical_cores.get(0, 0)
                self.fields[
                    'num_cores_on_processor0'].set_max_value(
                    avail_socket_cores)
                self.fields[
                    'num_cores_on_processor0'].help_text = \
                    "Processor 0 has %s physical cores." % avail_socket_cores

            if kwargs['initial'][
                    'num_cores_on_processor1'] == 99:  # No Processor
                self.fields[
                    'num_cores_on_processor1'].widget =\
                    forms.widgets.HiddenInput()
            else:
                avail_socket_cores = self.host.physical_cores.get(1, 0)
                self.fields[
                    'num_cores_on_processor1'].set_max_value(
                    avail_socket_cores)
                self.fields[
                    'num_cores_on_processor1'].help_text =\
                    "Processor 1 has %s physical cores." % avail_socket_cores

            if kwargs['initial'][
                    'num_cores_on_processor2'] == 99:  # No Processor
                self.fields[
                    'num_cores_on_processor2'].widget =\
                    forms.widgets.HiddenInput()
            else:
                avail_socket_cores = self.host.physical_cores.get(2, 0)
                self.fields[
                    'num_cores_on_processor2'].set_max_value(
                    avail_socket_cores)
                self.fields[
                    'num_cores_on_processor2'].help_text =\
                    "Processor 2 has %s physical cores." % avail_socket_cores

            if kwargs['initial'][
                    'num_cores_on_processor3'] == 99:  # No Processor
                self.fields[
                    'num_cores_on_processor3'].widget =\
                    forms.widgets.HiddenInput()
            else:
                avail_socket_cores = self.host.physical_cores.get(3, 0)
                self.fields[
                    'num_cores_on_processor3'].set_max_value(
                    avail_socket_cores)
                self.fields[
                    'num_cores_on_processor3'].help_text =\
                    "Processor 3 has %s physical cores." % avail_socket_cores

        for s in range(0, 4):
            processor = 'num_shared_on_processor{0}'.format(s)
            if ('compute' not in self.host.subfunctions or
                    kwargs['initial'][processor] == 99):  # No Processor
                self.fields[processor].widget = forms.widgets.HiddenInput()
            else:
                self.fields[processor].set_max_value(1)
                self.fields[processor].help_text =\
                    "Each processor can have at most one shared core."

    def clean(self):
        cleaned_data = super(UpdateCpuFunctions, self).clean()

        # host_id = cleaned_data.get('host_id')

        try:
            cleaned_data['platform_processor0'] = str(
                cleaned_data['platform_processor0'])
            cleaned_data['platform_processor1'] = str(
                cleaned_data['platform_processor1'])
            cleaned_data['platform_processor2'] = str(
                cleaned_data['platform_processor2'])
            cleaned_data['platform_processor3'] = str(
                cleaned_data['platform_processor3'])

            cleaned_data['num_cores_on_processor0'] = str(
                cleaned_data['num_cores_on_processor0'])
            cleaned_data['num_cores_on_processor1'] = str(
                cleaned_data['num_cores_on_processor1'])
            cleaned_data['num_cores_on_processor2'] = str(
                cleaned_data['num_cores_on_processor2'])
            cleaned_data['num_cores_on_processor3'] = str(
                cleaned_data['num_cores_on_processor3'])

            cleaned_data['num_shared_on_processor0'] = str(
                cleaned_data['num_shared_on_processor0'])
            cleaned_data['num_shared_on_processor1'] = str(
                cleaned_data['num_shared_on_processor1'])
            cleaned_data['num_shared_on_processor2'] = str(
                cleaned_data['num_shared_on_processor2'])
            cleaned_data['num_shared_on_processor3'] = str(
                cleaned_data['num_shared_on_processor3'])

            num_platform_cores = {}
            num_platform_cores[0] = cleaned_data.get('platform_processor0',
                                                     'None')
            num_platform_cores[1] = cleaned_data.get('platform_processor1',
                                                     'None')
            num_platform_cores[2] = cleaned_data.get('platform_processor2',
                                                     'None')
            num_platform_cores[3] = cleaned_data.get('platform_processor3',
                                                     'None')

            num_vswitch_cores = {}
            num_vswitch_cores[0] = cleaned_data.get('num_cores_on_processor0',
                                                    'None')
            num_vswitch_cores[1] = cleaned_data.get('num_cores_on_processor1',
                                                    'None')
            num_vswitch_cores[2] = cleaned_data.get('num_cores_on_processor2',
                                                    'None')
            num_vswitch_cores[3] = cleaned_data.get('num_cores_on_processor3',
                                                    'None')

            num_shared_on_map = {}
            num_shared_on_map[0] = cleaned_data.get('num_shared_on_processor0',
                                                    'None')
            num_shared_on_map[1] = cleaned_data.get('num_shared_on_processor1',
                                                    'None')
            num_shared_on_map[2] = cleaned_data.get('num_shared_on_processor2',
                                                    'None')
            num_shared_on_map[3] = cleaned_data.get('num_shared_on_processor3',
                                                    'None')

            if ('None' in num_platform_cores.values() or
                'None' in num_vswitch_cores.values() or
                    'None' in num_shared_on_map.values()):
                raise forms.ValidationError(_("Invalid entry."))
        except Exception as e:
            LOG.error(e)
            raise forms.ValidationError(_("Invalid entry."))

        # Since only vswitch is allowed to be modified
        cleaned_data['function'] = 'vswitch'
        # NOTE:  shared_vcpu can be changed

        return cleaned_data

    def handle(self, request, data):
        host_id = data['host_id']
        del data['host_id']
        del data['host']

        try:
            host = api.sysinv.host_get(self.request, host_id)
            cpudata = {}
            sharedcpudata = {}
            platformcpudata = {}
            for key, val in data.iteritems():
                if 'num_cores_on_processor' in key or 'function' in key:
                    if key not in self.fields:
                        cpudata[key] = val
                    elif not type(self.fields[key].widget) is\
                            forms.widgets.HiddenInput:
                        cpudata[key] = val
                if 'platform_processor' in key:
                    update_key = 'num_cores_on_processor' + key[-1:]
                    if key not in self.fields:
                        platformcpudata[update_key] = val
                    elif not type(self.fields[key].widget) is\
                            forms.widgets.HiddenInput:
                        platformcpudata[update_key] = val
                if 'num_shared_on_processor' in key:
                    key2 = key.replace('shared', 'cores')
                    if key not in self.fields:
                        sharedcpudata[key2] = val
                    elif not type(self.fields[key].widget) is\
                            forms.widgets.HiddenInput:
                        sharedcpudata[key2] = val

            sharedcpudata['function'] = 'shared'
            platformcpudata['function'] = 'platform'

            api.sysinv.host_cpus_modify(request, host.uuid,
                                        platformcpudata,
                                        cpudata,
                                        sharedcpudata)
            msg = _('CPU Assignments were successfully updated.')
            LOG.debug(msg)
            messages.success(request, msg)
            return self.host.cpus
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            LOG.exception(e)
            msg = _('Failed to update CPU Assignments.')
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)


class AddCpuProfile(forms.SelfHandlingForm):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)
    profilename = forms.CharField(label=_("Cpu Profile Name"),
                                  required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddCpuProfile, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddCpuProfile, self).clean()
        # host_id = cleaned_data.get('host_id')
        return cleaned_data

    def handle(self, request, data):

        cpuProfileName = data['profilename']
        try:
            cpuProfile = api.sysinv.host_cpuprofile_create(request, **data)
            msg = _(
                'Cpu Profile "%s" was successfully created.') % cpuProfileName
            LOG.debug(msg)
            messages.success(request, msg)
            return cpuProfile
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[data['host_id']])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _('Failed to create cpu profile "%s".') % cpuProfileName
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)
