# Server Autoconfig

A config rollback system written in Python.

## Features

- Pull configuration files using git.
- Easily applying changes to services.
- Easy to revert changes using git.
- Uploading current configuration files to git repo.

## Install

Simplily run `install.sh`.

Or you can also copy the files manually.

## Requirments

Software: git, python3

## Setup

For first run, it is recommend to copy the sample `config.yml` file to `/etc/server-autoconfig/config.yml`.

Then edit this config file. Change whatever you see to suitable value. A sample `config.yml` should be like:

`config.yml`

``` yaml
instance-id: 1a2b

git:
  repo: https://example.com/your-private-repo.git
  branch: main

services:
  - dnsmasq:
      reload-method: systemd-reload
      systemd-units:
        - dnsmasq.service
      file-pairs:
        - bedroom_router/dnsmasq.conf:/etc/dnsmasq/dnsmasq.conf
```

Then run:

```
server-autoconfig update
```

Then the script will do:

1. Clone your git repo to `/var/cache/server-autoconfig/id_${instance-id}/repo`. 
2. Config files in your system listed in config file will be backuped to git branch `backup`.
3. Copy files from git listed in config to your system.
4. Reload services.

## Usage

### Update specify service

```
server-autoconfig update service_name
```

### Don't reload services

```
server-autoconfig update --no-reload
```

### Revert changes

```
server-autoconfig revert
```

## How it works

