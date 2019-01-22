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
  "use strict";

  angular.module('horizon.dashboard.fault_management.events_suppression')
    .factory('horizon.dashboard.fault_management.events_suppression.service',
      service);

  service.$inject = [
    '$filter',
    'horizon.app.core.detailRoute',
    'horizon.app.core.openstack-service-api.fm'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.fault_management.events_suppression.service
   *
   * @description
   * This service provides functions that are used through the Events Suppression
   * features.  These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function service($filter, detailRoute, api) {
    return {
      getPromise: getPromise
    };

    function getPromise(params) {
      var include_unsuppressed = true;
      return api.getEventsSuppression(include_unsuppressed).then(modifyResponse);
    }

    function modifyResponse(response) {
      return {data: {items: response.data.items.map(modifyItem)}};

      function modifyItem(item) {

        // This enables the items to be updated on the view
        item.trackBy = [
          item.uuid,
          item.suppression_status,
          item.alarm_id
        ].join('/');

        if (item.suppression_status == 'suppressed') {
          item.is_suppressed = true;
        }
        else {
          item.is_suppressed = false;
        }

        return item;
      }
    }
  }
})();

