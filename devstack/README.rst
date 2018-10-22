=================================
Stx-gui dashboard devstack plugin
=================================

This directory contains the stx-gui devstack plugin

To enable the plugin, add the following to your local.conf:

    enable_plugin stx-gui <stx-gui GITURL> [GITREF]

where

    <stx-gui GITURL> is the URL of stx-gui repository
    [GITREF] is an optional git ref (branch/ref/tag). The default is master

For example:

    enable_plugin stx-gui https://git.openstack.org/openstack/stx-gui

Note:

    So far, this plugin is setup to work with openstack pike.
