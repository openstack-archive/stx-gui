#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.core import validators

from horizon.forms import IntegerField


class DynamicIntegerField(IntegerField):
    """A subclass of ``IntegerField``.

    A subclass of ``IntegerField`` with additional properties that make
    dynamically updating its range easier.
    """
    def set_max_value(self, max_value):
        if max_value is not None:
            for v in self.validators:
                if isinstance(v, validators.MaxValueValidator):
                    self.validators.remove(v)

            self.max_value = max_value
            self.validators.append(validators.MaxValueValidator(max_value))
            self.widget_attrs(self.widget)
            self.widget.attrs['max'] = self.max_value

    def set_min_value(self, min_value):
        if min_value is not None:
            for v in self.validators:
                if isinstance(v, validators.MinValueValidator):
                    self.validators.remove(v)

            self.min_value = min_value
            self.validators.append(validators.MinValueValidator(min_value))
            self.widget_attrs(self.widget)
            self.widget.attrs['min'] = self.min_value
