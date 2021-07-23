#!/bin/bash
set -v on

# v0.3.5

# pull files
git pull

# copy program file\
cp ./server-autoconfig.py /opt/server-autoconfig/
chmod +x /opt/server-autoconfig/server-autoconfig.py

# copy config file
cp ./config.yml /etc/server-autoconfig/

# copy service files
cp ./systemd/* /usr/lib/systemd/system/
systemctl daemon-reload
