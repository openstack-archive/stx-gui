#
# Copyright (c) 2015-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
from six.moves import configparser


# Configuration Global used by other modules to get access to the configuration
# specified in the config file.
CONFSS = dict()


class ConfigSS(configparser.ConfigParser):
    """Override ConfigParser class to add dictionary functionality. """
    def as_dict(self):
        d = dict(self._sections)
        for key in d:
            d[key] = dict(self._defaults, **d[key])
            d[key].pop('__name__', None)
        return d


def load(config_file):
    """Load the configuration file into a global CONFSS variable. """
    global CONFSS  # noqa pylint: disable=global-statement

    config = ConfigSS()
    config.read(config_file)
    if not CONFSS:
        CONFSS = config.as_dict()
    else:
        CONFSS.update(config.as_dict())
