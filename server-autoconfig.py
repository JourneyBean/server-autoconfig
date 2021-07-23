#!/bin/python3

# version 0.3.5

import yaml
import argparse
import os
import subprocess
from pathlib import Path
import time
import filecmp

# config and default config
class config:
    instance = 'default'
    config_path = '/etc/server-autoconfig/config.yml'
    data_path_prefix = '/var/cache/server-autoconfig/data_'
    debug_level = 0

    arg_no_restart = False
    arg_specify_service = False
    arg_full_restart = False

    config = []

class consts:
    DEBUG_LEVEL_ERROR = 0
    DEBUG_LEVEL_WARNING = 1
    DEBUG_LEVEL_NOTICE = 2
    DEBUG_LEVEL_INFO = 3

#################### UTILS ####################

# leveled debug control
def debug_output( level, message ):
    if level == consts.DEBUG_LEVEL_ERROR:
        message = "[ERR] " + message
    elif level == consts.DEBUG_LEVEL_WARNING:
        message = "[WARN] " + message
    elif level == consts.DEBUG_LEVEL_NOTICE:
        message = "[NOTE] " + message
    else:
        message = "[INFO] " + message

    if ( config.debug_level >= level ):
        print(message)

def getConfigPath():
    return config.config_path

def getDataPath():
    return config.data_path_prefix + config.instance

def getRepoPath():
    return getDataPath() + '/repo'

def isSystemdUnitExists(name):

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

def isNoReload():
    return config.arg_no_restart

def createDirectoryByName(filename):
    p,f = os.path.split(filename)
    dir = Path(p)
    if dir.exists():
        if not dir.is_dir():
            debug_output(consts.DEBUG_LEVEL_ERROR, "directory: [ERR] conflict file name at " + p + ", excepted directory.")
    else:
        cmd = "mkdir -p " + p
        debug_output(consts.DEBUG_LEVEL_INFO, cmd)
        os.system(cmd)

# Check local repository existence
def isDataDirectoryCreated():
    dir =  Path(getDataPath())
    return dir.is_dir()

# git referred tools
def checkoutRepoBranch(branch):
    debug_output(consts.DEBUG_LEVEL_INFO, "Checkout branch " + branch)
    cmd = 'cd ' + getRepoPath() + ' && git checkout ' + branch
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def newRepoBranch(branch):
    debug_output(consts.DEBUG_LEVEL_INFO, "Create branch " + branch)
    cmd = 'cd ' + getRepoPath() + ' && git branch ' + branch
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def commitRepo(message):
    debug_output(consts.DEBUG_LEVEL_INFO, "Commit to local repo")
    cmd = 'cd ' + getRepoPath() + ' && git add --all && git commit -m "' + message + '"'
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def revertRepo():
    debug_output(consts.DEBUG_LEVEL_INFO, "Revert changes at local repo")
    cmd = 'cd ' + getRepoPath() + ' && git reset --hard HEAD^'
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def clearRepoFiles():
    debug_output(consts.DEBUG_LEVEL_INFO, "Delete all repo files")
    cmd = 'cd ' + getRepoPath() + ' && git rm -r *'
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def resetRepo():
    debug_output(consts.DEBUG_LEVEL_INFO, "Reset repo")
    cmd = 'cd ' + getRepoPath() + ' && git reset --hard'
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

def pushRepo(branch):
    debug_output(consts.DEBUG_LEVEL_INFO, "Push repo")
    cmd = 'cd ' + getRepoPath() + ' && git checkout ' + branch + " && git push --set-upstream origin " + branch
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

#################### COMPONENTS ####################

