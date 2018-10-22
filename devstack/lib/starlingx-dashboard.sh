#!/bin/bash
#
# lib/starlingx-dashboard.sh
# Functions to control the configuration and operation of the ***gui*** service

# Dependencies:
#
# - ``functions`` file
# - ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined
# - ``SERVICE_{TENANT_NAME|PASSWORD}`` must be defined
# - ``SERVICE_HOST``
# - ``KEYSTONE_TOKEN_FORMAT`` must be defined

# ``stack.sh`` calls the entry points in this order:
#
# - install_stx-dashboard
# - configure_stx-dashboard
# - init_stx-dashboard
# - start_stx-dashboard
# - stop_stx-dashboard
# - clean_stx-dashboard

_XTRACE_STX_CONFIG=$(set +o | grep xtrace)
set -o xtrace

# Defaults
# --------

export BIN_DIR=${BIN_DIR:-"/usr/local/bin"}
export LIB_DIR=${LIB_DIR:-"/usr/local/lib"}
export INC_DIR=${INC_DIR:-"/usr/local/include"}
export UNIT_DIR=/etc/systemd/system/
export MAJOR=${MAJOR:-1}
export MINOR=${MINOR:-0}

PY_PKG_NAME=starlingx_dashboard
ENABLED_DIR=/usr/share/openstack-dashboard/openstack_dashboard/enabled/
PYTHON2_SITELIB=/usr/lib/python2.7/site-packages


STX_DASHBOARD_VERSION="1.0"
STX_DASHBOARD_DIR=$DEST/stx-gui/starlingx-dashboard/starlingx-dashboard/

# Functions
# ---------

function install_stx-dashboard(){
    cd $STX_DASHBOARD_DIR
    export PBR_VERSION=$STX_DASHBOARD_VERSION
    python2 setup.py build
    sudo -E python2 setup.py install

    sudo install -d -m 755 $ENABLED_DIR
    sudo install -p -D -m 755 $PY_PKG_NAME/enabled/* $ENABLED_DIR
}

function configure_stx-dashboard(){
    :
}

function init_stx-dashboard(){
    :
}

function start_stx-dashboard(){
    :
}

function stop_stx-dashboard(){
    :
}

function clean_stx-dashboard(){
    cd $STX_DASHBOARD_DIR
    sudo rm -rf $PYTHON2_SITELIB/$PY_PKG_NAME
    sudo rm -rf $PYTHON2_SITELIB/$PY_PKG_NAME-$STX_DASHBOARD_VERSION*.egg-info 
    sudo rm -rf $ENABLED_DIR
}
