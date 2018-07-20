/* Core functionality related to page auto refresh. */
horizon.refresh = {
    refresh_interval: 5000,
    _refresh_functions: [],
    timeout: null,

    init: function() {
        // Add page refresh time to page header
        horizon.refresh.datetime();

        $('#navbar-collapse > div.context_selection > ul > li > ul  li  a ').click(function (){
          clearTimeout(horizon.refresh.timeout);
          clearTimeout(horizon.datatables.timeout);
        });

        // Setup next refresh interval
        horizon.refresh.timeout = setTimeout(horizon.refresh.update, horizon.refresh.refresh_interval);
    },

    update: function() {
        if (!horizon.refresh._refresh_functions.length) {
            // No refresh handlers registered
            return;
        }

        // Ignore any tabs which react badly to auto-refresh
        var ignore = ["instance_details__console"];

        // Figure out which tabs have been loaded
        loaded = "";
        $(".nav-tabs a[data-target]").each(function(index){
          var slug = $(this).attr('data-target').replace('#','');
          if ($(this).attr('data-loaded') == 'true' && ignore.indexOf(slug) == -1){
            if (loaded){loaded+=','}
            loaded+=slug;
          }
        });

        // Grab current href (for refresh) but remove the tab parameter ( if exists )
        var currentHREF = $(location).attr('href');
        var qryStrObj = jQuery.query.load( currentHREF );
        var oldQryStr = qryStrObj.toString();
        var newQryStr = qryStrObj.SET("tab", null).SET("loaded", loaded).COMPACT().toString();
        if (oldQryStr){
          var $href=currentHREF.replace(oldQryStr, newQryStr);
        }else {
          var $href=currentHREF += newQryStr;
        }

        horizon.ajax.queue({
            url: $href,
            success: function(data, textStatus, jqXHR) {
                var refreshed = true;
                if (jqXHR.responseText.length > 0) {
                    $(horizon.refresh._refresh_functions).each(function (index, f) {
                        refreshed = f(data);
                        return refreshed;
                    });
                    if (refreshed) {
                        horizon.refresh.datetime();
                    }
                } else {
                    // assume that the entity has been deleted
                    location.href = $('#sidebar-accordion a.openstack-panel.active').attr('href');
                }
            },
            error: function(jqXHR, textStatus, error) {
                // Zero-status usually seen when user navigates away
                if (jqXHR.status != 0) {
                    horizon.refresh.alert();
                }
            },
            complete: function(jqXHR, textStatus) {

                // Check for redirect condition
                var redirect = false
                switch (jqXHR.status) {
                case 401:
                    // Authorization error, likely redirect to login page
                    redirect = jqXHR.getResponseHeader("X-Horizon-Location");
                    break;
                case 404:
                    // The object seems to be gone, redirect back to main nav
                    redirect = $('#sidebar-accordion a.openstack-panel.active').attr('href');
                    break;
                case 302:
                    // Object is likely gone and are being redirect to index page
                    redirect = jqXHR.getResponseHeader("Location");
                    break;
                }
                if (redirect) {
                    location.href = redirect;
                }

                horizon.autoDismissAlerts();

                // Check for error condition
                var messages = $.parseJSON(horizon.ajax.get_messages(jqXHR));
                var errors = $(messages).filter(function (index, item) {
                    return item[0] == 'error';
                });
                if (errors.length > 0) {
                    horizon.refresh.alert();
                }

                // Reset for next refresh interval
                horizon.refresh.timeout = setTimeout(horizon.refresh.update, horizon.refresh.refresh_interval);
            }
        });
    },

    alert: function() {
        horizon.clearInfoMessages();
        horizon.clearErrorMessages();
        horizon.clearWarningMessages();
        horizon.alert("info", gettext("Failed to auto refresh page, retrying on next interval."));
    },

    datetime: function() {
        // Update page refresh time
        var location = $('.datetime');
        if (location !== null) {
            var datetime = new Date();
            location.html(datetime.toLocaleString());
        }
    },

    addRefreshFunction: function(f) {
        horizon.refresh._refresh_functions.push(f);
    }
};

horizon.addInitFunction(function() {
    horizon.refresh.init();
});