# Handle command line config and config file
def args_parser():

    debug_output(consts.DEBUG_LEVEL_INFO, "args_parser: Ready to parse args")

    # setup argparse
    argp = argparse.ArgumentParser(
        'server-autoconfig',
        description='''
                    Auto config application tool using 
                    git repo.
                    '''
    )

    argp.add_argument(
        'action',
        choices=['update', 'rollback', 'download', 'backup', 'push', 'clear'],
        metavar='{update|rollback|download|backup|push|clear}',
        help='Update: download, apply to system and backup to local. \
                Rollback: revert settings to the last stage. \
                Download: download repo only. \
                Backup: backup current system configs to local only. \
                Push: push local backup to upstream repo. \
                Clear: clean all data, including local backups.'
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
        '--full-restart',
        action='store_true',
        help='Force restart all services when update, regardless of wether config file the same or not.'
    )

    args = argp.parse_args()

    return args

# Read and store config to memory
def config_init( args ):

    # TO-DO: Abstracting whole config into a class, using methods to obtain configs.

    # get config file path from default or parameters
    if args.config:
        config.config_path = args.config
    
    debug_output(consts.DEBUG_LEVEL_INFO, "Using config file: " + config.config_path)

    # parse config file
    try:
        f = open(config.config_path, 'r', encoding='utf-8')
    except IOError:
        debug_output(consts.DEBUG_LEVEL_ERROR, 
                    "Failed to open config file: " + config.config_path)
        exit(1)
    else:
        cfg_raw = f.read()
        config.config = yaml.safe_load(cfg_raw)
        f.close()

    # apply debug_level from config file or parameter overriding defaults
    if config.config['basic'].get('debug-level'):
        config.debug_level = config.config['basic']['debug-level']
    if args.debug:
        config.debug_level = consts.DEBUG_LEVEL_INFO
    debug_output(consts.DEBUG_LEVEL_NOTICE, "Debug level set to " + str(config.debug_level))

    # apply instance, data path, debug level if exists from config file overriding defaults
    if config.config['basic'].get('instance'):
        config.instance = config.config['basic']['instance']
    debug_output(consts.DEBUG_LEVEL_NOTICE, "Instance name: " + config.instance)

    if config.config['basic'].get('data-path-prefix'):
        config.data_path_prefix = config.config['basic']['data-path-prefix']
    debug_output(consts.DEBUG_LEVEL_NOTICE, "Data directory prefix: " + config.data_path_prefix)

    debug_output(consts.DEBUG_LEVEL_NOTICE, "Using data path: " + getDataPath())

    # apply --no-restart from args
    if args.no_restart:
        config.arg_no_restart = True
        debug_output(consts.DEBUG_LEVEL_NOTICE, "--no-restart, will not restart services")
    
    # apply --full-restart from args
    if args.full_restart:
        config.arg_full_restart = True
        debug_output(consts.DEBUG_LEVEL_NOTICE, "--full-restart, will restart all services")

    return


# Check services in config before actions
# only check restart methods. File pair checking will performed when updating
def config_checker( args ):

    services = config.config['services']

    # check each service in services section of config file.
    for service_name in services:

        debug_output(consts.DEBUG_LEVEL_INFO, "config_checker: Checking section config/services/" + service_name)

        # check by reload-method
        if services[service_name].get('restart-method'):

            # is systemd-reload or systemd-restart
            if (services[service_name]['restart-method'] == 'systemd-restart' or 
                services[service_name]['restart-method'] == 'systemd-reload'):

                # check systemd unit files
                if (services[service_name].get('systemd-units')):

                    for unit_file in services[service_name]['systemd-units']:
                        if not isSystemdUnitExists(unit_file):
                            debug_output(consts.DEBUG_LEVEL_ERROR, "Systemd unit " +
                                         unit_file + " Not found in section " +
                                         "config/services/" + service_name + "/systemd-units")
                            exit(1)
                        else:
                            debug_output(consts.DEBUG_LEVEL_INFO, "config_checker: [OK] Found " +
                                        "config/services/" + service_name + "/systemd-units/" + unit_file)

                else:
                    debug_output(consts.DEBUG_LEVEL_ERROR, 'No systemd units found in section' +
                                 "config/services/" + service_name)
                    exit(1)

            # is command
            elif ( services[service_name]['restart-method'] == 'command' ):
                    
                if not services[service_name].get('restart-command'):
                    debug_output(consts.DEBUG_LEVEL_ERROR, "No restart-command found in section" +
                                 "config/services/" + service_name)
                else:
                    debug_output(consts.DEBUG_LEVEL_INFO, "config_checker: [OK] Found config/services/" + service_name + "/restart-command")

            # is other
            else:
                debug_output(consts.DEBUG_LEVEL_ERROR, "Invalid parameter found in " +
                                 "config/services/" + service_name + "/reload-method section")
                exit(1)
        else:
            # no reload-method section. ERROR.
            debug_output(consts.DEBUG_LEVEL_ERROR, "No reload-method section found in " + 
                         "config/services/" + service_name + " section")
            exit(1)

    return

