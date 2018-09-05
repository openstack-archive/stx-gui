/* Core functionality related to alam-banner. */
horizon.alarmbanner = {

    enabled: false,
    refresh: function(data) {

        var $old = $(location).attr('pathname');
        var $url = $(location).attr('href');
        $url = $url.replace($old, "/admin/fault_management/banner");

        horizon.ajax.queue({
            url: $url,
            success: function(data, textStatus, jqXHR) {
                var $new = $(data);
                var $old = $('.alarmbanner');
                if ($new.html() !== $old.html()) {
                    $old.html($new.html());
                }

                // start periodic refresh
                if (horizon.alarmbanner.enabled === false) {
                    horizon.refresh.addRefreshFunction(
                           horizon.alarmbanner.refresh);
                    horizon.alarmbanner.enabled = true;
                }
            },
            error: function(jqXHR, textStatus, error) {
                if (jqXHR.status !== 401 && jqXHR.status !== 403) {
                    // error is raised with status of 0 when ajax query is cancelled
                    // due to new page request
                    if (jqXHR.status !== 0) {
                        horizon.clearInfoMessages();
                        horizon.clearErrorMessages();
                        horizon.alert("info", gettext("Failed to refresh alarm banner, retrying on next interval."));
                    }

                    // start periodic refresh
                    if (horizon.alarmbanner.enabled === false) {
                         horizon.refresh.addRefreshFunction(
                                horizon.alarmbanner.refresh);
                         horizon.alarmbanner.enabled = true;
                    }
                }
            },
            complete: function(jqXHR, textStatus) {
            }
        });
        return true;
    },

    onclick: function() {
        var $fm = "/admin/fault_management";
        var $dc = "/dc_admin/";
        var $cur = document.location.href;
        var $path = document.location.pathname;
        if ($path.match($fm) === null && $path.match($dc) === null) {
            document.location.href = $cur.replace($path, $fm);
        }
    },
};


horizon.addInitFunction(function() {
    // trigger alarm banner refresh on page load and enable
    // periodic refresh after the first one
    horizon.alarmbanner.refresh(null);
});
