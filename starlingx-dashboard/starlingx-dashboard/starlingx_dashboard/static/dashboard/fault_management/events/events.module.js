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
   * @name horizon.dashboard.fault_management.events
   * @ngModule
   * @description
   * Provides all the services and widgets require to display the Event panel
   */
  angular
    .module('horizon.dashboard.fault_management.events', [
      'ngRoute'
    ])
    .constant('horizon.dashboard.fault_management.events.resourceType', 'OS::StarlingX::Events')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.fault_management.events.service',
    'horizon.dashboard.fault_management.events.basePath',
    'horizon.dashboard.fault_management.events.resourceType'
  ];

  function run(registry, service, basePath, resourceType) {
    registry.getResourceType(resourceType)
    .setNames(gettext('Event'), gettext('Events'))

    // for detail summary view on table row
    .setSummaryTemplateUrl(basePath + 'details/drawer.html')

    // set default url for index view. this will be used for reproducing
    // sidebar and breadcrumb when refreshing or accessing directly
    // details view.
    .setDefaultIndexUrl('/admin/events/')

    // specify items for table row items, summary view and details view
    .setProperties(properties())

    // get items for table
    .setListFunction(service.getPromise)

    // specify table columns
    .tableColumns
    .append({
      id: 'timestamp',
      priority: 1,
      sortDefault: 'reverse'
    })
    .append({
      id: 'state',
      priority: 1
    })
    .append({
      id: 'event_log_id',
      priority: 1
    })
    .append({
      id: 'reason_text',
      priority: 1
    })
    .append({
      id: 'entity_instance_id',
      priority: 1
    })
    .append({
      id: 'suppression_status',
      priority: 1,
      allowed: service.suppressColAllowedPromiseFunction
    })
    .append({
      id: 'severity',
      priority: 2
    });

    // for magic-search
    registry.getResourceType(resourceType).filterFacets
     .append({
      'label': gettext('Event Type'),
      'name': 'event_type',
      'singleton': true,
       'options': [
          {label: gettext('log'), key: 'log'},
          {label: gettext('alarm'), key: 'alarm'}
        ]
    })
    .append({
      'label': gettext('ID'),
      'name': 'event_log_id',
      'singleton': true
    })
    .append({
      'label': gettext('Entity Instance ID'),
      'name': 'entity_instance_id',
      'singleton': true
    })
    .append({
      'label': gettext('Reason Text'),
      'name': 'reason_text',
      'singleton': true
    })
    .append({
      'label': gettext('State'),
      'name': 'state',
      'singleton': true,
      'options': [
          {label: gettext('clear'), key: 'clear'},
          {label: gettext('log'), key: 'log'},
          {label: gettext('set'), key: 'set'}
        ]
    })
    .append({
      'label': gettext('Severity'),
      'name': 'severity',
      'singleton': true,
      'options': [
          {label: gettext('critical'), key: 'critical'},
          {label: gettext('major'), key: 'major'},
          {label: gettext('minor'), key: 'minor'},
          {label: gettext('warning'), key: 'warning'},
          {label: gettext('not-applicable'), key: 'not-applicable'}
        ]
    })
    .append({
      'label': gettext('Timestamp'),
      'name': 'timestamp',
      'singleton': true
    })
    .append({
      'label': gettext('UUID'),
      'name': 'uuid',
      'singleton': true
    });
  }

  function properties() {
    return {
      uuid: { label: gettext('Event UUID'), filters: ['noValue'] },
      event_log_id: { label: gettext('ID'), filters: ['noValue'] },
      reason_text: { label: gettext('Reason Text'), filters: ['noValue'] },
      entity_instance_id: { label: gettext('Entity Instance ID'), filters: ['noValue'] },
      severity: { label: gettext('Severity'), filters: ['noValue'] },
      timestamp: { label: gettext('Timestamp'), filters: ['noValue'] },
      suppression_status: { label: gettext('Suppression Status'), filters: ['noValue'] },
      suppression: { label: gettext('Suppression'), filters: ['noValue'] },
      state: { label: gettext('State'), filters: ['noValue'] },
      service_affecting: { label: gettext('Service Affecting'), filters: ['noValue'] },
      event_log_type: { label: gettext('Alarm Type'), filters: ['noValue'] },
      probable_cause: { label: gettext('Probable Cause'), filters: ['noValue'] },
      entity_type_id: { label: gettext('Entity Type ID'), filters: ['noValue'] },
      proposed_repair_action: { label: gettext('Proposed Repair Action'), filters: ['noValue'] },
      event_type: { label: gettext('Event Type'), filters: ['noValue'] },
      _suppression_status: { label: gettext('_suppression_status'), filters: ['noValue'] }
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
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/fault_management/events/';
    $provide.constant('horizon.dashboard.fault_management.events.basePath', path);

    $routeProvider.when('/admin/events', {
      templateUrl: path + 'panel.html',
      resolve: {
        searchResults: ['horizon.dashboard.fault_management.events.service', function (searchService) {
            return searchService.getSuppressionList();
        }]
      }
    });
  }
})();
