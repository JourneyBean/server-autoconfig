# Server Autoconfig

使用Python编写的服务器配置自动应用脚本(v0.3.5)

## 主要功能

服务器中配置文件太多，人工管理起来太麻烦，总是疲于在不同目录中切换？使用这个脚本，我相信能为你减轻这一负担！

现在你要做的仅仅是将系统配置文件存储到一个安全的Git服务器上（本地Git仓库、SSH远程主机的Git仓库等Git能克隆的都可以），在目标设备下载此脚本，编辑脚本附带的配置文件。这样，配置更改操作只需在服务器进行，更改完成后，再于目标设备执行该脚本，只需一行命令，即可轻松下拉并应用配置。

将服务器配置文件存储在git服务器上，使用本脚本即可自动将配置文件下载并复制到指定位置，还可自动重启服务。

- 一个配置文件即可管理服务器上的所有配置
- 支持自动重启服务，支持重启服务前后执行自定义脚本
- 支持配置自动备份，并可上传至主仓库
- 支持配置一键回滚

## 安装

```
cd server-autoconfig
chmod +x ./install.sh
sudo ./install.sh
```

你也可以手动复制文件到系统的bin文件夹并赋予运行权限，并创建数据文件夹。

但一般建议执行安装脚本，因为可以检测必要的包是否安装。

### 卸载

```
cd server-autoconfig
chmod +x ./uninstall.sh
sudo ./uninstall.sh
```

你也可以直接手动删除

## 配置

编辑配置文件（脚本安装方式的配置文件在`/etc/server-autoconfig/config.yml`）。以下是示例配置：

`config.yml`

``` yaml
basic:
  instance: default
  data-path-prefix: '/var/cache/server-autoconfig/data_'
  debug-level: 0

upstream:
  git-addr: https://my-git-server/serverconfig.git
  git-pull-branch: main
  git-backup-branch: backup-router

services:

  dnsmasq:
    restart-before: 'ifdown eth1'
    restart-after: 'bash -c "/var/test.sh"'
    restart-method: systemd-reload
    systemd-units:
      - dnsmasq.service
    files:
      - /router/dnsmasq/dnsmasq.conf:/etc/dnsmasq/dnsmasq.conf
  
  my_service:
    restart-method: command
    restart-command: 'systemctl restart smb.service && systemctl reload nmb.service'
    files:
      - /router/samba/samba.conf:/etc/samba/samba.conf
      - /router/samba/custom.conf:/var/spool/samba/custom.conf
```

## 使用方法

### 下拉配置

简单地，你可以使用`server-autoconfig update`一键将上游配置部署到本机，并自动重启更改的服务，同时会对本机之前的配置进行备份。备份数据存储在本地。

如果不需要重启服务，可以添加`--no-restart`选项；如果需要强制重启所有服务，使用`--full-reload`选项。

### 回滚配置

使用`servr-autoconfig rollback`一键回滚到上一次配置状态，并自动重启更改的服务。`--no-restart`也可用。

### 推送备份

若需要将备份数据推送到上游仓库，可以使用`server-autoconfig push`推送。

### 清除数据

如果需要清除所有本地数据（**包括本地备份**），可以使用`server-autoconfig clear`清除。

### 其他

- 仅下载仓库：`server-autoconfig download`
- 仅备份到本地：`server-autoconfig backup`
- 指定配置文件：添加 `-c /path/to/file.yml` 选项
- debug： `--debug`

## 一些技巧

### 多个实例

可以同时为脚本创建多个实例，只需复制配置文件并修改basic/instance节内容为不同值即可。不同实例的存储仓库完全分开。实际上，每个实例都独享不同的数据文件夹，位于`/var/cache/server-autoconfig/data_xxxx`，其中`xxxx`即表示配置的实例名称。

但需要注意的是，如果需要多个实例同时上传备份配置（以及多个主机共享同一上游仓库），最好将备份分支名称区分开来，否则可能出现上传问题。

### 双向修改（合并备份至主分支）

可以直接在目标设备修改系统配置文件，然后通过此脚本上传到备份分支，再合并到主线，实现配置的上传。

### 自动检查并下拉配置

配合Systemd，每隔一定时间自动下拉配置，具体使用方法如下：

```sh
sudo systemctl start server-autoconfig.timer
sudo systemctl enable server-autoconfig.timer
```

或者也可指定配置文件使用：

```sh
sudo systemctl start server-autoconfig@my-autoconfig.timer
sudo systemctl enable server-autoconfig@my-autoconfig.timer
```
上面的例子将使用/etc/server-autoconfig/my-autoconfig.yml配置文件。

若使用crontab，按照systemd文件里的配置写即可。

### 保存Git私有仓库的帐号密码

进入配置的本地仓库文件夹（一般在`/var/cache/server-autoconfig/data_xxxx/repo`），执行：

```
sudo git config --local credential.helper store --file /var/cache/server-autoconfig/data_xxxx/credentials
```

然后手动执行一次`server-autoconfig update`，填入帐号密码即可。

> **注意：对于托管在公共服务的私有Git仓库，建议使用密钥(或Token)作为密码登陆，以确保安全性。**

> **注意：不指定凭据存储路径也可工作，但是同时运行多个实例时可能会出现问题，因为若不指定凭据路径，则所有凭据都默认存储在~/.git-credentials，导致不同仓库的密钥产生混淆**