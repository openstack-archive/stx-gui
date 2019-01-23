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
   * @ngname horizon.dashboard.fault_management.events_suppression.actions
   *
   * @description
   * Provides all of the actions for Events Suppression.
   */
  angular
    .module('horizon.dashboard.fault_management.events_suppression.actions', [
      'horizon.framework',
      'horizon.dashboard.fault_management'
    ])
    .run(registerEventsSuppressionActions);

  registerEventsSuppressionActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.dashboard.fault_management.events_suppression.suppress_event.service',
    'horizon.dashboard.fault_management.events_suppression.unsuppress_event.service',
    'horizon.dashboard.fault_management.events_suppression.resourceType'
  ];

  function registerEventsSuppressionActions (
    registry,
    gettext,
    suppressEventService,
    unsuppressEventService,
    resourceType
  ) {
    var eventSuppressionResourceType = registry.getResourceType(resourceType);

     eventSuppressionResourceType.itemActions
      .append({
        id: 'suppressEventAction',
        service: suppressEventService,
        template: {
          type: 'danger',
          text: gettext('Suppress Event')
        }
      });

     eventSuppressionResourceType.itemActions
      .append({
        id: 'unsuppressEventAction',
        service: unsuppressEventService,
        template: {
          type: 'danger',
          text: gettext('Unsuppress Event')
        }
      });

  }
})();
