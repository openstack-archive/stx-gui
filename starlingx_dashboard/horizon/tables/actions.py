#
# Copyright (c) 2018 Intel Corporation
#
# SPDX-License-Identifier: Apache-2.0
#

from collections import OrderedDict

from django.conf import settings
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon.tables.actions import BaseAction
from horizon.tables import FilterAction

DEFAULT_TABLE_LIMITS = [10, 20, 50, 100, 500, 1000]


class FixedWithQueryFilter(FilterAction):
    """A FilterAction that visually renders like a combination
       FixedFilterAction and a FilterAction of type "query.

       Before extracting data from the filter, always ensure to first call
       the method updateFromRequestDataToSession(..) which will copy current
       request data to the session

       Use get_filter_string(self, request) method to extract the current
       filter string

       Use get_filter_field(self,request) method to extract the current
       "choice" value
    """
    def __init__(self, **kwargs):
        super(FixedWithQueryFilter, self).__init__(**kwargs)
        self.filter_type = "fixedwithquery"
        self.filter_choices = []
        self.default_value = ''
        self.grouped_choices = []
        self.disabled_choices = []

    def _get_fieldFromGETorPOSTorSESSION(self, request, param_name):
        """Utility method for getting 'named" data (param_name) from either
           GET/POST or Session .
           IMPORTANT NOTE:  Has the side-effect of storing the data into
                            the session
          TODO:  In the future, this method should really live in some
                 utility module.

        :param request:
        :param param_name:
        :return: value of data referenced by param_name
        """
        the_field = None

        if param_name in request.GET:
            the_field = request.GET.get(param_name, '')

        if the_field is None and param_name in request.POST:
            the_field = request.POST.get(param_name, '')

        if the_field is None and param_name in request.session:
            the_field = request.session.get(param_name, '')

        if the_field is not None:
            request.session[param_name] = the_field

        return the_field

    def get_filter_field(self, request):
        param_name = '%s_field' % self.get_param_name()
        filter_field = self._get_fieldFromGETorPOSTorSESSION(request,
                                                             param_name)
        self.filter_field = filter_field \
            if filter_field \
            else self.default_value
        return filter_field

    def get_filter_string(self, request):
        param_name = self.get_param_name()
        filter_string = self._get_fieldFromGETorPOSTorSESSION(request,
                                                              param_name)
        self.filter_string = filter_string if filter_string else ''
        self.build_grouped_choices()

        return filter_string

    def updateFromRequestDataToSession(self, request):
        # The desired side-effect of calling the following 2 functions
        # will update the filter field and filter string into
        # the session so that they are 'remembered' across requests
        self.get_filter_field(request)
        self.get_filter_string(request)

    def set_disabled_filter_field_for_group(self, grpNo, disabled_status):
        self.disabled_choices[grpNo] = disabled_status

    def get_filter_field_for_group(self, grpNo):
        splitted = self.filter_field.split("|")
        if len(splitted) <= grpNo:
            raise Exception("get_filter_field_for_group: grpNo out of \
                             range! grpNo={}".format(grpNo))
        value = splitted[grpNo]
        if not value:
            value = self.default_value.split("|")[grpNo]
        return value

    def build_grouped_choices(self):
        grps = []
        grpNo = 0

        for choices_in_group in self.filter_choices:
            currentGrpValue = self.get_filter_field_for_group(grpNo)
            disable_status = self.disabled_choices[grpNo]

            grps.append(
                {
                    "grpNo": grpNo,
                    "filter_choices": choices_in_group,
                    "value": currentGrpValue,
                    "disabled": disable_status
                }
            )
            grpNo = grpNo + 1

        self.grouped_choices = grps

        return grps


class LimitAction(BaseAction):
    """A base class representing a count limit action for a table.

    .. attribute:: name

        The short name or "slug" representing this action. Defaults to
        ``"limit"``.

    .. attribute:: limits

        A set of table entry limits. Default: ``"settings.TABLE_LIMITS"``.

    .. attribute:: limit_format

        A default format sting used do format the verbose
        name of each limit count.
        Default: ``"%(count)s %(name)s"``.

    .. attribute:: verbose_name

        A descriptive entity name to be used . Default: ``"Entries"``.
    """

    # class attribute name is used for ordering of Actions in table
    name = "limit"
    verbose_name = _("Entries")
    limit_format = _("%(count)s %(name)s")
    limits = set(getattr(settings, 'TABLE_LIMITS', DEFAULT_TABLE_LIMITS))

    def __init__(self, **kwargs):
        super(LimitAction, self).__init__(**kwargs)
        self.name = kwargs.get('name', self.name)
        self.limits = kwargs.get('limits', self.limits)
        self.limit_format = kwargs.get('limit_format', self.limit_format)
        self.verbose_name = kwargs.get('verbose_name', self.verbose_name)

    def get_param_name(self):
        """Returns the limit parameter name for this table action."""
        return self.table._meta.limit_param

    def get_default_classes(self):
        classes = super(LimitAction, self).get_default_classes()
        classes += ("btn", "btn-default", "btn-sm",
                    "btn-limit", "dropdown-toggle")
        return classes

    def get_limit_display(self):
        """Default formatter for each limit entry."""
        count = self.table.get_limit_count()
        return self.get_limit_name(count)

    def get_limit_name(self, count):
        """Default formatter for each limit entry."""
        if count is None:
            return "Default Limit"
        return str(self.limit_format % {'count': count,
                                        'name': self.verbose_name})

    def get_limit_count(self):
        """Return the current table limit for tables that support paging."""
        count = self.table.get_limit_count()
        return count

    def get_limits(self):
        """"Return the set of limits supported by the action."""
        limits = {}
        for count in self.limits:
            limits[count] = self.get_limit_name(count)
        return OrderedDict(sorted(limits.items(), key=lambda limit: limit[0]))
