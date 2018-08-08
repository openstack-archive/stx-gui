# Copyright (c) 2013-2015 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class AddPortForwardingRule(policy.PolicyTargetMixin, tables.LinkAction):
    name = "createportforwardingrule"
    verbose_name = _("Add Rule")
    url = "horizon:project:routers:addportforwardingrule"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_portforwarding"),)

    def get_link_url(self, datum=None):
        router_id = self.table.kwargs['router_id']
        return reverse(self.url, args=(router_id,))


class UpdatePortForwardingRule(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updateportforwardingrule"
    verbose_name = _("Update Rule")
    url = "horizon:project:routers:updateportforwardingrule"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "update_portforwarding"),)

    def get_link_url(self, datum=None):
        router_id = self.table.kwargs['router_id']
        portforwarding_id = datum['id']
        return reverse(self.url, args=(router_id, portforwarding_id,))


class RemovePortForwardingRule(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Rule",
            u"Delete Rule",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Port Forwarding Rule",
            u"Deleted Port Forwarding Rules",
            count
        )

    failure_url = 'horizon:project:routers:detail'
    policy_rules = (("network", "delete_portforwarding"),)

    def delete(self, request, obj_id):
        try:
            api.neutron.portforwarding_delete(
                request, portforwarding_id=obj_id)
        except Exception:
            msg = _('Failed to delete port forwarding rule %s') % obj_id
            LOG.info(msg)
            router_id = self.table.kwargs['router_id']
            redirect = reverse(self.failure_url,
                               args=[router_id])
            exceptions.handle(request, msg, redirect=redirect)


def _get_port_link_url(rule):
    port = rule['port']
    link = 'horizon:project:networks:ports:detail'
    return reverse(link, args=(port.id,))


def _get_port_name_or_id(rule):
    port = rule['port']
    if port.name:
        return port.name
    return '(' + port.id[:8] + ')'


class PortForwardingRulesTable(tables.DataTable):
    port = tables.Column(_get_port_name_or_id, verbose_name=_("Port"),
                         link=_get_port_link_url)
    inside_addr = tables.Column("inside_addr",
                                verbose_name=_("Private Address"))
    inside_port = tables.Column("inside_port", verbose_name=_("Private Port"))
    outside_port = tables.Column("outside_port", verbose_name=_("Public Port"))
    protocol = tables.Column("protocol", verbose_name=_("Protocol"))
    description = tables.Column("description", verbose_name=_("Description"))

    def get_object_display(self, portforwarding):
        return portforwarding.id

    class Meta(object):
        name = "portforwardings"
        verbose_name = _("Port Forwarding Rules")
        table_actions = (AddPortForwardingRule, RemovePortForwardingRule)
        row_actions = (UpdatePortForwardingRule, RemovePortForwardingRule, )
