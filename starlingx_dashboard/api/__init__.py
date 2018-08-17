#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Copyright (c) 2017 Wind River Systems, Inc.
#

#from cgcs_dashboard.api import dc_manager
#from cgcs_dashboard.api import iservice
#from cgcs_dashboard.api import sysinv
from starlingx_dashboard.api import base
from starlingx_dashboard.api import dc_manager
from starlingx_dashboard.api import sysinv
from starlingx_dashboard.api import vim
from starlingx_dashboard.api import patch

# TODO (ediardo): cleanup the imports below
__all__ = [
    "base",
    "dc_manager",
    "sysinv",
    "vim",
]
