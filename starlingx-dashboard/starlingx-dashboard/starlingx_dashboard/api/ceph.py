#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2013-2014 Wind River Systems, Inc.
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

from __future__ import absolute_import

import logging

from cephclient import wrapper

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


# TODO(wrs) this can be instancized once, or will need to pass request per
# user?
def cephwrapper():
    return wrapper.CephWrapper()


class Monitor(base.APIDictWrapper):
    __attrs = ['host', 'rank']

    def __init__(self, apidict):
        super(Monitor, self).__init__(apidict)


class OSD(base.APIDictWrapper):
    __attrs = ['id', 'name', 'host', 'status']

    def __init__(self, apidict):
        super(OSD, self).__init__(apidict)


class Cluster(base.APIDictWrapper):
    _attrs = ['fsid', 'status', 'health', 'detail']

    def __init__(self, apidict):
        super(Cluster, self).__init__(apidict)


class Storage(base.APIDictWrapper):
    _attrs = ['total', 'used', 'available',
              'writes_per_sec', 'operations_per_sec']

    def __init__(self, apidict):
        super(Storage, self).__init__(apidict)


def _Bytes_to_MiB(value_B):
    return (value_B / (1024 * 1024))


def _Bytes_to_GiB(value_B):
    return (value_B / (1024 * 1024 * 1024))


def cluster_get():
    # the json response doesn't give all the information
    response, text_body = cephwrapper().health(body='text')
    # ceph is not up, raise exception
    if not response.ok:
        response.raise_for_status()
    health_info = text_body.split(' ', 1)

    # if health is ok, there will be no details so just show HEALTH_OK
    if len(health_info) > 1:
        detail = health_info[1]
    else:
        detail = health_info[0]

    response, cluster_uuid = cephwrapper().fsid(body='text')
    if not response.ok:
        cluster_uuid = None

    cluster = {
        'fsid': cluster_uuid,
        'health': health_info[0],
        'detail': detail,
    }

    return Cluster(cluster)


def storage_get():
    # # Space info
    response, body = cephwrapper().df(body='json')
    # return no space info
    if not response.ok:
        response.raise_for_status()
    stats = body['output']['stats']
    space = {
        'total': _Bytes_to_GiB(stats['total_bytes']),
        'used': _Bytes_to_MiB(stats['total_used_bytes']),
        'available': _Bytes_to_GiB(stats['total_avail_bytes']),
    }

    # # I/O info
    response, body = cephwrapper().osd_pool_stats(body='json',
                                                  name='cinder-volumes')
    if not response.ok:
        response.raise_for_status()
    stats = body['output'][0]['client_io_rate']
    # not showing reads/sec at the moment
    # reads_per_sec = stats['read_bytes_sec'] if (
    #    'read_bytes_sec' in stats) else 0
    writes_per_sec = stats['write_bytes_sec'] if (
        'write_bytes_sec' in stats) else 0
    operations_per_sec = stats['op_per_sec'] if ('op_per_sec' in stats) else 0
    io = {
        'writes_per_sec': writes_per_sec / 1024,
        'operations_per_sec': operations_per_sec
    }

    storage = {}
    storage.update(space)
    storage.update(io)

    return Storage(storage)


def _get_quorum_status(mon, quorums):
    if mon['rank'] in quorums:
        status = 'up'
    else:
        status = 'down'
    return status


def monitor_list():
    response, body = cephwrapper().mon_dump(body='json')
    # return no monitors info
    if not response.ok:
        response.raise_for_status()

    quorums = body['output']['quorum']

    mons = []
    for mon in body['output']['mons']:
        status = _get_quorum_status(mon, quorums)
        mons.append(
            {'host': mon['name'], 'rank': mon['rank'], 'status': status})
    return [Monitor(m) for m in mons]


def osd_list():
    # would use osd_find, but it doesn't give osd's name
    response, tree = cephwrapper().osd_tree(body='json')
    if not response.ok:
        response.raise_for_status()

    osds = []
    for node in tree['output']['nodes']:
        # found osd
        if node['type'] == 'osd':
            osd = {}
            osd['id'] = node['id']
            osd['name'] = node['name']
            osd['status'] = node['status']

            # check if osd belongs to host
            response, body = cephwrapper().osd_find(body='json', id=osd['id'])
            if response.ok and 'host' in body['output']['crush_location']:
                osd['host'] = body['output']['crush_location']['host']
            # else dont set hostname

            osds.append(osd)

    return [OSD(o) for o in osds]
