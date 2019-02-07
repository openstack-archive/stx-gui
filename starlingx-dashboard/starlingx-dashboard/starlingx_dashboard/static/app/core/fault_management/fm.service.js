/**
 *  Copyright (c) 2018-2019 Wind River Systems, Inc.
 *
 *  SPDX-License-Identifier: Apache-2.0
 *
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.fm', FmAPI);

  FmAPI.$inject = [
    '$q',
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service',
    '$http'
  ];

  function FmAPI($q, apiService, toastService, $http) {
    var service = {
      getAlarmSummary: getAlarmSummary,
      getAlarms: getAlarms,
      getAlarm: getAlarm,
      getEvents: getEvents,
      getEvent: getEvent,
      getEventsSuppression: getEventsSuppression,
      updateEventSuppression: updateEventSuppression
    };

    $http.defaults.xsrfCookieName = 'platformcsrftoken';

    return service;

    ///////////////////////////////
    // Alarms

    function getAlarmSummary() {
      return apiService.get('/api/fm/alarm_summary/')
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve alarm summary."));
        });
    }

    function getAlarms() {
      var results = apiService.get('/api/fm/alarm_list/')
      return results
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve alarms."));
        });
    }

    function getAlarm(uuid) {
      var results =  apiService.get('/api/fm/alarm_get/' + uuid)
      return results
        .error(function() {
          var msg = gettext("Unable to retrieve alarm with uuid: %(uuid)s.");
          toastService.add('error', interpolate(msg, {uuid: uuid}, true));
        });
    }

    ///////////////////////////////
    // Events

    function getEvents() {
      var results = apiService.get('/api/fm/event_log_list/')
      return results
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve events."));
        });
    }

    function getEvent(uuid) {
      var results =  apiService.get('/api/fm/event_log_get/' + uuid)
      return results
        .error(function() {
          var msg = gettext("Unable to retrieve event with uuid: %(uuid)s.");
          toastService.add('error', interpolate(msg, {uuid: uuid}, true));
        });
    }

    ///////////////////////////////
    // Events Suppression

    function getEventsSuppression(include_unsuppressed) {
      var query_string = '/api/fm/events_suppression_list/'
      if (include_unsuppressed) {
        query_string = query_string + '?include_unsuppressed'
      }

      var results = apiService.get(query_string);

      return results
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve events suppression."));
        });
    }

    function updateEventSuppression(uuid, params) {
      var results = apiService.patch('/api/fm/event_suppression/' + uuid, params)
      // Errors are expected to be processed by the caller, just return
      return results;
    }


  }
}());
