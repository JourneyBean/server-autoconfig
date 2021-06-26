#!/bin/bash

# v0.3.0

mkdir /opt/server-autoconfig
cp ./server-autoconfig.py /opt/server-autoconfig/
ln -s /usr/share/bin/server-autoconfig /opt/server-autoconfig/server-autoconfig.py
cp ./server-autoconfig.yml /etc/
mkdir -p /var/cache/server-autoconfig/