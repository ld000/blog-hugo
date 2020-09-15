---
title: Mac下用CLion debug MySQL5.7源码
date: 2020-03-26
tags: ["java", "CLion", "MySQL"]
---

## 编译安装 MySQL

首先从 github 下载 mysql 源码

```shell
    https://github.com/mysql/mysql-server
``` 

接下来编译安装

```shell
    // 进到源码目录
    cd /Users/d/c/mysql-server-5.7
    
    // cmake
    cmake \
    -DCMAKE_INSTALL_PREFIX=/Users/d/c/mysql_build \
    -DMYSQL_DATADIR=/Users/d/c/mysql_build/data \
    -DSYSCONFDIR=/Users/d/c/mysql_build \
    -DMYSQL_UNIX_ADDR=/Users/d/c/mysql_build/data/mysql.sock \
    -DWITH_DEBUG=1 \
    -DDOWNLOAD_BOOST=1 \
    -DWITH_BOOST=/Users/d/c/boost \
    -DWITH_SSL=/usr/local/opt/openssl@1.1
    
    // install
    make && make install
    
    // 初始化数据库
    cd /Users/d/c/mysql_build
    bin/mysqld --basedir=/Users/d/c/mysql_build --datadir=/Users/d/c/mysql_build/data --initialize-insecure
```

`-DDOWNLOAD_BOOST=1 -DWITH_BOOST=/Users/d/c/boost` 这两个参数指定 boost 路径，之后会自动下载 boost。

`-DWITH_SSL=/usr/local/opt/openssl@1.1` 指定 openssl 路径，不指定有可能会报以下错误

```shell
    Cannot find appropriate system libraries for WITH_SSL=system.
    Make sure you have specified a supported SSL version.
    Valid options are :
    system (use the OS openssl library),
    yes (synonym for system),
    </path/to/custom/openssl/installation>
    
    CMake Error at cmake/ssl.cmake:63 (MESSAGE):
    Please install the appropriate openssl developer package.
```

## 配置CLion

打开 mysql 源码目录，修改 cmake 配置

![https://void.oss-cn-beijing.aliyuncs.com/img/20200326121222.jpg](https://void.oss-cn-beijing.aliyuncs.com/img/20200326121222.jpg)

```shell
    -DCMAKE_INSTALL_PREFIX=/Users/d/c/mysql_build -DMYSQL_DATADIR=/Users/d/c/mysql_build/data -DSYSCONFDIR=/Users/d/c/mysql_build -DMYSQL_UNIX_ADDR=/Users/d/c/mysql_build/data/mysql.sock -DWITH_DEBUG=1 -DDOWNLOAD_BOOST=1 -DWITH_BOOST=/Users/d/c/boost -DWITH_SSL=/usr/local/opt/openssl@1.1
```

之后选择 mysqld，然后点击 debug 按钮就可以开始调试了。

![https://void.oss-cn-beijing.aliyuncs.com/img/20200326122342.jpg](https://void.oss-cn-beijing.aliyuncs.com/img/20200326122342.jpg)