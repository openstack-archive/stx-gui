# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.api import base
from openstack_dashboard.api import ceph
from openstack_dashboard.api import sysinv
from openstack_dashboard.dashboards.admin.storage_overview import constants
from openstack_dashboard.dashboards.admin.storage_overview import tables

LOG = logging.getLogger(__name__)


class StorageServicesTab(tabs.TableTab):
    table_classes = (tables.MonitorsTable, tables.OSDsTable,)
    name = _("Services")
    slug = "storage_services"
    template_name = constants.STORAGE_SERVICE_DETAIL_TEMPLATE_NAME

    def get_monitors_data(self):
        try:
            return ceph.monitor_list()
        except Exception as e:
            LOG.error(e)
            return

    def get_osds_data(self):
        try:
            return ceph.osd_list()
        except Exception as e:
            LOG.error(e)
            return

    def get_cluster_data(self):
        try:
            return ceph.cluster_get()
        except Exception as e:
            LOG.error(e)
            return

    def get_storage_data(self):
        try:
            return ceph.storage_get()
        except Exception as e:
            LOG.error(e)
            return

    def get_context_data(self, request):
        try:
            context = super(StorageServicesTab, self).get_context_data(request)
            context['monitors'] = self.get_monitors_data()
            context['osds'] = self.get_osds_data()
            context['cluster'] = self.get_cluster_data()
            context['storage'] = self.get_storage_data()
            return context
        except Exception as e:
            LOG.error(e)
            msg = _('Unable to get storage services list.')
            exceptions.check_message(["Connection", "refused"], msg)
            return

    def allowed(self, request):
        return base.is_TiS_region(request)


class StorageUsageTab(tabs.TableTab):
    table_classes = (tables.UsageTable,)
    name = _("Usage")
    slug = "usage"
    template_name = constants.STORAGE_USAGE_TEMPLATE_NAME

    def get_usage_data(self):
        try:
            return sysinv.storage_usage_list(self.request)
        except Exception:
            LOG.error("Exception requesting storage usage information")

        return []


class StorageOverviewTabs(tabs.TabGroup):
    slug = "storage_overview"
    tabs = (StorageServicesTab, StorageUsageTab)
    sticky = True
