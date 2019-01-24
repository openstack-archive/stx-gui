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

  angular.module('horizon.dashboard.fault_management.events')
    .factory('horizon.dashboard.fault_management.events.service',
      service);

  service.$inject = [
    '$filter',
    'horizon.app.core.openstack-service-api.fm',
    '$q',
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.fault_management.events.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.fault_management.events.service
   *
   * @description
   * This service provides functions that are used through the Events
   * features.  These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function service($filter, api, $q, registry, resourceType) {

    var showSuppressColumn = null;

    return {
      getPromise: getPromise,
      suppressColAllowedPromiseFunction: suppressColAllowedPromiseFunction,
      getSuppressionList: getSuppressionList,
      setEventType: setEventType
    };

    function getPromise(params) {
      return api.getEvents(params).then(modifyResponse);
    }

    function modifyResponse(response) {
      return {data: {items: response.data.items.map(modifyItem)}};

      function modifyItem(item) {
        var timestamp = item.updated_at ? item.updated_at : item.created_at;
        item.trackBy = item.uuid + timestamp;

        setEventType(item);

        if (item.suppression_status == 'suppressed') {
          item._suppression_status = 'True';
        }
        else if (item.suppression_status == 'unsuppressed') {
          item._suppression_status = 'False';
        }
        else {
          item._suppression_status = 'None';
        }

        return item;
      }
    }

    function getSuppressionList() {
      var include_unsuppressed = false;
      return api.getEventsSuppression(include_unsuppressed).then(modifyResponseSupp);
    }

    function modifyResponseSupp(response) {
      if (response.data.items.length == 0) {
        showSuppressColumn = false;
      }
      else {
        showSuppressColumn = true;
      }
      return;
    }


    /**
     * @name suppressColAllowedPromiseFunction
     * @description
     * If there are no unsuppressed events then we do not show the Suppression
     * Status column. We also do show the the filter associated with that column.
     */
    function suppressColAllowedPromiseFunction() {

      var filters = registry.getResourceType(resourceType).filterFacets;
      var index = filters.findIndex(obj => obj['id'] === 'suppression_status');

      if (showSuppressColumn === false) {
        if (index >= 0) {
          filters.remove('suppression_status')
        }
        return $q.reject();
      }
      else {
        if (index < 0) {
          filters.append({
            'label': gettext('Suppression Status'),
            'id': 'suppression_status',
            'name': '_suppression_status',
            'singleton': false,
            'options': [
                {label: gettext('suppressed'), key: 'True'},
                {label: gettext('unsuppressed'), key: 'False'},
                {label: gettext('None'), key: 'None'}
              ]
          });
        }
        return $q.resolve();
      }
    }

    ///////////
    // Utils //
    ///////////

    function setEventType(item) {
      if (item.state == "clear" || item.state == "set") {
        item.event_type = "alarm"
      }
      else if (item.state == "log" ) {
        item.event_type = "log"
      }
      return item;
    }

  }
})();

