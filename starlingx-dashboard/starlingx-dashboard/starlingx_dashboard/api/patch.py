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
# Copyright (c) 2014 Wind River Systems, Inc.
#

import logging

from six.moves.urllib.parse import urlparse

import requests

from openstack_dashboard.api import base
from requests_toolbelt import MultipartEncoder


LOG = logging.getLogger(__name__)


class Client(object):
    def __init__(self, version, url, token_id):
        self.version = version
        self.url = url
        self.token_id = token_id

    def _make_request(self, token_id, method, api_version, api_cmd,
                      encoder=None):
        url = self.url
        url += "/%s/%s" % (api_version, api_cmd)
        # url += "/patch/%s" % (api_cmd)

        headers = {"X-Auth-Token": token_id,
                   "Accept": "application/json"}

        if method == 'GET':
            req = requests.get(url, headers=headers)
        elif method == 'POST':
            if encoder is not None:
                headers['Content-Type'] = encoder.content_type
            req = requests.post(url, headers=headers, data=encoder)

        resp = req.json()

        return resp

    def get_patches(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "query?show=all")

    def show_patch(self, patch_id):
        return self._make_request(self.token_id, "GET", self.version,
                                  "show/%s" % patch_id)

    def get_hosts(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "query_hosts")

    def upload(self, patchfile):
        encoder = MultipartEncoder(fields=patchfile)
        return self._make_request(self.token_id, "POST", self.version,
                                  "upload", encoder=encoder)

    def apply(self, patch_ids):
        patches = "/".join(patch_ids)
        return self._make_request(self.token_id, "POST", self.version,
                                  "apply/%s" % patches)

    def remove(self, patch_ids):
        patches = "/".join(patch_ids)
        return self._make_request(self.token_id, "POST", self.version,
                                  "remove/%s" % patches)

    def delete(self, patch_ids):
        patches = "/".join(patch_ids)
        return self._make_request(self.token_id, "POST", self.version,
                                  "delete/%s" % patches)

    def host_install(self, host):
        return self._make_request(self.token_id, "POST", self.version,
                                  "host_install/%s" % host)

    def host_install_async(self, host):
        return self._make_request(self.token_id, "POST", self.version,
                                  "host_install_async/%s" % host)


def _patching_client(request):
    o = urlparse(base.url_for(request, 'patching'))
    url = "://".join((o.scheme, o.netloc))
    return Client("v1", url, token_id=request.user.token.id)


class Patch(object):
    _attrs = ['status',
              'sw_version',
              'install_instructions',
              'description',
              'warnings',
              'summary',
              'repostate',
              'patchstate',
              'requires',
              'unremovable',
              'reboot_required']


class Host(object):
    _attrs = ['hostname',
              'installed',
              'ip',
              'missing_pkgs',
              'nodetype',
              'patch_current',
              'patch_failed',
              'requires_reboot',
              'secs_since_ack',
              'stale_details',
              'to_remove',
              'sw_version',
              'state',
              'allow_insvc_patching',
              'interim_state']


def get_patches(request):
    patches = []
    try:
        info = _patching_client(request).get_patches()
    except Exception:
        return patches

    if info:
        for p in info['pd'].iteritems():
            patch = Patch()

            for a in patch._attrs:
                if a == 'requires':
                    patch.requires = [str(rp) for rp in p[1][a]]
                    continue

                if a == 'reboot_required':
                    # Default to "N"
                    setattr(patch, a, str(p[1].get(a, "N")))
                    continue

                # Must handle older patches that have metadata that is missing
                # newer attributes. Default missing attributes to "".
                setattr(patch, a, str(p[1].get(a, "")))
            patch.patch_id = str(p[0])

            patches.append(patch)
    return patches


def get_patch(request, patch_id):
    patches = get_patches(request)
    patch = next((p for p in patches if p.patch_id == patch_id), None)

    # add on patch contents
    data = _patching_client(request).show_patch(patch_id)
    patch.contents = [str(pkg) for pkg in data['contents'][patch_id]]

    return patch


def get_hosts(request):
    hosts = []
    try:
        info = _patching_client(request).get_hosts()
    except Exception:
        return hosts

    if info:
        for h in info['data']:
            host = Host()
            for a in host._attrs:
                setattr(host, a, h[a])
            hosts.append(host)
    return hosts


def get_host(request, hostname):
    phosts = get_hosts(request)
    return next((phost for phost in phosts if phost.hostname == hostname),
                None)


def get_message(data):
    LOG.info("RESPONSE: %s", data)
    if not data or ('error' in data and data["error"] != ""):
        raise ValueError(data["error"] or "Invalid patch file")
    if 'warning' in data and data["warning"] != "":
        return data["warning"]
    if 'info' in data and data["info"] != "":
        return data["info"]
    return ""


def upload_patch(request, patchfile, name):
    _file = {'file': (name, patchfile,)}
    resp = _patching_client(request).upload(_file)
    return get_message(resp)


def patch_apply_req(request, patch_id):
    resp = _patching_client(request).apply(patch_id)
    return get_message(resp)


def patch_remove_req(request, patch_id):
    resp = _patching_client(request).remove(patch_id)
    return get_message(resp)


def patch_delete_req(request, patch_id):
    resp = _patching_client(request).delete(patch_id)
    return get_message(resp)


def host_install(request, hostname):
    resp = _patching_client(request).host_install(hostname)
    return get_message(resp)


def host_install_async(request, hostname):
    resp = _patching_client(request).host_install_async(hostname)
    return get_message(resp)
