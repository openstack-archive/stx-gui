#
# Copyright (c) 2013-2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.system_config.address_pools import \
    tables as address_pool_tables
from starlingx_dashboard.dashboards.admin.system_config \
    import tables as toplevel_tables


LOG = logging.getLogger(__name__)


class SystemsTab(tabs.TableTab):
    table_classes = (toplevel_tables.SystemsTable, )
    name = _("Systems")
    slug = "systems"
    template_name = ("admin/system_config/_systems.html")

    def get_systems_data(self):
        request = self.request
        systems = []
        try:
            systems = stx_api.sysinv.system_list(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve systems list.'))
        return systems


class AddressPoolsTab(tabs.TableTab):
    table_classes = (address_pool_tables.AddressPoolsTable,)
    name = _("Address Pools")
    slug = "address_pools"
    template_name = ("horizon/common/_detail_table.html")

    def get_address_pools_data(self):
        request = self.request
        pools = []
        try:
            pools = stx_api.sysinv.address_pool_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve address pool list.'))

        return pools


class cDNSTab(tabs.TableTab):
    table_classes = (toplevel_tables.cDNSTable, )
    name = _("DNS")
    slug = "cdns_table"
    template_name = ("admin/system_config/_cdns_table.html")

    def get_cdns_table_data(self):
        request = self.request
        data = []

        try:
            dns_data = {'uuid': ' ',
                        'nameserver_1': ' ',
                        'nameserver_2': ' ',
                        'nameserver_3': ' '}

            dns_list = stx_api.sysinv.dns_list(request)
            if dns_list:
                dns = dns_list[0]

                dns_data['uuid'] = dns.uuid
                if dns.nameservers:
                    servers = dns.nameservers.split(",")
                    for index, server in enumerate(servers):
                        dns_data['nameserver_%s' % (index + 1)] = server

            data.append(type('DNS', (object,), dns_data)())

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve dns list.'))

        return data


class cNTPTab(tabs.TableTab):
    table_classes = (toplevel_tables.cNTPTable, )
    name = _("NTP")
    slug = "cntp_table"
    template_name = ("admin/system_config/_cntp_table.html")

    def get_cntp_table_data(self):
        request = self.request
        data = []

        try:
            ntp_data = {'uuid': ' ',
                        'enabled': False,
                        'ntpserver_1': ' ',
                        'ntpserver_2': ' ',
                        'ntpserver_3': ' '}

            ntp_list = stx_api.sysinv.ntp_list(request)
            if ntp_list:
                ntp = ntp_list[0]

                ntp_data['uuid'] = ntp.uuid
                ntp_data['enabled'] = ntp.enabled
                if ntp.ntpservers:
                    servers = ntp.ntpservers.split(",")
                    for index, server in enumerate(servers):
                        ntp_data['ntpserver_%s' % (index + 1)] = server

            data.append(type('NTP', (object,), ntp_data)())

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve ntp list.'))

        return data


class cPTPTab(tabs.TableTab):
    table_classes = (toplevel_tables.cPTPTable, )
    name = _("PTP")
    slug = "cptp_table"
    template_name = ("admin/system_config/_cptp_table.html")

    def get_cptp_table_data(self):
        request = self.request
        data = []

        try:
            ptp_data = {'uuid': ' ',
                        'enabled': False,
                        'mode': ' ',
                        'transport': ' ',
                        'mechanism': ' '}

            ptp_list = stx_api.sysinv.ptp_list(request)
            if ptp_list:
                ptp = ptp_list[0]

                ptp_data['uuid'] = ptp.uuid
                ptp_data['enabled'] = ptp.enabled
                ptp_data['mode'] = ptp.mode
                ptp_data['transport'] = ptp.transport
                ptp_data['mechanism'] = ptp.mechanism

            data.append(type('PTP', (object,), ptp_data)())

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve ptp list.'))

        return data


class cEXTOAMTab(tabs.TableTab):
    table_classes = (toplevel_tables.cOAMTable, )
    name = _("OAM IP")
    slug = "coam_able"
    template_name = ("admin/system_config/_coam_table.html")

    def get_coam_table_data(self):
        request = self.request
        oam_list = []

        try:
            oam_list = stx_api.sysinv.extoam_list(request)

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve oam list.'))
        # Sort hosts by hostname
        # hosts.sort(key=lambda f: (f.personality, f.hostname))
        return oam_list


class iStorageTab(tabs.TableTab):
    table_classes = (toplevel_tables.iStorageTable, )
    name = _("Controller Filesystem")
    slug = "storage_table"
    template_name = ("admin/system_config/_storage_table.html")

    def get_storage_table_data(self):
        request = self.request
        storage_list = []

        try:
            storage_list = stx_api.sysinv.controllerfs_list(request)

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve filesystem list.'))

        return storage_list


class iStoragePoolsTab(tabs.TableTab):
    table_classes = (toplevel_tables.iStoragePoolsTable, )
    name = _("Ceph Storage Pools")
    slug = "storage_pools_table"
    template_name = ("admin/system_config/_storage_pools_table.html")

    def get_storage_pools_table_data(self):
        request = self.request
        storage_list = []

        try:
            storage_list = stx_api.sysinv.storagepool_list(request)

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve storage pool list.'))

        return storage_list

    def allowed(self, request):
        """Only display the Tab if we have a ceph based setup"""
        try:
            cinder_backend = stx_api.sysinv.get_cinder_backend(request)
            if stx_api.sysinv.CINDER_BACKEND_CEPH in cinder_backend:
                return True
        except Exception:
            pass
        return False


class SDNControllerTab(tabs.TableTab):
    table_classes = (toplevel_tables.SDNControllerTable, )
    name = _("SDN Controllers")
    slug = "sdn_controller_table"
    template_name = ("admin/system_config/_sdn_controller_table.html")

    def get_sdn_controller_table_data(self):
        request = self.request
        controllers = []

        try:
            controllers = stx_api.sysinv.sdn_controller_list(request)

        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve SDN Controller list.'))

        return controllers

    def allowed(self, request):
        """Only display the Tab if we have a SDN based setup"""
        try:
            sdn_enabled = stx_api.sysinv.get_sdn_enabled(request)
            return sdn_enabled
        except Exception:
            return False


class CeilometerConfigTab(tabs.TableTab):
    table_classes = (toplevel_tables.CeilometerPipelinesTable,)
    name = _("Pipelines")
    slug = "ceilometer_config"
    template_name = ("horizon/common/_detail_table.html")

    def get_ceilometer_pipelines_data(self):
        request = self.tab_group.request
        pipelines = []
        try:
            pipelines = api.ceilometer.pipeline_list(request)
        except Exception:
            msg = _('Unable to retrieve ceilometer pipeline data.')
            exceptions.handle(request, msg)
        return pipelines

    def allowed(self, request):
        if request.user.services_region == 'SystemController':
            return False
        return stx_api.base.is_stx_region(request)


class ConfigTabs(tabs.TabGroup):
    slug = "system_config_tab"
    tabs = (SystemsTab, AddressPoolsTab, cDNSTab, cNTPTab, cPTPTab,
            cEXTOAMTab, iStorageTab, iStoragePoolsTab, SDNControllerTab,
            CeilometerConfigTab)
    sticky = True
