/* Functionality related to detail panes */
horizon.details = {
};

horizon.details.refresh = function(html) {
    var $new_details = $(html).find('.detail > dl').parent();
    var $old_details = $('.detail > dl').parent();

    if ($new_details.length != $old_details.length) {
        // Page structure has changed, abort refresh
        return false;
    }

    $new_details.each(function(index, elm) {
        var $new_detail = $(this);
        var $old_detail = $($old_details.get(index));
        if ($new_detail.html() != $old_detail.html()) {
            $old_detail.replaceWith($new_detail);
        }
    });

    return true;
};

horizon.addInitFunction(function() {
  if ($('.detail > dl').length > 0) {
      // Register callback handler to update the detail panels on page refresh
      horizon.refresh.addRefreshFunction(horizon.details.refresh);
  }
});
