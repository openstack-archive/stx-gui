#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django import template

register = template.Library()


@register.filter(name="get_value")
def get_value(dictionary, key):
    return dictionary.get(key)
