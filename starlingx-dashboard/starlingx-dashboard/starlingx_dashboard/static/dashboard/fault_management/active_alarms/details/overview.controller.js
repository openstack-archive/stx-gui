/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * Copyright (c) 2019 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
  "use strict";

  angular
    .module('horizon.dashboard.fault_management.active_alarms')
    .controller('horizon.dashboard.fault_management.active_alarms.OverviewController', controller);

  controller.$inject = [
    '$scope'
  ];

  function controller(
    $scope
  ) {
    var ctrl = this;
    ctrl.alarm = {};

    $scope.context.loadPromise.then(onGetAlarm);

    function onGetAlarm(item) {
      ctrl.alarm = item.data;
    }
  }
})();
