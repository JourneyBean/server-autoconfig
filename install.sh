#!/bin/bash

# v0.3.0

# copy program file
mkdir /opt/server-autoconfig
cp ./server-autoconfig.py /opt/server-autoconfig/
chmod +x /opt/server-autoconfig/server-autoconfig.py
ln -s /usr/share/bin/server-autoconfig /opt/server-autoconfig/server-autoconfig.py

# copy config file
mkdir /etc/server-autoconfig
cp ./config.yml /etc/server-autoconfig/

# create data folder
mkdir -p /var/cache/server-autoconfig/

# copy service files
cp ./systemd/* /usr/lib/systemd/system/
systemctl daemon-reload
