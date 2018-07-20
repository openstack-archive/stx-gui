#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.system_config.forms \
    import CreateSDNController
from openstack_dashboard.dashboards.admin.system_config.forms \
    import EditPipeline
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdatecDNS
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdatecEXT_OAM
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdatecNTP
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdateiStorage
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdateiStoragePools
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdateSDNController
from openstack_dashboard.dashboards.admin.system_config.forms \
    import UpdateSystem
from openstack_dashboard.dashboards.admin.system_config.tables \
    import SDNControllerTable
from openstack_dashboard.dashboards.admin.system_config.tabs \
    import ConfigTabs


LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = ConfigTabs
    template_name = 'admin/system_config/index.html'
    page_title = _("System Configuration")

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)


class UpdateSystemView(forms.ModalFormView):
    form_class = UpdateSystem
    template_name = 'admin/system_config/update_system.html'
    context_object_name = 'system'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateSystemView, self).get_context_data(**kwargs)
        context['system_id'] = self.kwargs['system_id']
        return context

    def get_initial(self):
        try:
            system = api.sysinv.system_get(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve system data."))

        return {'system_uuid': system.uuid,
                'name': system.name,
                'description': system.description}


class UpdatecDNSView(forms.ModalFormView):
    form_class = UpdatecDNS
    template_name = 'admin/system_config/update_cdns_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdatecDNSView, self).get_context_data(**kwargs)
        dns_list = api.sysinv.dns_list(self.request)

        if dns_list:
            if "uuid" in dns_list[0]._attrs:
                uuid = dns_list[0].uuid

            else:
                uuid = " "

        else:
            uuid = " "

        context['uuid'] = uuid
        return context

    def get_initial(self):
        # request = self.request
        dns_form_data = {'uuid': ' ',
                         'NAMESERVER_1': None,
                         'NAMESERVER_2': None,
                         'NAMESERVER_3': None}

        try:
            dns_list = api.sysinv.dns_list(self.request)

            if dns_list:
                dns = dns_list[0]

                dns_form_data['uuid'] = dns.uuid
                if dns.nameservers:
                    servers = dns.nameservers.split(",")
                    for index, server in enumerate(servers):
                        dns_form_data['NAMESERVER_%s' % (index + 1)] = server

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve DNS data."))

        return dns_form_data


class UpdatecNTPView(forms.ModalFormView):
    form_class = UpdatecNTP
    template_name = 'admin/system_config/update_cntp_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdatecNTPView, self).get_context_data(**kwargs)
        ntp_list = api.sysinv.ntp_list(self.request)

        if ntp_list:
            if "uuid" in ntp_list[0]._attrs:
                uuid = ntp_list[0].uuid

            else:
                uuid = " "

        else:
            uuid = " "

        context['uuid'] = uuid
        return context

    def get_initial(self):
        ntp_form_data = {'uuid': ' ',
                         'NTP_SERVER_1': None,
                         'NTP_SERVER_2': None,
                         'NTP_SERVER_3': None}

        try:
            ntp_list = api.sysinv.ntp_list(self.request)

            if ntp_list:
                ntp = ntp_list[0]

                ntp_form_data['uuid'] = ntp.uuid
                if ntp.ntpservers:
                    servers = ntp.ntpservers.split(",")
                    for index, server in enumerate(servers):
                        ntp_form_data['NTP_SERVER_%s' % (index + 1)] = server

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve NTP data."))

        return ntp_form_data


class UpdatecEXT_OAMView(forms.ModalFormView):
    form_class = UpdatecEXT_OAM
    template_name = 'admin/system_config/update_coam_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdatecEXT_OAMView, self).get_context_data(**kwargs)
        extoam_list = api.sysinv.extoam_list(self.request)

        if extoam_list:
            if 'uuid' in extoam_list[0]._attrs:
                uuid = extoam_list[0].uuid

            else:
                uuid = " "

        else:
            uuid = " "

        context['uuid'] = uuid
        return context

    def get_initial(self):

        oam_form_data = {'uuid': ' ',
                         'EXTERNAL_OAM_SUBNET': None,
                         'EXTERNAL_OAM_FLOATING_ADDRESS': None,
                         'EXTERNAL_OAM_GATEWAY_ADDRESS': None,
                         'EXTERNAL_OAM_0_ADDRESS': None,
                         'EXTERNAL_OAM_1_ADDRESS': None,
                         }

        try:

            extoam_list = api.sysinv.extoam_list(self.request)

            if extoam_list:
                if extoam_list[0]:

                    extoam_attrs = extoam_list[0]._attrs

                    if 'uuid' in extoam_attrs:
                        oam_form_data['uuid'] = extoam_list[0].uuid

                    oam_form_data['EXTERNAL_OAM_SUBNET'] = \
                        extoam_list[0]._oam_subnet
                    oam_form_data['EXTERNAL_OAM_FLOATING_ADDRESS'] = \
                        extoam_list[0]._oam_floating_ip
                    oam_form_data['EXTERNAL_OAM_GATEWAY_ADDRESS'] = \
                        extoam_list[0]._oam_gateway_ip
                    oam_form_data['EXTERNAL_OAM_0_ADDRESS'] = \
                        extoam_list[0]._oam_c0_ip
                    oam_form_data['EXTERNAL_OAM_1_ADDRESS'] = \
                        extoam_list[0]._oam_c1_ip

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve OAM data."))

        return oam_form_data


class UpdateiStorageView(forms.ModalFormView):
    form_class = UpdateiStorage
    success_url = reverse_lazy('horizon:admin:system_config:index')
    template_name = 'admin/system_config/update_istorage_table.html'

    def get_context_data(self, **kwargs):
        context = super(UpdateiStorageView, self).get_context_data(**kwargs)

        if api.sysinv.is_system_mode_simplex(self.request):
            context['is_system_mode_simplex'] = True

        return context

    def get_initial(self):
        system = api.sysinv.system_get(self.request)

        fs_list = api.sysinv.controllerfs_list(self.request)
        fs_form_data = {fs.name.replace("-", "_"): fs.size for fs in fs_list}
        fs_form_data.update({'uuid': system.uuid})
        return fs_form_data


class UpdateiStoragePoolsView(forms.ModalFormView):
    form_class = UpdateiStoragePools
    template_name = 'admin/system_config/update_istorage_pools_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        ctxt = super(UpdateiStoragePoolsView, self).get_context_data(**kwargs)
        ctxt['tier_name'] = self.kwargs['tier_name']

        storage_list = api.sysinv.storagepool_list(self.request)

        ctxt['uuid'] = " "
        for s in storage_list:
            if s.tier_name == ctxt['tier_name']:
                ctxt['uuid'] = s.uuid
                ctxt['tier_name'] = s.tier_name
                ctxt['tier_total'] = s.ceph_total_space_gib

                ctxt['configured_quota'] = 0
                # check before adding each value in case it is None
                if s.cinder_pool_gib:
                    ctxt['configured_quota'] += s.cinder_pool_gib
                if s.glance_pool_gib:
                    ctxt['configured_quota'] += s.glance_pool_gib
                if s.ephemeral_pool_gib:
                    ctxt['configured_quota'] += s.ephemeral_pool_gib
                if s.object_pool_gib:
                    ctxt['configured_quota'] += s.object_pool_gib
                break

        return ctxt

    def get_initial(self):
        form_data = {'uuid': ' ',
                     'tier_name': None,
                     'cinder_pool_gib': None,
                     'glance_pool_gib': None,
                     'ephemeral_pool_gib': None,
                     'object_pool_gib': None}

        try:
            target_tier = self.kwargs['tier_name']
            storage_list = api.sysinv.storagepool_list(self.request)
            for s in storage_list:
                if s.tier_name == target_tier:

                    storage_attrs = s._attrs

                    if 'uuid' in storage_attrs:
                        form_data['uuid'] = s.uuid

                    if 'tier_name' in storage_attrs:
                        form_data['tier_name'] = s.tier_name

                    if 'cinder_pool_gib' in storage_attrs:
                        form_data['cinder_pool_gib'] = s.cinder_pool_gib

                    if 'glance_pool_gib' in storage_attrs:
                        form_data['glance_pool_gib'] = s.glance_pool_gib

                    if 'ephemeral_pool_gib' in storage_attrs:
                        form_data['ephemeral_pool_gib'] = s.ephemeral_pool_gib

                    if 'object_pool_gib' in storage_attrs:
                        form_data['object_pool_gib'] = s.object_pool_gib

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve size of Ceph pools."))

        return form_data


######################################################
#           SDN Controller Modal Views               #
######################################################


class DetailSDNControllerView(tables.DataTableView):
    table_class = SDNControllerTable
    template_name = 'admin/system_config/detail_sdn_controller_table.html'
    failure_url = reverse_lazy('horizon:admin:system_config:index')

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            uuid = self.kwargs['uuid']
            try:
                self._object = api.sysinv.sdn_controller_get(self.request,
                                                             uuid)
            except Exception:
                redirect = self.failure_url
                msg = _("Unable to retrieve details for "
                        "SDN controller")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(DetailSDNControllerView, self).\
            get_context_data(**kwargs)
        controller = self._get_object()
        context['uuid'] = controller.uuid
        context['sdn_controller_table'] = controller
        return context


class CreateSDNControllerView(forms.ModalFormView):
    form_class = CreateSDNController
    template_name = 'admin/system_config/create_sdn_controller_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')


