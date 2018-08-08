# Copyright (c) 2013-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.project.routers.portforwardings \
    import forms as project_forms
from starlingx_dashboard.dashboards.project.routers.portforwardings \
    import tabs as project_tabs


class AddPortForwardingRuleView(forms.ModalFormView):
    form_class = project_forms.AddPortForwardingRule
    template_name = 'project/routers/portforwardings/create.html'
    success_url = 'horizon:project:routers:detail'
    failure_url = 'horizon:project:routers:detail'
    page_title = _("Add Port Forwarding Rule")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['router_id'],))

    @memoized.memoized_method
    def get_router_object(self):
        try:
            router_id = self.kwargs["router_id"]
            return api.neutron.router_get(self.request, router_id)
        except Exception:
            redirect = reverse(self.failure_url, args=[router_id])
            msg = _("Unable to retrieve router.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = (super(AddPortForwardingRuleView, self).
                   get_context_data(**kwargs))
        context['router'] = self.get_router_object()
        return context

    def get_initial(self):
        router = self.get_router_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name,
                "tenant_id": router.tenant_id}


class UpdatePortForwardingRuleView(forms.ModalFormView):
    form_class = project_forms.UpdatePortForwardingRule
    template_name = 'project/routers/portforwardings/update.html'
    success_url = 'horizon:project:routers:detail'
    failure_url = 'horizon:project:routers:detail'
    page_title = _("Update Port Forwarding Rule")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['router_id'],))

    @memoized.memoized_method
    def get_router_object(self):
        try:
            router_id = self.kwargs["router_id"]
            return api.neutron.router_get(self.request, router_id)
        except Exception:
            redirect = reverse(self.failure_url, args=[router_id])
            msg = _("Unable to retrieve router.")
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def get_portforwarding_object(self):
        try:
            router_id = self.kwargs["router_id"]
            portforwarding_id = self.kwargs["portforwarding_id"]
            return stx_api.neutron.portforwarding_get(self.request,
                                                  portforwarding_id)
        except Exception:
            redirect = reverse(self.failure_url, args=[router_id])
            msg = _("Unable to retrieve port forwarding rule.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdatePortForwardingRuleView, self).get_context_data(
            **kwargs)
        context['router'] = self.get_router_object()
        context['portforwarding'] = self.get_portforwarding_object()
        return context

    def get_initial(self):
        router = self.get_router_object()
        rule = self.get_portforwarding_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name,
                "tenant_id": router.tenant_id,
                "portforwarding_id": self.kwargs['portforwarding_id'],
                "inside_addr": rule.inside_addr,
                "inside_port": rule.inside_port,
                "outside_port": rule.outside_port,
                "protocol": rule.protocol,
                "description": rule.description}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.PortForwardingDetailTabs
    template_name = 'project/networks/portforwardings/detail.html'