def filepair_checker():

    debug_output(consts.DEBUG_LEVEL_INFO, "[filepair_checker]: Checking files")

    services = config.config['services']
    for service_name in services:
        if not services[service_name].get('files'):
            debug_output(consts.DEBUG_LEVEL_ERROR, "Could not find file section in " +
                         "config/services/" + service_name)
            exit(1)
        # check filepairs existence
        else:
            for file_pair in services[service_name]['files']:
                repo_file = file_pair[:file_pair.index(':')]
                repo_file = getRepoPath() + '/' + repo_file
                target_file = file_pair[file_pair.index(':')+1:]
                if not os.path.exists(repo_file):
                    debug_output(consts.DEBUG_LEVEL_ERROR, "Could not find file from local repo: " +
                                 repo_file + " in section " + "config/services/" + service_name + "/files")
                    exit(1)
                else:
                    debug_output(consts.DEBUG_LEVEL_INFO, "config/services/" + service_name + ": Found " + repo_file )

def filepair_copy( isReverse ):

    # for each services
    services = config.config['services']
    for service_name in services:
        for file_pair in services[service_name]['files']:
            repo_file = file_pair[:file_pair.index(':')]
            repo_file = getRepoPath() + '/' + repo_file
            target_file = file_pair[file_pair.index(':')+1:]
            if not isReverse:
                # target file missing, or two files are not the same
                if (not os.path.exists(target_file)) or (not filecmp.cmp(repo_file, target_file)):
                    # copy file
                    createDirectoryByName(target_file)
                    cmd = 'cp ' + repo_file + ' ' + target_file
                    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
                    os.system(cmd)
                    # set flag
                    services[service_name]['isRestartNeeded'] = True
                # target file not missing, and two files are the same
                else:
                    # do nothing
                    pass
            else:
                # force full backup, no matter exists or the same
                createDirectoryByName(repo_file)
                cmd = 'cp ' + target_file + ' ' + repo_file
                debug_output(consts.DEBUG_LEVEL_INFO, cmd)
                os.system(cmd)

    return

# pull or clone remote repo to local cache
def prepare_repo():

    debug_output(consts.DEBUG_LEVEL_INFO, "[prepare_repo] Prepare local repo")

    # prepare repo: pull or clone
    if os.path.exists(getDataPath() + '/initialized'):
        # checkout to upstream branch
        checkoutRepoBranch(config.config['upstream']['git-pull-branch'])
        resetRepo()
        # git pull
        debug_output(consts.DEBUG_LEVEL_INFO, "Initialized. Pull from repo " + config.config['upstream']['git-addr'])
        cmd = 'cd ' + getRepoPath() + ' && git pull'
        debug_output(consts.DEBUG_LEVEL_INFO, cmd)
        os.system(cmd)
    else:
        debug_output(consts.DEBUG_LEVEL_INFO, "Not initialized. Clone from repo " + config.config['upstream']['git-addr'])
        cmd = "git clone " + config.config['upstream']['git-addr'] + ' ' + getRepoPath()
        debug_output(consts.DEBUG_LEVEL_INFO, cmd)
        os.system(cmd)
        cmd = "touch " + getDataPath() + '/initialized'
        debug_output(consts.DEBUG_LEVEL_INFO, cmd)
        os.system(cmd)
    
    # checkout branch
    debug_output(consts.DEBUG_LEVEL_INFO, "Checkout from branch " + config.config['upstream']['git-pull-branch'])
    cmd = 'cd ' + getRepoPath() + ' && git checkout ' + config.config['upstream']['git-pull-branch']
    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
    os.system(cmd)

    return

