/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function() {
  'use strict';

  /**
   * @ngdoc horizon.dashboard.dc_admin.cloud_overview
   * @ngModule
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display the cloud overview panel.
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview', [])
    .config(config);

  config.$inject = [
    '$provide',
    '$windowProvider'
  ];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/dc_admin/';
    $provide.constant('horizon.dashboard.dc_admin.basePath', path);
  }

})();
