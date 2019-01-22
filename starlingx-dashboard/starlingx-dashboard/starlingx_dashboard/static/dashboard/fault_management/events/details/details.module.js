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
   * @ngname horizon.dashboard.fault_management.events.details
   *
   * @description
   * Provides details features for Event.
   */
  angular
    .module('horizon.dashboard.fault_management.events.details', [
      'horizon.app.core',
      'horizon.framework.conf'
    ])
    .run(registerDetails);

  registerDetails.$inject = [
    'horizon.app.core.openstack-service-api.fm',
    'horizon.dashboard.fault_management.events.basePath',
    'horizon.dashboard.fault_management.events.resourceType',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerDetails(
    api,
    basePath,
    resourceType,
    registry
  ) {
    registry.getResourceType(resourceType)
      .setLoadFunction(loadFunction)
      .detailsViews.append({
        id: 'eventsDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });


    function loadFunction(uuid) {
      return api.getEvent(uuid);
    }
  }
})();
