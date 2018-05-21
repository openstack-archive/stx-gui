/**
 * Copyright (c) 2017 Wind River Systems, Inc.
 *
 * The right to copy, distribute, modify, or otherwise make use
 * of this software may be licensed only pursuant to the terms
 * of an applicable Wind River license agreement.
 */

(function() {
  'use strict';

  describe('horizon.dashboard.dc_admin', function() {
    it('should exist', function() {
      expect(angular.module('horizon.dashboard.dc_admin')).toBeDefined();
    });
  });

  describe('horizon.dashboard.dc_admin.basePath constant', function() {
    var dc_adminBasePath, staticUrl;

    beforeEach(module('horizon.dashboard.dc_admin'));
    beforeEach(inject(function($injector) {
      dc_adminBasePath = $injector.get('horizon.dashboard.dc_admin.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should equal to "/static/dashboard/dc_admin/"', function() {
      expect(dc_adminBasePath).toEqual(staticUrl + 'dashboard/dc_admin/');
    });
  });

})();
