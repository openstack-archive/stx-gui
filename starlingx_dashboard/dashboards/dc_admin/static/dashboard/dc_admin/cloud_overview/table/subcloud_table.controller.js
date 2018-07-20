/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */


(function() {
  'use strict';

  /**
   * @ngdoc dcOverviewCloudTableController
   * @ngController
   *
   * @description
   * Controller for the dc_admin overview table.
   * Serve as the focal point for table actions.
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview')
    .controller('dcOverviewCloudTableController', dcOverviewCloudTableController);

  dcOverviewCloudTableController.$inject = [
    '$q',
    '$scope',
    '$timeout',
    '$interval',
    '$window',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.app.core.openstack-service-api.dc_manager',
    'horizon.app.core.openstack-service-api.keystone',
  ];

  function dcOverviewCloudTableController(
    $q,
    $scope,
    $timeout,
    $interval,
    $window,
    toast,
    gettext,
    modalFormService,
    simpleModalService,
    deleteModal,
    dc_manager,
    keystone
  ){

    var ctrl = this;
    ctrl.subClouds = [];
    ctrl.isubClouds = [];
    ctrl.subCloudSummaries = [];

    //ctrl.globalActions = globalActions;

    ctrl.manage = manage;
    ctrl.unmanageSubcloud = unmanageSubcloud;
    ctrl.deleteSubcloud = deleteSubcloud;
    ctrl.addSubcloud = addSubcloud;
    ctrl.editSubcloud = editSubcloud;
    ctrl.addSubcloudAction = addSubcloudAction;
    ctrl.generateConfig = generateConfig;
    ctrl.downloadConfig = downloadConfig;
    ctrl.goToAlarmDetails = goToAlarmDetails;
    ctrl.goToHostDetails = goToHostDetails;

    // Auto-refresh
    ctrl.$interval = $interval;
    ctrl.refreshInterval;
    ctrl.refreshWaitTime = 5000;

    // Messages
    ctrl.endpointErrorMsg = gettext("This subcloud's endpoints are not yet accessible by horizon.  Please log out and log back in to access this subcloud.");

    getData();
    startRefresh();

    ////////////////////////////////

    function getData() {
      // Fetch subcloud data to populate the table
      $q.all([
        dc_manager.getSubClouds().success(getSubCloudsSuccess),
        dc_manager.getSummaries().success(getSummariesSuccess)
      ]).then(function(){
        map_subclouds();
      })
    }

    function getSubCloudsSuccess(response) {
      ctrl.subClouds = response.items;
    }

    function getSummariesSuccess(response) {
      ctrl.subCloudSummaries = response.items;
    }

    function map_subclouds() {
      ctrl.subClouds = $.map(ctrl.subClouds, function (subCloud){
        var match = ctrl.subCloudSummaries.filter(function(summary){return summary.name == subCloud.name;});
        if (match.length == 0){
          // No matching summary to this subcloud
          return subCloud;
        }
        return angular.extend(subCloud, match[0]);
      });
    }


    ///////////////////////////
    // REFRESH FUNCTIONALITY //
    ///////////////////////////

    function startRefresh() {
      if (angular.isDefined(ctrl.refreshInterval)) return;
      ctrl.refreshInterval = ctrl.$interval(getData, ctrl.refreshWaitTime);
    }

    $scope.$on('$destroy',function(){
      ctrl.stopRefresh();
    });

    function stopRefresh() {
      if (angular.isDefined(ctrl.refreshInterval)) {
        ctrl.$interval.cancel(ctrl.refreshInterval);
        ctrl.refreshInterval = undefined;
      }
    }


    /////////////////
    // UNMANAGE/MANAGE //
    /////////////////

    function manage(cloud) {
      var response = dc_manager.editSubcloud(cloud.subcloud_id, {'management-state': 'managed'});
    }

    function unmanageSubcloud(cloud) {
      var options = {
        title: 'Confirm Subcloud Unmanage',
        body: 'Are you sure you want to unmanage subcloud '+cloud.name+'?',
        submit: 'Unmanage',
        cancel: 'Cancel'
      };

      simpleModalService.modal(options).result.then(function() {
        dc_manager.editSubcloud(cloud.subcloud_id, {'management-state': 'unmanaged'});
      });
    }


    ////////////
    // DELETE //
    ////////////

    function deleteSubcloud(cloud) {
      var scope = { $emit: deleteActionComplete };
      var context = {
        labels: {
          title: gettext('Confirm Subcloud Delete'),
          message: gettext('This will delete subcloud %s, are you sure you want to continue?'),
          submit: gettext('Delete'),
          success: gettext('Subcloud delete successful.')
          },
        deleteEntity: doDelete,
        successEvent: 'success',
      };
      cloud.id = cloud.subcloud_id;
      deleteModal.open(scope, [cloud], context);

    }
    function doDelete(id) {
      var response = dc_manager.deleteSubcloud(id);
      return response;
    }

    function deleteActionComplete(eventType) {
      return;
    }


    /////////////////
    // CREATE/EDIT //
    /////////////////

    var subcloudSchema = {
      type: "object",
      properties: {
        "name": {
          type: "string",
          title: "Name"},
        "description": {
          type: "string",
          title: "Description"},
        "location": {
          type: "string",
          title: "Location"},
        "management-subnet": {
          type: "string",
          title: "Management Subnet"},
        "management-start-ip": {
          type: "string",
          title: "Management Start IP"},
        "management-end-ip": {
          type: "string",
          title: "Management End IP"},
        "management-gateway-ip": {
          type: "string",
          title: "Management Gateway IP"},
        "systemcontroller-gateway-ip": {
          type: "string",
          title: "System Controller Gateway IP"},
      },
      required: ["name", "management-subnet", "management-start-ip", "management-end-ip", "management-gateway-ip", "systemcontroller-gateway-ip"],
    };

    function addSubcloud() {
      var model = {
        "name": "",
        "description": "",
        "location": "",
        "management-subnet": "",
        "management-start-ip": "",
        "management-end-ip": "",
        "management-gateway-ip": "",
        "central-gateway-ip": ""};
      var config = {
        title: gettext('Add Subcloud'),
        schema: subcloudSchema,
        form: ["*"],
        model: model
      };
      return modalFormService.open(config).then(function then() {
        return ctrl.addSubcloudAction(model);
      });
    }

    function addSubcloudAction(model) {
      return dc_manager.createSubcloud(model);
    }

    var editsubcloudSchema  = {
      type: "object",
      properties: {
        "name": {
          type: "string",
          title: "Name",
          readonly: true},
        "description": {
          type: "string",
          title: "Description"},
        "location": {
          type: "string",
          title: "Location"},
      }
    };

    function editSubcloud(cloud) {
      var model = {
        "name": cloud.name,
        "description": cloud.description,
        "location": cloud.location,
        };

      var config = {
        title: gettext('Edit Subcloud'),
        schema: editsubcloudSchema,
        form: ["*"],
        model: model
      };
      return modalFormService.open(config).then(function(){
        return dc_manager.editSubcloud(cloud.subcloud_id, model);
      });
    }


    ////////////////////
    // GenerateConfig //
    ////////////////////

    var generateConfigSchema  = {
      type: "object",
      properties: {
        "management-interface-port": {
          type: "string",
          title: "Management Interface Port",},
        "management-interface-mtu": {
          type: "number",
          title: "Management Interface MTU"},
        "oam-subnet": {
          type: "string",
          title: "OAM Subnet"},
        "oam-gateway-ip": {
          type: "string",
          title: "OAM Gateway IP"},
        "oam-floating-ip": {
          type: "string",
          title: "OAM Floating IP"},
        "oam-unit-0-ip": {
          type: "string",
          title: "OAM Unit-0 IP"},
        "oam-unit-1-ip": {
          type: "string",
          title: "OAM Unit-1 IP"},
        "oam-interface-port": {
          type: "string",
          title: "OAM Interface Port"},
        "oam-interface-mtu": {
          type: "number",
          title: "OAM Interface MTU"},
        "system-mode": {
          type: "string",
          title: "System Mode",
          enum: ["duplex", "duplex-direct", "simplex"],
          default: "duplex"},
      },
    };

    function generateConfig(cloud) {
      var model = {};
      var config = {
        title: gettext('Generate Subcloud Configuration File'),
        schema: generateConfigSchema,
        form: ["*"],
        model: model,
      };
      return modalFormService.open(config).then(function(){
        return dc_manager.generateConfig(cloud.subcloud_id, model).success(function(response) {
          downloadConfig(response.config, cloud.name + "_config.ini");
        });
      });
    }


//    function generateConfig(cloud) {
//      return dc_manager.generateConfig(cloud.subcloud_id, {}).success(function(response) {
//        downloadConfig(response.config, cloud.name + "_config.ini");
//      });
//    }

    function downloadConfig(text, filename) {
      // create text file as object url
      var blob = new Blob([ text ], { "type" : "text/plain" });
      window.URL = window.URL || window.webkitURL;
      var fileurl = window.URL.createObjectURL(blob);
      // provide text as downloaded file
      $timeout(function() {
        //Update view
        var a = angular.element('<a></a>');
        a.attr("href", fileurl);
        a.attr("download", filename);
        a.attr("target", "_blank");
        angular.element(document.body).append(a);
        a[0].click();
        a.remove();
      }, 0);
    }


    /////////////
    // Details //
    /////////////

    function goToAlarmDetails(cloud) {
      // TODO handle tabs?

      // Check to see that the subcloud is managed
      if (cloud.management_state != 'managed') {
        toast.add('error',
            gettext('The subcloud must be in the managed state before you can access detailed views.'));
        return;
      }

      keystone.getCurrentUserSession().success(function(session){
        session.available_services_regions.indexOf(cloud.name)
        if (session.available_services_regions.indexOf(cloud.name) > -1) {
          $window.location.href = "/auth/switch_services_region/"+ cloud.name + "/?next=/admin/fault_management/";
        } else {
          toast.add('error', ctrl.endpointErrorMsg);
          // TODO(tsmith) should we force a logout here with an reason message?
        }
      }).error(function(error) {
        toast.add('error',
            gettext("Could not retrieve current user's session."));
      });
    }

    function goToHostDetails(cloud) {
      // Check to see that the subcloud is managed
      if (cloud.management_state != 'managed') {
        toast.add('error',
            gettext('The subcloud must be in the managed management state before you can access detailed views.'));
        return;
      }

      keystone.getCurrentUserSession().success(function(session){
        if (session.available_services_regions.indexOf(cloud.name) > -1) {
          $window.location.href = "/auth/switch_services_region/"+ cloud.name + "/?next=/admin/inventory/";
        } else {
          toast.add('error', ctrl.endpointErrorMsg);
        }
      }).error(function(error) {
        toast.add('error',
            gettext("Could not retrieve current user's session."));
      });
    }

  }
})();
