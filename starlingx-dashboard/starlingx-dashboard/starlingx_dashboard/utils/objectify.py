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
#  Copyright (c) 2019 Wind River Systems, Inc.
#
#  SPDX-License-Identifier: Apache-2.0
#


from functools import wraps  # noqa


def objectify(func):
    """Mimic an object given a dictionary.

    Given a dictionary, create an object and make sure that each of its
    keys are accessible via attributes.
    Ignore everything if the given value is not a dictionary.
    :param value: A dictionary or another kind of object.
    :returns: Either the created object or the given value.

    >>> obj = {'old_key': 'old_value'}
    >>> oobj = objectify(obj)
    >>> oobj['new_key'] = 'new_value'
    >>> print oobj['old_key'], oobj['new_key'], oobj.old_key, oobj.new_key

    >>> @objectify
    ... def func():
         ...     return {'old_key': 'old_value'}
    >>> obj = func()
    >>> obj['new_key'] = 'new_value'
    >>> print obj['old_key'], obj['new_key'], obj.old_key, obj.new_key


    """

    def create_object(value):
        if isinstance(value, dict):
            # Build a simple generic object.
            class Object(dict):
                def __setitem__(self, key, val):
                    setattr(self, key, val)
                    return super(Object, self).__setitem__(key, val)

            # Create that simple generic object.
            ret_obj = Object()
            # Assign the attributes given the dictionary keys.
            for key, val in value.iteritems():
                ret_obj[key] = val
                setattr(ret_obj, key, val)
            return ret_obj
        else:
            return value

    # If func is a function, wrap around and act like a decorator.
    if hasattr(func, '__call__'):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function for the decorator.

            :returns: The return value of the decorated function.

            """
            value = func(*args, **kwargs)
            return create_object(value)

        return wrapper

    # Else just try to objectify the value given.
    else:
        return create_object(func)
