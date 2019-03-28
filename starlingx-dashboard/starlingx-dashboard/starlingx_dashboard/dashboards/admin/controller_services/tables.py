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
#  Copyright (c) 2019 Wind River Systems, Inc.
#
#  SPDX-License-Identifier: Apache-2.0
#
from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables


class ControllerServiceFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            if q in service.type.lower():
                return True
            return False

        return filter(comp, services)


def cs_get_c0(iservice):
    template_name = 'controller_services/_services_c0.html'
    context = {"iservice": iservice}
    return template.loader.render_to_string(template_name, context)


def cs_get_c1(iservice):
    template_name = 'controller_services/_services_c1.html'
    context = {"iservice": iservice}
    return template.loader.render_to_string(template_name, context)


class ControllerServicesTable(tables.DataTable):
    servicename = tables.Column("servicename", verbose_name=_('Name'))
    c0 = tables.Column(cs_get_c0, verbose_name=_('controller-0'))
    c1 = tables.Column(cs_get_c1, verbose_name=_('controller-1'))

    class Meta(object):
        name = "controller_services"
        verbose_name = _("Controller Services")
        table_actions = (ControllerServiceFilterAction,)
        multi_select = False
