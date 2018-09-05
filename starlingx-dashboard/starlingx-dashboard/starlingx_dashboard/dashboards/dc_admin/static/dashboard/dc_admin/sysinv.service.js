/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.sysinv', SysinvAPI);

  SysinvAPI.$inject = [
    '$q',
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service',
    '$http'
  ];

  function SysinvAPI($q, apiService, toastService, $http) {
    var service = {
      getSystem: getSystem
    };

    var csrf_token = $('input[name=csrfmiddlewaretoken]').val();
    $http.defaults.headers.post['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.common['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.put['X-CSRFToken'] = csrf_token;

    return service;


    ////////////
    // System //
    ////////////

    function getSystem() {
      return apiService.get('/api/sysinv/system/')
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext("Unable to retrieve the System Controller's system."));
        });
    }

  }
}());
