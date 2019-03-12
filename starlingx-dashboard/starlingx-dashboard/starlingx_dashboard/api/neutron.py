#
# Copyright (c) 2018 Intel Corporation
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from openstack_dashboard.api import base
from openstack_dashboard.api.neutron import NeutronAPIDictWrapper
from openstack_dashboard.api.neutron import neutronclient
from openstack_dashboard.api.neutron import QoSPolicy


class PortForwardingRule(base.APIDictWrapper):
    pass


class ProviderNetworkType(NeutronAPIDictWrapper):
    """Wrapper for neutron Provider Network Types."""


class ProviderNetworkRange(NeutronAPIDictWrapper):
    """Wrapper for neutron Provider Networks Id Ranges."""


class ProviderNetwork(NeutronAPIDictWrapper):
    """Wrapper for neutron Provider Networks."""


class ProviderTenantNetwork(NeutronAPIDictWrapper):
    """Wrapper for neutron Provider Tenant Networks."""


def provider_network_type_list(request, **params):
    providernet_types = neutronclient(request).list_providernet_types(
        **params).get(
            'providernet_types')
    return [ProviderNetworkType(t) for t in providernet_types]


def provider_network_create(request, **kwargs):
    body = {'providernet': kwargs}

    providernet = neutronclient(request).create_providernet(body=body).get(
        'providernet')
    return ProviderNetwork(providernet)


def provider_network_list(request, **params):
    providernets = neutronclient(request).list_providernets(**params).get(
        'providernets')
    return [ProviderNetwork(n) for n in providernets]


def provider_network_list_for_tenant(request, tenant_id, **params):
    return provider_network_list(request, tenant_id=tenant_id, **params)


def provider_network_list_tenant_networks(request, providernet_id, **params):
    nets = neutronclient(request).list_networks_on_providernet(
        providernet_id, **params).get('networks')
    return [ProviderTenantNetwork(n) for n in nets]


def provider_network_get(request, providernet_id,
                         expand_subnet=True, **params):
    providernet = neutronclient(request).show_providernet(
        providernet_id, **params).get('providernet')
    return ProviderNetwork(providernet)


def provider_network_delete(request, providernet_id):
    neutronclient(request).delete_providernet(providernet_id)


def provider_network_modify(request, providernet_id, **kwargs):
    body = {'providernet': kwargs}
    providernet = neutronclient(request).update_providernet(
        providernet_id, body=body).get('providernet')
    return ProviderNetwork(providernet)


def provider_network_range_create(request, **kwargs):
    body = {'providernet_range': kwargs}
    _range = neutronclient(request).create_providernet_range(body=body).get(
        'providernet_range')
    return ProviderNetworkRange(_range)


def provider_network_range_list(request, **params):
    ranges = neutronclient(request).list_providernet_ranges(**params).get(
        'providernet_ranges')
    return [ProviderNetworkRange(r) for r in ranges]


def provider_network_range_get(request, range_id,
                               expand_subnet=True, **params):
    _range = neutronclient(request).show_providernet_range(
        range_id, **params).get('providernet_range')
    return ProviderNetworkRange(_range)


def provider_network_range_delete(request, range_id):
    neutronclient(request).delete_providernet_range(range_id)


def provider_network_range_modify(request, range_id, **kwargs):
    body = {'providernet_range': kwargs}
    _range = neutronclient(request).update_providernet_range(
        range_id, body=body).get('providernet_range')
    return ProviderNetworkRange(_range)


def qos_list(request):
    qoses = neutronclient(request).list_qoses().get('qoses')
    return [QoSPolicy(q) for q in qoses]


def qos_get(request, qos_id):
    qos = neutronclient(request).show_qos(qos_id).get('qos')
    return QoSPolicy(qos)


def qos_create(request, **kwargs):
    body = {'qos': kwargs}
    return neutronclient(request).create_qos(body=body)


def qos_update(request, qos_id, **kwargs):
    body = {'qos': kwargs}
    return neutronclient(request).update_qos(qos_id, body=body)


def qos_delete(request, qos_id):
    neutronclient(request).delete_qos(qos_id)


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
