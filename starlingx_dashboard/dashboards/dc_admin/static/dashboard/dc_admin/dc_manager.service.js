/**
 * Copyright (c) 2017 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.dc_manager', DCManagerAPI);

  DCManagerAPI.$inject = [
    '$q',
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service',
    '$http'
  ];

  function DCManagerAPI($q, apiService, toastService, $http) {
    var service = {
      getSummaries: getSummaries,
      createSubcloud: createSubcloud,
      editSubcloud: editSubcloud,
      getSubClouds: getSubClouds,
      deleteSubcloud: deleteSubcloud,
      generateConfig: generateConfig
    };

    var csrf_token = $('input[name=csrfmiddlewaretoken]').val();
    $http.defaults.headers.post['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.common['X-CSRFToken'] = csrf_token;
    $http.defaults.headers.put['X-CSRFToken'] = csrf_token;

    return service;


    ///////////////
    // Summaries //
    ///////////////

    function getSummaries() {
      return apiService.get('/api/dc_manager/alarm_summaries/')
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext('Unable to retrieve the subcloud alarm summaries.'));
        });
    }


    ///////////////
    // SubClouds //
    ///////////////

    /**
     * @name createSubcloud
     * @description
     * Create a subcloud
     * @param {string} model a dict of attributes for the new subcloud.
     * @returns {Object} The result of the API call
     */
    function createSubcloud(model) {
      return apiService.put(
        '/api/dc_manager/subclouds/',
        {
          data: model,
        }
      )
      .error(function (error, status) {
        var msg;
        if (error.indexOf("<html") !== -1 || error.indexOf("<?xml") !== -1) {
          msg = "HTTP Error Code: " + status;
        }
        else {
          msg = error;
        }

        toastService.clearErrors();
        toastService.add('error', gettext(msg));
      })
      .success(function () {
        toastService.clearErrors();
        toastService.add('success', gettext('Subcloud created succesfully.'));
      });
    }

    /**
     * @name editSubcloud
     * @description
     * Update a subcloud by subcloud ID
     * @param {string} subcloud_id Specifies the id of the subcloud modify.
     * @param {object} updated attributes to modify.
     * @returns {Object} The result of the API call
     */
    function editSubcloud(subcloud_id, updated) {
      return apiService.patch(
        '/api/dc_manager/subclouds/' + subcloud_id,
        {
          updated: updated
        }
      )
      .error(function (error, status) {
        var msg;
        if (error.indexOf("<html") !== -1 || error.indexOf("<?xml") !== -1) {
          msg = "HTTP Error Code: " + status;
        }
        else {
          msg = error;
        }
        toastService.clearErrors();
        toastService.add('error', gettext(msg));
      })
      .success(function () {
        toastService.add('success', gettext('Subcloud edited succesfully.'));
      });
    }

    function getSubClouds() {
      return apiService.get('/api/dc_manager/subclouds/')
        .error(function () {
          toastService.clearErrors();
          toastService.add('error', gettext('Unable to retrieve the subclouds.'));
        });
    }

    /**
     * @name deleteSubcloud
     * @description
     * Deletes single subcloud by ID.
     *
     * @param {string} subcloud_id
     * The Id of the subcloud to delete.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     *
     * @returns {Object} The result of the API call
     */
    function deleteSubcloud(subcloud_id, suppressError) {
      return apiService.delete('/api/dc_manager/subclouds/' + subcloud_id)
      .error(function (error, status) {
        toastService.clearErrors();
        toastService.add('error', gettext(error));
      });
    }


    /**
     * @name generateConfig
     * @description
     * Generate a subcloud config with the given data
     * @param {string} subcloud_id Specifies the id of the subcloud to generate for.
     * @param {object} data a dict of attributes to be inserted into the config.
     * @returns {Object} The result of the API call
     */
    function generateConfig(subcloud_id, data) {
      var response = apiService.get('/api/dc_manager/subclouds/' + subcloud_id + '/generate-config/', {params: data})
      .error(function (error, status) {
        var msg;
        if (error.indexOf("<html") !== -1 || error.indexOf("<?xml") !== -1) {
          msg = "HTTP Error Code: " + status;
        }
        else {
          msg = error;
        }
        toastService.clearErrors();
        toastService.add('error', gettext(msg));
      });
      return response;
    }

  }
}());
