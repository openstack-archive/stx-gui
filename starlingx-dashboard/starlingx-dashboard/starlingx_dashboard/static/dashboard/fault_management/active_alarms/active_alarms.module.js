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
 * Copyright (c) 2019 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.dashboard.fault_management.active_alarms
   * @ngModule
   * @description
   * Provides all the services and widgets require to display the Alarm
   * panel
   */
  angular
    .module('horizon.dashboard.fault_management.active_alarms', [
      'ngRoute',
      'horizon.dashboard.fault_management.active_alarms.details'
    ])
    .constant('horizon.dashboard.fault_management.active_alarms.resourceType', 'OS::StarlingX::ActiveAlarms')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.fault_management.active_alarms.service',
    'horizon.dashboard.fault_management.active_alarms.basePath',
    'horizon.dashboard.fault_management.active_alarms.resourceType'
  ];

  function run(registry, service, basePath, resourceType) {
    registry.getResourceType(resourceType)
    .setNames(gettext('Active Alarm'), gettext('Active Alarms'))

    // for detail summary view on table row
    .setSummaryTemplateUrl(basePath + 'details/drawer.html')

    // set default url for index view. this will be used for reproducing
    // sidebar and breadcrumb when refreshing or accessing directly
    // details view.
    // TODO(kbujold): Uncomment when we rebase to Stein, to fix upstream bug 1746706
    //.setDefaultIndexUrl('/admin/fault_management/')

    // specify items for table row items, summary view and details view
    .setProperties(properties())

    // get items for table
    .setListFunction(service.getPromise)

    // specify table columns
    .tableColumns
    .append({
      id: 'alarm_id',
      priority: 1,
      urlFunction: service.urlFunction
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
      id: 'severity',
      priority: 1,
      sortDefault: 'true'
    })
    .append({
      id: 'suppression_status',
      priority: 1,
      allowed: service.suppressColAllowedPromiseFunction
    })
    .append({
      id: 'timestamp',
      priority: 1
    });

    // for magic-search
    registry.getResourceType(resourceType).filterFacets
    .append({
      'label': gettext('Alarm ID'),
      'name': 'alarm_id',
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
      'label': gettext('Severity'),
      'name': 'severity',
      'singleton': true,
      'options': [
          {label: gettext('critical'), key: 'critical'},
          {label: gettext('major'), key: 'major'},
          {label: gettext('minor'), key: 'minor'},
          {label: gettext('warning'), key: 'warning'}
        ]
    })
    .append({
      'label': gettext('Timestamp'),
      'name': 'timestamp',
      'singleton': true
    })
    .append({
      'label': gettext('Management Affecting'),
      'name': 'mgmt_affecting',
      'singleton': true,
      'options': [
          {label: gettext('True'), key: 'True'},
          {label: gettext('False'), key: 'False'}
        ]
    })
    .append({
      'label': gettext('UUID'),
      'name': 'uuid',
      'singleton': true
    });
  }

  function properties() {
    return {
      uuid: { label: gettext('Alarm UUID'), filters: ['noValue'] },
      alarm_id: { label: gettext('Alarm ID'), filters: ['noValue'] },
      reason_text: { label: gettext('Reason Text'), filters: ['noValue'] },
      entity_instance_id: { label: gettext('Entity Instance ID'), filters: ['noValue'] },
      severity: { label: gettext('Severity'), filters: ['noValue'] },
      timestamp: { label: gettext('Timestamp'), filters: ['noValue'] },
      mgmt_affecting: { label: gettext('Management Affecting'), filters: ['noValue'] },
      suppression_status: { label: gettext('Suppression Status'), filters: ['noValue'] },
      alarm_state: { label: gettext('Alarm State'), filters: ['noValue'] },
      service_affecting: { label: gettext('Service Affecting'), filters: ['noValue'] },
      alarm_type: { label: gettext('Alarm Type'), filters: ['noValue'] },
      probable_cause: { label: gettext('Probable Cause'), filters: ['noValue'] },
      entity_type_id: { label: gettext('Entity Type ID'), filters: ['noValue'] },
      proposed_repair_action: { label: gettext('Proposed Repair Action'), filters: ['noValue'] },
      is_suppressed: { label: gettext('IsSuppressed'), filters: ['noValue'] },
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
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/fault_management/active_alarms/';
    $provide.constant('horizon.dashboard.fault_management.active_alarms.basePath', path);
    $routeProvider.when('/admin/active_alarms', {
      templateUrl: path + 'panel.html',
      resolve: {
        searchResults: ['horizon.dashboard.fault_management.active_alarms.service', function (searchService) {
            return searchService.getSuppressionList();
        }]
      }

    });
  }
})();
