---
title: MacOS 用 automater 自动备份安装的软件列表
date: 2019-09-15
tags: ["automater"]
---

不知道有没有人经历过重装系统后需要把所有软件都重装一遍的痛苦，而且很有可能落下几个软件没装，等到用的时候才发现，重新下载再重新配置，时间不知不觉就没了。 

所以要是能把安装过的软件列表都备份下来就好了。mac 上正好就有这样一个软件 `brew`。

## 准备

`brew` 是 Mac 下的一个包管理工具，类似 Ubuntu 的 apt，可以方便的安装各种软件。

> [https://brew.sh/](https://brew.sh/)

靠一行命令就可以安装：

```sh
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

安装好后就可以靠命令来快速安装软件了

```sh
    # 安装不带界面的命令行下的工具或三方库
    brew install wget
    # 安装带界面的应用程序
    brew cask install firefox
```

还可以安装 `mas`来管理 App Store 下载的软件

> [https://github.com/mas-cli/mas](https://github.com/mas-cli/mas)

```sh
    brew install mas
```

之后我们就可以执行命令将安装过的软件列表导出了

```sh
    brew bundle dump --force --describe
```

执行上面命令后会导出个 Brewfile 文件，里面大概长这样

```sh
    tap "homebrew/bundle"
    tap "homebrew/cask"
    tap "homebrew/core"
    
    brew "bazaar"
    
    cask "docker"
    
    mas "iMovie 剪辑", id: 408981434
```

记录了通过 brew 和 App Store 安装的软件，之后可以通过 `brew bundle --file="./Brewfile"`导入。

## Automator 配置

Automator 是 masOS 下的一个自动操作工具

> “自动操作”能让电脑上的大部分操作自动进行。有了“自动操作”，要创建自动化操作，您不必了解复杂的编程或脚本语言，只需使用“自动操作”资源库中数百个可用操作中的任意一些，便可以创建工作流程。这些操作能与各种 App 和 macOS 的部分程序进行互动。工作流程可以简单到只有一个操作，也可以包含许多操作以执行一系列复杂的任务。

> [https://support.apple.com/zh-cn/guide/automator/welcome/mac](https://support.apple.com/zh-cn/guide/automator/welcome/mac)

我们可以通过 Automator 创建个自动备份 Brewfile 的程序，还可以同步到 GitHub 上防止丢失。

首先创建一个日历提醒

![](/img/automator_brewfile/automator1.png)

在左侧资源库中选择运行 Shell 脚本

![](/img/automator_brewfile/automator2.png)

然后填写上导出 Brewfile 的命令

![](/img/automator_brewfile/automator3.png)

```sh
    cd ~/workspace/github-self/mac-init
    # 导出 Brewfile，注意 brew 命令要写全路径
    /usr/local/bin/brew bundle dump --force --describe
    
    # 以下是提交 GitHub
    git add --all
    git commit -m "update brewfile"
    git pull
    git push
```

写好后可以点击右上角的运行按钮来测试下，打开结果可以看到运行输出

![](/img/automator_brewfile/automator4.png)

之后 ctrl+s 保存，输入文件名后会自动创建一个日历提醒，重复里选上每周，之后就可以让电脑自动备份安装过的软件列表了。

![](/img/automator_brewfile/automator5.png)

下次在新电脑上就可以执行`brew bundle --file="./Brewfile"`来恢复安装过的软件了，是不是很方便呢。

如果怕忘了命令还可以写个脚本来自动执行，比如我的 [`https://github.com/ld000/mac-init`](https://github.com/ld000/mac-init)。