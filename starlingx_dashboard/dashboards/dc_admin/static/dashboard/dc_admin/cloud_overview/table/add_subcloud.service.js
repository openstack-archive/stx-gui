/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.dashboard.container-infra.clusters.create.service
   * @description Service for the container-infra cluster create modal
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview')
    .factory('horizon.dashboard.dc_admin.cloud_overview.add_subcloud.service', createService);

  createService.$inject = [
    '$location',
    'horizon.app.core.openstack-service-api.dc_manager',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
  ];

  function createService(
    $location, dc_manager, actionResult, gettext, $qExtensions, modal, toast
  ) {

    var config;
    var message = {
      success: gettext('Subcloud %s was successfully created.')
    };

    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function perform(selected, $scope) {
      config = workflow.init('create', gettext('Create'), $scope);
      if (typeof selected !== 'undefined') {
        config.model.cluster_template_id = selected.id;
      }
      return modal.open(config).then(submit);
    }

    function allowed() {
      return $qExtensions.booleanAsPromise(true);
    }

    function submit(context) {
      context.model = cleanNullProperties(context.model);
      return magnum.createCluster(context.model, false).then(success, true);
    }

    function cleanNullProperties(model) {
      // Initially clean fields that don't have any value.
      // Not only "null", blank too.
      for (var key in model) {
        if (model.hasOwnProperty(key) && model[key] === null || model[key] === "" ||
            key === "tabs") {
          delete model[key];
        }
      }
      return model;
    }

    function success(response) {
      response.data.id = response.data.uuid;
      toast.add('success', interpolate(message.success, [response.data.id]));
      var result = actionResult.getActionResult()
                   .created(resourceType, response.data.id);
      if (result.result.failed.length === 0 && result.result.created.length > 0) {
        $location.path("/project/clusters");
      } else {
        return result.result;
      }
    }
  }
})();