# copy current filepairs to branch
def backup_current_config():

    debug_output(consts.DEBUG_LEVEL_INFO, "[backup_current_config]: Backing up")

    newRepoBranch(config.config['upstream']['git-backup-branch'])
    checkoutRepoBranch(config.config['upstream']['git-backup-branch'])
    clearRepoFiles()
    filepair_copy(1) # system -> repo
    commitRepo("bcakup at " + time.asctime( time.localtime(time.time())))

# copy files to system
def update_config():

    debug_output(consts.DEBUG_LEVEL_INFO, "[update_config]: Updating config to system")

    checkoutRepoBranch(config.config['upstream']['git-pull-branch'])
    resetRepo()
    filepair_copy(0) # repo -> system

def restart_service():

    debug_output(consts.DEBUG_LEVEL_INFO, "[restart_service]: Restarting services")

    # for each services
    services = config.config['services']
    for service_name in services:

        if services[service_name].get('isRestartNeeded') or config.arg_full_restart:

            # before
            if services[service_name].get('restart-before'):
                debug_output(consts.DEBUG_LEVEL_INFO, services[service_name]['restart-before'])
                os.system(services[service_name]['restart-before'])

            # restart
            if (services[service_name]['restart-method'] == 'systemd-restart' or 
                services[service_name]['restart-method'] == 'systemd-reload'):
                for unit_file in services[service_name]['systemd-units']:
                    cmd = ""
                    if (services[service_name]['restart-method'] == 'systemd-restart'):
                        cmd = "systemctl restart " + unit_file
                    else:
                        cmd = "systemctl reload " + unit_file
                    debug_output(consts.DEBUG_LEVEL_INFO, cmd)
                    os.system(cmd)
            elif (services[service_name]['restart-method'] == 'command'):
                debug_output(consts.DEBUG_LEVEL_INFO, services[service_name]['restart-command'])
                os.system(services[service_name]['restart-command'])

            # after
            if services[service_name].get('restart-after'):
                debug_output(consts.DEBUG_LEVEL_INFO, services[service_name]['restart-after'])
                os.system(services[service_name]['restart-after'])

            if services[service_name].get('isRestartNeeded'):
                del services[service_name]['isRestartNeeded']

        else:
            debug_output(consts.DEBUG_LEVEL_INFO, "Skipping restarting " + service_name)

def clear_cache():
    debug_output(consts.DEBUG_LEVEL_WARNING, "Will delete cache including backups!")
    cmd = "rm -rf " + getDataPath()
    str = input("Will exectute: " + cmd + ". Proceed?(Y/n)" )
    if str == 'Y':
        os.system(cmd)

#################### MAIN ####################

def main():
    args = args_parser()

    config_init(args)
    config_checker(args)

    if args.action == "update":
        prepare_repo()              # clone or pull repo
        filepair_checker()          # check repo files to see if matches config
        backup_current_config()     # copy system config to repo in backup branch
        update_config()             # copy repo config to system
        if not args.no_restart:
            restart_service()       # restart system service

    elif args.action == "backup":
        backup_current_config()

    elif args.action == "download":
        prepare_repo()

    elif args.action == "push":
        pushRepo(config.config['upstream']['git-backup-branch'])

    elif args.action == "rollback":
        # change to backup branch
        checkoutRepoBranch(config.config['upstream']['git-backup-branch'])
        # copy backup branch to system
        filepair_copy(0)
        # revert git repo
        revertRepo()
        # restart system service
        if not args.no_restart:
            restart_service()

    elif args.action == "clear":
        str = input("This will delete all data include local backup files. Proceed? (Y/n)")
        if (str == 'Y'):
            clear_cache()
        else:
            pass

    return True

if __name__ == "__main__":
    main()