class UpdateSDNControllerView(forms.ModalFormView):
    form_class = UpdateSDNController
    template_name = 'admin/system_config/update_sdn_controller_table.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateSDNControllerView, self).\
            get_context_data(**kwargs)
        controller = self._get_object()
        context['uuid'] = controller.uuid
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            controller_uuid = self.kwargs['uuid']
            try:
                self._object = api.sysinv.sdn_controller_get(self.request,
                                                             controller_uuid)
            except Exception:
                redirect = self.success_url
                msg = _('Unable to retrieve SDN controller details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        controller = self._get_object()
        data = {'uuid': controller.uuid,
                'ip_address': controller.ip_address,
                'port': controller.port,
                'transport': controller.transport,
                'state': controller.state}
        return data


######################################################
#           Pipeline/PM Views                        #
######################################################
class UpdatePipelineView(forms.ModalFormView):
    form_class = EditPipeline
    template_name = 'admin/system_config/edit.html'
    success_url = reverse_lazy('horizon:admin:system_config:index')

    def get_context_data(self, **kwargs):
        context = super(UpdatePipelineView, self).get_context_data(**kwargs)
        context['pipeline_name'] = self.kwargs['pipeline_name']
        return context

    def get_initial(self):
        pipeline = None
        try:
            target_pipeline = self.kwargs['pipeline_name']
            pipelines = api.ceilometer.pipeline_list(self.request)
            for p in pipelines:
                if p.name == target_pipeline:
                    pipeline = p
                    break
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve host data."))

        if pipeline is None:
            exceptions.handle(self.request,
                              _("Unable to retrieve host data."))

        return {'pipeline_name': pipeline.name,
                'compress': pipeline.compress,
                'max_bytes': pipeline.max_bytes,
                'backup_count': pipeline.backup_count,
                'location': pipeline.location,
                'enabled': pipeline.enabled}
