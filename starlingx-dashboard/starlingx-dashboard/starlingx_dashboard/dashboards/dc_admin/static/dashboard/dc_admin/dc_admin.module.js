/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function() {
  'use strict';

  /**
   * @ngdoc horizon.dashboard.dc_admin
   * @ngModule
   *
   * @description
   * Dashboard module to host distributed cloud admin panels.
   */
  angular
    .module('horizon.dashboard.dc_admin', [
      'horizon.dashboard.dc_admin.cloud_overview',
      'ngRoute'
    ]);
})();
