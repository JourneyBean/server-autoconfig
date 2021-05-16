#!/bin/python3

# Usage: server-autoconfig action [options]
# action: init, update [--write-and-restart] [--write-files-only] [--restart-services-only]
# -r git-repo-addr : specify git repo
# -b branch : specify git branch name
# -s service-name : specify what service to be affected. 
#                   'all' for all services in conf file.
# -m systemd-restart-method : "restart" or "reload" or "stop"
# -f file-pairs : /relative/path/in/git/file.conf:/absolute/path/in/system/file.conf
#
# -c conf-file : specify config file. default: /etc/server-autoconfig/server-autoconfig.yml

import yaml
import argparse
import os
import subprocess

# default parameters
class config:
    config_path = '/etc/server-autoconfig/config.yml'
    repo_path = '/home/johnson/Projects/test/repo'
    debug = False
    config = []

def isUnitExists(name):

    p = subprocess.Popen(["systemctl", "list-units", "--all", name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT
    )

    count = 0
    while p.poll() is None:
        line = p.stdout.readline()
        # print(line)
        count = count + 1

    return (count-8) > 0

# Handle command line config and config file
def args_parser():

    # setup argparse

    argp = argparse.ArgumentParser(
        'server-autoconfig',
        description='''Auto config application tool from git repo.
                        Note that command line parameters will override parameters in config file.
                    '''
    )

    argp.add_argument(
        'action',
        choices=['init', 'update'],
        metavar='{init|update}',
        help='{init, update} init will clone your git repo only.'
    )

    argp.add_argument(
        '-c', '--config',
        required=False,
        metavar='config-file',
        help='Config file in YAML format'
    )

    argp.add_argument(
        '--debug',
        action='store_true',
        help='Activate debug.'
    )

    argp.add_argument(
        '--no-restart',
        action='store_true',
        help='Don\'t restart services when update.'
    )

    argp.add_argument(
        '-r', '--repo',
        required=False,
        metavar='git-repo-url',
        help='Your Git repo\'s URL'
    )

    argp.add_argument(
        '-b', '--branch',
        required=False,
        metavar='git-branch',
        help='Your Git repo\'s branch.'
    )

    argp.add_argument(
        '-n', '--name',
        required=False,
        metavar='name',
        help='Service name defined in YAML config. Or you can specify a new name.'
    )

    argp.add_argument(
        '--reload-method', '-m',
        required=False,
        choices=['systemd-reload', 'systemd-restart', 'systemd-stop', 'command', 'shell'],
        metavar='{systemd-reload|systemd-restart|systemd-stop|command|shell}',
        help='Systemd units to restart.'
    )

    argp.add_argument(
        '--units', '-u',
        nargs='?',
        required=False,
        metavar='systemd-unit-name',
        help='Systemd units to restart.'
    )

    argp.add_argument(
        '--reload-command',
        required=False,
        metavar='command',
        help='Command to restart service.'
    )

    argp.add_argument(
        '--reload-shell',
        required=False,
        metavar='shell-path',
        help='Shell file to restart service.'
    )

    argp.add_argument(
        '--files', '-f',
        nargs='?',
        required=False,
        metavar='repo-file-path:system-file-path',
        help='File pairs to replace system-config-file to repo-file-path'
    )

    args = argp.parse_args()

    # args logic check
    if args.reload_method or args.units or args.reload_command or args.reload_shell or args.files:
        if not args.name:
            exit('[ERR] Muse specify a name when adding or modifying a service. Exiting.')

    if args.reload_method == 'systemd-reload' or args.reload_method == 'systemd-restart':
        if not args.units:
            exit('[ERR] Must specify aleast one systemd unit using --units when using reload_method=systemd-reload or systemd-restart. Exiting.')

    if args.reload_method == 'command':
        if not args.reload_command:
            exit('[ERR] Must specify command using --reload-command when using reload_method=command. Exiting.')

    if args.reload_method == 'shell':
        if not args.reload_shell:
            exit('[ERR] Must specify a shell file using --reload-shell when using reload_method=shell. Exiting.')
    
    if args.reload_shell:
        if not os.path.exists(args.reload_shell):
            exit('[ERR] File not found for reload shell file: ' + args.reload_shell + '. Exiting.')

    return args

# mix command-line arguments and config file
def config_parser(args, init):

    # get config file path
    if args.config:
        config.config_path = args.config
    if not os.path.exists(config.config_path):
        exit('[ERR] Failed to open config file: ' + config.config_path + '. Exiting.')
    print('[INFO] Using config file: ' + config.config_path)

    # read config file
    f = open(config.config_path, 'r', encoding='utf-8')
    cfg = f.read()
    config.config = yaml.safe_load(cfg)

    # merge config file and command line parameters
    if args.repo:
        config.config['git']['addr'] = args.repo
    
    if args.branch:
        config.config['git']['branch'] = args.branch

    if args.name:
        if args.name in config.config['services']:
            # name in config file. override.
            if args.reload_method:
                config.config['services'][args.name]['reload-method'] = args.reload_method
                if args.reload_method == 'systemd-reload' or args.reload_method == 'systemd-restart':
                    config.config['services'][args.name]['systemd-units'] = args.units
                if args.reload_method == 'command':
                    config.config['services'][args.name]['reload-command'] = args.reload_command
                if args.reload_method == 'shell':
                    config.config['services'][args.name]['reload-shell'] = args.reload_shell
            if args.files:
                config.config['services'][args.name]['files'] = args.files
        else:
            # name not in config file. temporary add new service.
            config.config['services'][args.name] = {}
            if args.reload_method:
                config.config['services'][args.name]['reload-method'] = args.reload_method
                if args.reload_method == 'systemd-reload' or args.reload_method == 'systemd-restart':
                    config.config['services'][args.name]['systemd-units'] = args.units
                if args.reload_method == 'command':
                    config.config['services'][args.name]['reload-command'] = args.reload_command
                if args.reload_method == 'shell':
                    config.config['services'][args.name]['reload-shell'] = args.reload_shell
            if args.files:
                config.config['services'][args.name]['files'] = args.files
    
    # if init mode, not checking files.
    if not init:
        # print(config.config)
        # check config file
        for service_name in config.config['services']:

            # check reload-method
            if config.config['services'][service_name]['reload-method']:

                # is systemd-reload or systemd-restart
                if (config.config['services'][service_name]['reload-method'] == 'systemd-reload' or
                    config.config['services'][service_name]['reload-method'] == 'systemd-restart'):

                    # check systemd-units
                    if config.config['services'][service_name]['systemd-units']:
                        for unit_file in config.config['services'][service_name]['systemd-units']:
                            if not isUnitExists(unit_file):
                                exit('[ERR] Config parse error: in section services/' + service_name + '/systemd-units: Unit ' + unit_file + ' not found.' )

                # is shell to reload
                if (config.config['services'][service_name]['reload-method'] == 'shell'):

                    # check if file exists
                    if (not 'reload-shell' in config.config['services'][service_name]) or (not os.path.exists(config.config['services'][service_name]['reload-shell'])):
                        exit('[ERR] Config parse error: in section services/' + service_name + '/reload-shell: Not found.')

                # is command to reload
                if (config.config['services'][service_name]['reload-method'] == 'command'):

                    # check if command exists
                    if (not 'reload-command' in config.config['services'][service_name]) and (not config.config['services'][service_name]['reload-command']):
                        exit('[ERR] Config parse error: in section services/' + service_name + '/reload-command: Command cannot be null.')

            else:
                config.config['services'][service_name]['reload-method'] = 'command'
                config.config['services'][service_name]['reload-command'] = 'sleep 0'
            
            # check files
            if (not config.config['services'][service_name]['files']):
                exit('[ERR] Config parse error: in section services/' + service_name + ': Section file not found. Must contain one.')
            for file_pair in config.config['services'][service_name]['files']:
                repo_file = file_pair[:file_pair.index(':')]
                repo_file = config.repo_path + '/' + repo_file
                target_file = file_pair[file_pair.index(':')+1:]
                if not os.path.exists(repo_file):
                    exit('[ERR] Config parse error: in section services/' + service_name + '/files/: ' + repo_file + ': Cannot found file. Try init first.')
                if not os.path.exists(target_file):
                    print('[INFO] In section services/' + service_name + '/files/' + target_file + ': Cannot found file.')


    return True

def action_init_handler(args):

    print('[INFO] Ready to init.')

    # clone git repo
    print('[INFO] Repo: ' + config.config['git']['addr'])
    print('[INFO] local: ' + config.repo_path)
    cmd = "git clone " + config.config['git']['addr'] + ' ' + config.repo_path
    print(cmd)
    os.system(cmd)

    # checkout branch
    cmd = 'cd ' + config.repo_path + ' && git checkout ' + config.config['git']['branch']
    print(cmd)
    os.system(cmd)

    return True

def action_update_handler(args):

    print('[INFO] Ready to update.')

    # pull git repo
    cmd = 'cd ' + config.repo_path + ' && git checkout ' + config.config['git']['branch']
    print(cmd)
    os.system(cmd)

    cmd = 'cd ' + config.repo_path + ' && git pull'
    print(cmd)
    os.system(cmd)

    # handle service
    for service_name in config.config['services']:

        # copy files
        for file_pair in config.config['services'][service_name]['files']:
            repo_file = file_pair[:file_pair.index(':')]
            repo_file = config.repo_path + '/' + repo_file
            target_file = file_pair[file_pair.index(':')+1:]
            
            cmd = 'cp ' + repo_file + ' ' + target_file
            print(cmd)
            os.system(cmd)
        
        # restart service
        if config.config['services'][service_name]['reload-method'] == 'systemd-reload':
            for unit_file in config.config['services'][service_name]['systemd-units']:
                cmd = 'systemctl reload ' + unit_file
                print(cmd)
                os.system(cmd)
        if config.config['services'][service_name]['reload-method'] == 'systemd-restart':
            for unit_file in config.config['services'][service_name]['systemd-units']:
                cmd = 'systemctl restart ' + unit_file
                print(cmd)
                os.system(cmd)
        if config.config['services'][service_name]['reload-method'] == 'shell':
            cmd = 'bash ' + config.config['services'][service_name]['reload_shell']
            print(cmd)
            os.system(cmd)
        if config.config['services'][service_name]['reload-method'] == 'command':
            cmd = 'bash -c \'' + config.config['services'][service_name]['command'] + '\''
            print(cmd)
            os.system(cmd)


    return True

def main():
    args = args_parser()

    if args.action == 'init':
        config_parser(args, init=True)
        action_init_handler(args)

    if args.action == 'update':
        config_parser(args, init=False)
        action_update_handler(args)

    return True

if __name__ == "__main__":
    main()