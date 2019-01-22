/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
/**
 *  Copyright (c) 2019 Wind River Systems, Inc.
 *
 *  SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.dashboard.fault_management
   * @description
   * Dashboard module to host various platform panels.
   */
  // fixme: if ngRoute and $routeProvider are unnecessary, remove them
  /* eslint-disable no-unused-vars */
  angular
    .module('horizon.dashboard.fault_management', [
      'horizon.dashboard.fault_management.active_alarms',
      'horizon.dashboard.fault_management.events',
      'horizon.dashboard.fault_management.events_suppression',
      'ngRoute'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider', '$routeProvider'];

  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/fault_management/';
    $provide.constant('horizon.dashboard.fault_management.basePath', path);
  }
  /* eslint-disable no-unused-vars */
})();
