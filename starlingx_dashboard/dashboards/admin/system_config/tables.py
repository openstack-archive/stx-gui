#
# Copyright (c) 2013-2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import logging

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from openstack_dashboard import api


LOG = logging.getLogger(__name__)

CONFIG_STATE_CREATED = 'created'
CONFIG_STATE_MODIFIED = 'modified'
CONFIG_STATE_APPLYING = 'applying'
CONFIG_STATE_APPLIED = 'applied'
CONFIG_STATE_FAILED = 'failed'
CONFIG_STATE_ABORTED = 'aborted'

STATE_DISPLAY_CHOICES = (
    (CONFIG_STATE_CREATED, _("Created")),
    (CONFIG_STATE_MODIFIED, _("Modified")),
    (CONFIG_STATE_APPLYING, _("Applying")),
    (CONFIG_STATE_APPLIED, _("Applied")),
    (CONFIG_STATE_FAILED, _("Failed")),
    (CONFIG_STATE_ABORTED, _("Aborted")),
)


def get_short_software_version(system):
    return system.get_short_software_version()


class EditSystem(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit System")
    url = "horizon:admin:system_config:update_system"
    classes = ("ajax-modal", "btn-edit")


class SystemsTable(tables.DataTable):
    system_name = tables.Column('name',
                                verbose_name=_('Name'))

    system_type = tables.Column('system_type',
                                verbose_name=_('System Type'))

    system_mode = tables.Column('system_mode',
                                verbose_name=_('System Mode'))

    system_desc = tables.Column('description',
                                verbose_name=_("Description"))

    system_version = tables.Column(get_short_software_version,
                                   verbose_name=_("Version"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.name

    class Meta(object):
        name = "systems"
        verbose_name = _("Systems")
        multi_select = False
        row_actions = (EditSystem, )


class EditcDNS(tables.LinkAction):
    name = "update_cdns"
    verbose_name = _("Edit DNS")
    url = "horizon:admin:system_config:update_cdns_table"
    classes = ("ajax-modal", "btn-edit")


class EditcNTP(tables.LinkAction):
    name = "update_cntp"
    verbose_name = _("Edit NTP")
    url = "horizon:admin:system_config:update_cntp_table"
    classes = ("ajax-modal", "btn-edit")


class EditcOAM(tables.LinkAction):
    name = "update_coam"
    verbose_name = _("Edit OAM IP")
    url = "horizon:admin:system_config:update_coam_table"
    classes = ("ajax-modal", "btn-edit")


class EditiStorage(tables.LinkAction):
    name = "update_storage"
    verbose_name = _("Edit Filesystem")
    url = "horizon:admin:system_config:update_storage_table"
    classes = ("ajax-modal", "btn-edit")


class EditiStoragePools(tables.LinkAction):
    name = "update_storage_pools"
    verbose_name = _("Edit pool quotas")
    url = "horizon:admin:system_config:update_storage_pools_table"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, storage_ceph):
        return reverse(self.url, args=(storage_ceph.tier_name,))


class UpdateDNSRow(tables.Row):
    ajax = True

    def get_data(self, request, obj_id):
        return api.sysinv.dns_get(request, obj_id)


class cDNSTable(tables.DataTable):
    nameserver_1 = tables.Column(
        "nameserver_1",
        verbose_name=_('DNS Server 1 IP'))

    nameserver_2 = tables.Column(
        "nameserver_2",
        verbose_name=_('DNS Server 2 IP'))

    nameserver_3 = tables.Column(
        "nameserver_3",
        verbose_name=_('DNS Server 3 IP'))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.uuid
        # return datum.cname

    class Meta(object):
        name = "cdns_table"
        verbose_name = _("DNS")
        row_class = UpdateDNSRow
        multi_select = False
        table_actions = (EditcDNS,)


class UpdateNTPRow(tables.Row):
    ajax = True

    def get_data(self, request, obj_id):
        return api.sysinv.ntp_get(request, obj_id)


class cNTPTable(tables.DataTable):
    ntpserver_1 = tables.Column(
        'ntpserver_1',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('NTP Server 1 Address'))

    ntpserver_2 = tables.Column(
        'ntpserver_2',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('NTP Server 2 Address'))

    ntpserver_3 = tables.Column(
        'ntpserver_3',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('NTP Server 3 Address'))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.uuid

    class Meta(object):
        name = "cntp_table"
        verbose_name = _("NTP")
        row_class = UpdateNTPRow
        multi_select = False
        table_actions = (EditcNTP,)


class UpdateOAMRow(tables.Row):
    ajax = True

    def get_data(self, request, obj_id):
        return api.sysinv.extoam_get(request, obj_id)


class cOAMTable(tables.DataTable):
    region_config = tables.Column(
        'region_config',
        verbose_name=_('OAM Region Config'),
        hidden=True)

    oam_subnet = tables.Column(
        'oam_subnet',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('OAM Subnet'))

    oam_floating_ip = tables.Column(
        'oam_floating_ip',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('OAM Floating IP'))

    oam_gateway_ip = tables.Column(
        'oam_gateway_ip',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('OAM Gateway IP'))

    oam_c0_ip = tables.Column(
        'oam_c0_ip',
        # link="horizon:admin:system_config:detail_cdns",
        verbose_name=_('OAM controller-0 IP'))

    oam_c1_ip = tables.Column(
        'oam_c1_ip',
        verbose_name=_('OAM controller-1 IP'))

    # This is optional for non region config
    oam_start_ip = tables.Column(
        'oam_start_ip',
        # hidden=(region_config.transform.strip() == "True"),
        hidden=True,
        verbose_name=_('OAM Start IP'))

    oam_end_ip = tables.Column(
        'oam_end_ip',
        # hidden=(region_config.transform.strip() != "True"),
        hidden=True,
        verbose_name=_('OAM End IP'))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.uuid

    def __init__(self, request, *args, **kwargs):
        super(cOAMTable, self).__init__(request, *args, **kwargs)

        if api.sysinv.is_system_mode_simplex(request):
            self.columns['oam_floating_ip'].verbose_name = _('OAM IP')
            del self.columns['oam_c0_ip']
            del self.columns['oam_c1_ip']

    class Meta(object):
        name = "coam_table"
        verbose_name = _("OAM IP")
        row_class = UpdateOAMRow
        multi_select = False
        table_actions = (EditcOAM,)


class UpdateStorageRow(tables.Row):
    ajax = True

    def get_data(self, request):
        return api.sysinv.storagefs_list(request)


class iStorageTable(tables.DataTable):
    name = tables.Column(
        'name',
        verbose_name=_('Storage Name'))

    size = tables.Column(
        'size',
        verbose_name=_('Size (GiB)'))

    def get_object_id(self, datum):
        return unicode(datum.name)

    def get_object_display(self, datum):
        return

    def __init__(self, request, *args, **kwargs):
        super(iStorageTable, self).__init__(request, *args, **kwargs)

    class Meta(object):
        name = "storage_table"
        verbose_name = _("Controller Filesystem")
        multi_select = False
        table_actions = (EditiStorage,)
        columns = ('name', 'size')


class iStoragePoolsTable(tables.DataTable):
    tier_name = tables.Column(
        'tier_name',
        verbose_name=_('Ceph Storage Tier'))

    cinder_pool_gib = tables.Column(
        'cinder_pool_gib',
        verbose_name=_('Cinder Volume Storage (GiB)'))

    glance_pool_gib = tables.Column(
        'glance_pool_gib',
        verbose_name=_('Glance Image Storage (GiB)'))

    ephemeral_pool_gib = tables.Column(
        'ephemeral_pool_gib',
        verbose_name=_('Nova Ephemeral Disk Storage (GiB)'))

    object_pool_gib = tables.Column(
        'object_pool_gib',
        verbose_name=_('Object Storage (GiB)'))

    total_ceph_space = tables.Column(
        'ceph_total_space_gib',
        verbose_name=_('Ceph total space (GiB)'))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return ("%s" % datum.tier_name)

    class Meta(object):
        name = "storage_pools_table"
        verbose_name = _("Ceph Storage Pools")
        row_class = UpdateStorageRow
        multi_select = False
        row_actions = (EditiStoragePools,)


###########################################################
#                   SDN Controller Tables                 #
###########################################################
class DeleteSDNController(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete SDN Controller",
            u"Delete SDN Controllers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted SDN Controller",
            u"Deleted SDN Controllers",
            count
        )

    def delete(self, request, obj_id):
        try:
            api.sysinv.sdn_controller_delete(request, obj_id)
        except exc.ClientException as ce:
            # Display REST API error on the GUI
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            return False
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            e.handle(request, msg)
            return False


class CreateSDNController(tables.LinkAction):
    name = "create"
    verbose_name = _("Create SDN Controller")
    url = "horizon:admin:system_config:create_sdn_controller_table"
    classes = ("ajax-modal", "btn-create")


class EditSDNController(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit SDN Controller")
    url = "horizon:admin:system_config:update_sdn_controller_table"
    classes = ("ajax-modal", "btn-edit")


class SDNControllerFilterAction(tables.FilterAction):
    def filter(self, table, controllers, filter_string):
        """Naive case-insensitive search."""
        s = filter_string.lower()
        return [controller for controller in controllers
                if s in controller.name.lower()]


class SDNControllerTable(tables.DataTable):
    name = tables.Column("uuid", verbose_name=_("Name"),
                         link="horizon:admin:system_config:"
                              "detail_sdn_controller_table")
    state = tables.Column("state",
                          verbose_name=_("Administrative State"))
    ip_address = tables.Column("ip_address",
                               verbose_name=_("Host"))
    port = tables.Column("port",
                         verbose_name=_("Remote Port"))

    def get_object_id(self, datum):
        return unicode(datum.uuid)

    def get_object_display(self, datum):
        return datum.uuid

    class Meta(object):
        name = "sdn_controller_table"
        verbose_name = _("SDN Controllers")
        table_actions = (CreateSDNController, DeleteSDNController,
                         SDNControllerFilterAction)
        row_actions = (EditSDNController, DeleteSDNController)


###########################################################
#                   Pipeline                              #
###########################################################
class ChangeCeilometerPipeline(tables.LinkAction):
    name = "update_defaults"
    verbose_name = _("Update Settings")
    url = "horizon:admin:system_config:update"
    classes = ("ajax-modal", "btn-edit")

    # def get_link_url(self, pipeline):
    # step = 'update_group_members'
    # #base_url = reverse(self.url, args=[name])
    # param = urlencode({"step": step})
    # return "?".join([base_url, param])


class CeilometerPipelinesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_('Name'))
    location = tables.Column("location", verbose_name=_('Location'))
    max_bytes = tables.Column('max_bytes', verbose_name=_('Max Bytes'))
    backup_count = tables.Column('backup_count',
                                 verbose_name=_('Backup Count'))
    compress = tables.Column('compress', verbose_name=_('Compress'))
    enabled = tables.Column("enabled", verbose_name=_('Enabled'))

    def get_object_id(self, obj):
        return "%s" % (obj.name,)

    class Meta(object):
        name = "ceilometer_pipelines"
        verbose_name = _("Pipelines")
        row_actions = (ChangeCeilometerPipeline, )
        multi_select = False
