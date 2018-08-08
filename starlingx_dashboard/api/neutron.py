from openstack_dashboard.api import base
from openstack_dashboard.api.neutron import *

class PortForwardingRule(base.APIDictWrapper):
    pass

def portforwarding_list(request, **params):
    rules = (neutronclient(request).
             list_portforwardings(**params).get('portforwardings'))
    return [PortForwardingRule(r) for r in rules]


def portforwarding_get(request, portforwarding_id):
    rule = (neutronclient(request).
            show_portforwarding(portforwarding_id).get('portforwarding'))
    return PortForwardingRule(rule)


def portforwarding_create(request, **kwargs):
    body = {'portforwarding': kwargs}
    rule = neutronclient(request).create_portforwarding(body=body)
    return PortForwardingRule(rule)


def portforwarding_update(request, portforwarding_id, **kwargs):
    body = {'portforwarding': kwargs}
    rule = neutronclient(request).update_portforwarding(
        portforwarding_id, body=body).get('portforwarding')
    return PortForwardingRule(rule)


def portforwarding_delete(request, portforwarding_id):
    return neutronclient(request).delete_portforwarding(portforwarding_id)
