# Copyright 2012 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#


import logging

from django.core.urlresolvers import reverse  # noqa
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from neutronclient.common import exceptions as neutron_exceptions

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class DeleteProviderNetworkRange(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Range",
            "Delete Ranges",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Range",
            "Deleted Ranges",
            count
        )

    def get_redirect_url(self):
        providernet_id = self.table.kwargs['providernet_id']
        return reverse('horizon:admin:datanets:datanets:detail',
                       args=(providernet_id,))

    def delete(self, request, obj_id):
        try:
            stx_api.neutron.provider_network_range_delete(request, obj_id)
        except neutron_exceptions.NeutronClientException as e:
            LOG.info(str(e))
            exceptions.handle(request,
                              str(e),
                              redirect=self.get_redirect_url())
        except Exception:
            msg = _('Failed to delete provider network range %s') % obj_id
            LOG.info(msg)
            exceptions.handle(request, msg, redirect=self.get_redirect_url())


class CreateProviderNetworkRange(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Range")
    url = "horizon:admin:datanets:datanets:createrange"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        providernet_id = self.table.kwargs['providernet_id']
        return reverse(self.url, args=(providernet_id,))

    def allowed(self, request, datum=None):
        # TODO(datanetworks): depends on spec network-segment-range-management
        return False


class EditProviderNetworkRange(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Range")
    url = "horizon:admin:datanets:datanets:editrange"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, providernet_range):
        providernet_id = self.table.kwargs['providernet_id']
        return reverse(self.url, args=(providernet_id, providernet_range.id))


def _get_vxlan_provider_attributes(datum):
    vxlan = datum.vxlan
    return (_("Mode: {} Group: {}, Port: {}, TTL: {}").format(
            vxlan['mode'], vxlan['group'], vxlan['port'], vxlan['ttl']))


def _get_provider_attributes(datum):
    if hasattr(datum, "vxlan"):
        return _get_vxlan_provider_attributes(datum)
    return _("n/a")


class ProviderNetworkRangeTable(tables.DataTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    url = "horizon:admin:datanets:datanets:ranges:detail"
    name = tables.Column("name", verbose_name=_("Name"), link=url)
    minimum = tables.Column("minimum", verbose_name=_("Minimum"))
    maximum = tables.Column("maximum", verbose_name=_("Maximum"))
    attributes = tables.Column(_get_provider_attributes,
                               verbose_name=_("Provider Attributes"))

    class Meta(object):
        name = "provider_network_ranges"
        verbose_name = _("Segmentation Ranges")
        table_actions = (CreateProviderNetworkRange,
                         DeleteProviderNetworkRange)
        row_actions = (EditProviderNetworkRange, DeleteProviderNetworkRange)
