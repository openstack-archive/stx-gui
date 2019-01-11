#
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class UpdateMemory(tables.LinkAction):
    name = "updatememory"
    verbose_name = _("Update Memory")
    url = "horizon:admin:inventory:updatememory"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, memory=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, memory=None):
        host = self.table.kwargs['host']
        return (host._administrative == 'locked' and
                host.subfunctions and
                'worker' in host.subfunctions)


class CreateMemoryProfile(tables.LinkAction):
    name = "createMemoryProfile"
    verbose_name = _("Create Memory Profile")
    url = "horizon:admin:inventory:addmemoryprofile"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        if host.subfunctions and 'storage' in host.subfunctions:
            return False
        return (host.invprovision == 'provisioned' and
                not stx_api.sysinv.is_system_mode_simplex(request))


def get_processor_memory(memory):
    if memory.hugepages_configured == 'True':
        template_name = \
            'admin/inventory/memorys/_memoryfunction_hugepages.html'
    else:
        template_name = \
            'admin/inventory/memorys/_memoryfunction_hugepages_other.html'
    context = {"memory": memory}
    return template.loader.render_to_string(template_name, context)


def get_vm_hugepages(memory):
    template_name = 'admin/inventory/memorys/_vmfunction_hugepages.html'
    context = {"memory": memory}
    return template.loader.render_to_string(template_name, context)


def get_vs_hugepages(memory):
    template_name = 'admin/inventory/memorys/_vswitchfunction_hugepages.html'
    context = {"memory": memory}
    return template.loader.render_to_string(template_name, context)


class MemorysTable(tables.DataTable):
    processor = tables.Column('numa_node',
                              verbose_name=_('Processor'))

    memory = tables.Column(get_processor_memory,
                           verbose_name=_('Memory'))

    vm_huge = tables.Column(get_vm_hugepages,
                            verbose_name=_('Application Pages'))

    vs_huge = tables.Column(get_vs_hugepages,
                            verbose_name=_('vSwitch Pages'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "memorys"
        verbose_name = _("Memory")
        multi_select = False
        table_actions = (UpdateMemory, CreateMemoryProfile,)
