/**
 *  Copyright (c) 2018 Wind River Systems, Inc.
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
      getAlarmSummary: getAlarmSummary
    };

    var csrf_token = $('input[name=csrfmiddlewaretoken]').val();
    $http.defaults.headers.post['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.common['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.put['X-CSRFToken'] = csrf_token;

    return service;


    ///////////////////
    // Alarm Summary //
    ///////////////////

    function getAlarmSummary() {
      return apiService.get('/api/fm/alarm_summary/')
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve the System Controller's alarm summary."));
        });
    }

  }
}());
