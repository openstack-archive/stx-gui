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
   * @name horizon.dashboard.fault_management.events_suppression
   * @ngModule
   * @description
   * Provides all the services and widgets require to display the Events Suppression
   * panel
   */
  angular
    .module('horizon.dashboard.fault_management.events_suppression', [
      'ngRoute',
      'horizon.dashboard.fault_management.events_suppression.actions'
    ])
    .constant('horizon.dashboard.fault_management.events_suppression.resourceType', 'OS::StarlingX::EventsSuppression')
    .run(run)
    .config(config);


  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.fault_management.events_suppression.service',
    'horizon.dashboard.fault_management.events_suppression.basePath',
    'horizon.dashboard.fault_management.events_suppression.resourceType'
  ];


  function run(registry, service, basePath, resourceType) {
    registry.getResourceType(resourceType)
    .setNames(gettext('Events Suppression'), gettext('Events Suppression'))

    // specify items for table row items, summary view and details view
    .setProperties(properties())

    // get items for table
    .setListFunction(service.getPromise)

    // set default url for index view. this will be used for reproducing
    // sidebar and breadcrumb when refreshing or accessing directly
    // details view.
    .setDefaultIndexUrl('/admin/events_suppression/')

    // specify table columns
    .tableColumns
    .append({
      id: 'alarm_id',
      priority: 1,
      sortDefault: true
    })
    .append({
      id: 'description',
      priority: 1
    })
    .append({
      id: 'suppression_status',
      priority: 1
    });
    // for magic-search
    registry.getResourceType(resourceType).filterFacets
    .append({
      'label': gettext('Event ID'),
      'name': 'alarm_id',
      'singleton': true
    })
    .append({
      'label': gettext('Description'),
      'name': 'description',
      'singleton': true
    })
    .append({
      'label': gettext('Status'),
      'name': 'is_suppressed',
      'singleton': true,
      'options': [
          {label: gettext('suppressed'), key: 'true'},
          {label: gettext('unsuppressed'), key: 'false'}
        ]
    })
    ;
  }

  function properties() {
    return {
      alarm_id: { label: gettext('Event ID'), filters: ['noValue'] },
      description: { label: gettext('Description'), filters: ['noValue'] },
      uuid: { label: gettext('Event UUID'), filters: ['noValue'] },
      suppression_status: { label: gettext('Status'), filters: ['noValue'] },
      links: { label: gettext('Links'), filters: ['noValue'] },
      is_suppressed: { label: gettext('IsSuppressed'), filters: ['noValue'] }
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/fault_management/events_suppression/';
    $provide.constant('horizon.dashboard.fault_management.events_suppression.basePath', path);
    $routeProvider.when('/admin/events_suppression', {
      templateUrl: path + 'panel.html'
    });
  }
})();
