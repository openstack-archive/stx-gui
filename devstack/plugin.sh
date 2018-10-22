#!/bin/bash# devstack/plugin.sh
# Triggers stx-gui specific functions to install and configure starlingx dashboard
# Dependencies:
#
# - ``functions`` file
# - ``DATA_DIR`` must be defined# ``stack.sh`` calls the entry points in this order:
#

LIBDIR=$DEST/stx-gui/devstack/lib
source $LIBDIR/starlingx-dashboard.sh
# check for service enabled

if is_service_enabled stx-gui; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
	# Perform installation of service source
	echo_summary "Installing stx-gui"
	install_stx-dashboard

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
	echo_summary "Configuring stx-gui"

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize and start the service
        echo_summary "Initializing and start stx-gui"

    elif [[ "$1" == "stack" && "$2" == "test-config" ]]; then
        # do sanity test
        echo_summary "do test-config"
    fi
    if [[ "$1" == "unstack" ]]; then
        # Shut down services
        echo_summary "Stop stx-gui service"
    fi
    if [[ "$1" == "clean" ]]; then
	clean_stx-dashboard
    fi
fi
