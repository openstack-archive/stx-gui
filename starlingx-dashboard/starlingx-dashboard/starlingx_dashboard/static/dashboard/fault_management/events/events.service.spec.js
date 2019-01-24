/**
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 *  Copyright (c) 2019 Wind River Systems, Inc.
 *
 *  SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
  "use strict";

  describe('Event service', function() {
    var service;
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.fault_management.events'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.dashboard.fault_management.events.service');
    }));

    describe('getPromise', function() {
      it("provides a promise", inject(function($q, $injector, $timeout) {
        var api = $injector.get('horizon.app.core.openstack-service-api.fm');
        var deferred = $q.defer();
        spyOn(api, 'getEvents').and.returnValue(deferred.promise);
        var result = service.getPromise({});
        deferred.resolve({
          data:{
            items: [{uuid: '123abc', reason_text: 'resource1'}]
          }
        });
        $timeout.flush();
        expect(api.getEvents).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].reason_text).toBe('resource1');
      }));
    });

  });

})();

