/**
 *  Copyright (c) 2019 Wind River Systems, Inc.
 *
 *  SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
  'use strict';

  angular
    .module('horizon.dashboard.fault_management')
    .factory('horizon.dashboard.fault_management.events_suppression.unsuppress_event.service', updateService);

  updateService.$inject = [
    '$location',
    'horizon.app.core.openstack-service-api.fm',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.q.extensions'
    ];

  function updateService($location, api, simpleModalService, toastService, $qExtensions) {

    var scope;

    var service = {
      perform: perform,
      allowed: allowed
    };

    var unsuppressedText = "Unsuppress Event";
    var unsuppressed = "unsuppressed";

    return service;

    function perform(selected, newScope) {

      var alarm_id = selected.alarm_id;

      var options = {
        title: 'Confirm ' + unsuppressedText,
        body: 'You have selected: "' + alarm_id +
              '". Please confirm your selection. Events with selected Alarm ID will be ' +
              unsuppressed + '.',
        submit: unsuppressedText,
        cancel: 'Cancel'
      };

      selected = angular.isArray(selected) ? selected : [selected];

      return simpleModalService.modal(options).result.then(onModalSubmit);

      function onModalSubmit() {
        return $qExtensions.allSettled(selected.map(updateEntityPromise)).then(notify);
      }

      function updateEntityPromise(selected) {
        var status = {'suppression_status': unsuppressed};
        return {promise: api.updateEventSuppression(selected.uuid, status)};
      }

      function notify(result) {
        if (result.pass.length > 0) {
          var msg = gettext("Events %(unsuppressed)s for Alarm ID: %(alarm_id)s");
          toastService.add('success', interpolate(msg, {unsuppressed: unsuppressed, alarm_id: alarm_id}, true));
          $location.path('/admin/events_suppression');
        }

        if (result.fail.length > 0) {
          var msg = gettext("Failed to %(unsuppressed)s events for Alarm ID: %(alarm_id)s");
          toastService.add('error', interpolate(msg, {unsuppressed: unsuppressed, alarm_id: alarm_id}, true));
          return result;
        }
      }
    }

    function allowed($scope) {
      if ($scope.suppression_status == unsuppressed) {
        return $qExtensions.booleanAsPromise(false);
      }
      else {
        return $qExtensions.booleanAsPromise(true);
      }
    }

  }
})();
