# Server Autoconfig

A config rollback system written in Python.

## Features

- Pull configuration files using git.
- Easily applying changes to services.
- Easy to revert changes using git.
- Uploading current configuration files to git.

## Install

Simplily run `install.sh`.

Or you can also copy the files manually.

## Usage

For first use, edit the `config.yml`, then execute

```
server-autoconfig init
```

The script will automatically clone the git repo.

Next, execute

```
server-autoconfig update
```

Then configuration files will be replaced and services will be reloaded.

## To-do

- Revert last changed
- Pushing to remote