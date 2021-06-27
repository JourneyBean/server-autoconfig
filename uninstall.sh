#!/bin/bash

# v0.3.0

# delete program file
rm /usr/share/bin/server-autoconfig
rm -r /opt/server-autoconfig

# delete config folder
rm -r /etc/server-autoconfig

# delete data
rm -r /var/cache/server-autoconfig

# delete service files
systemctl stop server-autoconfig.timer
rm /usr/lib/systemd/system/server-autoconfig.service
rm /usr/lib/systemd/system/server-autoconfig.timer
rm /usr/lib/systemd/system/server-autoconfig@.service
rm /usr/lib/systemd/system/server-autoconfig@.timer
systemctl daemon-reload
