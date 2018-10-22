#!/bin/bash# devstack/plugin.sh
# Triggers stx-gui specific functions to install and configure starlingx dashboard
#
#

function install_stx_dashboard {
    setup_develop ${STX_GUI_DIR}/starlingx-dashboard/starlingx-dashboard
}

function configure_stx_dashboard {
    cp -a ${STX_GUI_DIR}/starlingx-dashboard/starlingx-dashboard/starlingx_dashboard/enabled/* $DEST/horizon/openstack_dashboard/local/enabled
    cp -a ${STX_GUI_DIR}/starlingx-dashboard/starlingx-dashboard/starlingx_dashboard/local/local_settings.d/_30_stx_local_settings.py $DEST/horizon/openstack_dashboard/local/local_settings.d/
}

#check for service enabled
if is_service_enabled horizon && is_service_enabled stx-gui; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing stx-gui"
        install_stx_dashboard

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring stx-gui"
        configure_stx_dashboard

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
        rm -f $DEST/horizon/openstack_dashboard/local/enabled/*starlingx*
        rm -f $DEST/horizon/openstack_dashboard/local/enabled/_2212_WRS_dc_admin_software_management_panel.py
        rm -f $DEST/horizon/openstack_dashboard/local/local_settings.d/_30_stx_local_settings.py
    fi
fi
