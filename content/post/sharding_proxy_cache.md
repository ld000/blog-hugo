---
title: sharding-proxy 连接缓存导致 fullGC 内存不释放
date: 2020-05-25
tags: ["java", "sharding-proxy"]
---

sharding-proxy版本：3.1.0

之前公司使用了 sharding-proxy 作为数据库分库分表代理。

在运行一段时间后，出现大量连接超时，触发了线上报警。观察内存发现内存几乎占满了，频繁触发 fullGC。内存无法释放。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710103616.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710103616.png)

一时无法确定原因，先将流量都切到一台备用 sharding-proxy，然后执行 `jmap` 导出内存到MAT里进行分析。

```bash
jmap -dump,format=b,file=proxy.hprof [pid]
```

可以看到1.8G的内存都被 Guava 的 cache 占用了。猜测是用了强引用，缓存没有释放。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710114017.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710114017.png)

点击Details查看详细信息，可以看到是 `ChannelRegistry` 这个类里的缓存。

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710115710.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200710115710.png)

接下来分析下代码，

```java
public final class ChannelRegistry {
    
    private static final ChannelRegistry INSTANCE = new ChannelRegistry();
    
    // TODO :wangkai do not use cache, should use map, and add unregister feature
    public final Cache<String, Integer> connectionIds = CacheBuilder.newBuilder().build();
    
    /**
     * Get instance of channel registry.
     *
     * @return instance of channel registry
     */
    public static ChannelRegistry getInstance() {
        return INSTANCE;
    }
    
    /**
     * Put connection id by channel ID.
     *
     * @param channelId netty channel ID
     * @param connectionId database connection ID
     */
    public void putConnectionId(final String channelId, final int connectionId) {
        connectionIds.put(channelId, connectionId);
        // 自己加的日志
        log.info("put channel cache, key: {}, value: {}", channelId, connectionId);
    }
    
    /**
     * Get connection id by channel ID.
     *
     * @param channelId netty channel ID
     * @return connectionId database connection ID
     */
    public int getConnectionId(final String channelId) {
        Integer result = connectionIds.getIfPresent(channelId);
        Preconditions.checkNotNull(result, String.format("Can not get connection id via channel id: %s", channelId));
        return result;
    }
}
```

默认构造器创建了一个强引用缓存，里面缓存了netty连接和对应的数据库连接。只有 put 方法，没有释放方法。

每次有新的netty连接，都会创建一个缓存元素，造成这个缓存越来越大，而且不会释放。

为了确定是这个问题，我在 `putConnectionId` 方法里加了日志部署测试

![https://raw.githubusercontent.com/ld000/git-resources/master/img/20200818084548.png](https://raw.githubusercontent.com/ld000/git-resources/master/img/20200818084548.png)

部署后，发现日志里频繁的 put cache，可以确定就是这个原因导致内存无法释放。连接创建这么频繁是因为运维在前面挂了一层 Aliyun SLB 负载，SLB 会频繁的创建探活连接。

## 修复

修改也比较简单，sharding-proxy 分为 backend 和 frontend 两部分。backend 负责与 MySQL 示例交互，默认使用 JDBC 连接，不会使用这个缓存，不需要修改。要修改的只有 frontend 部分，这部分负责和连接 sharding-proxy 的客户端交互，使用的 Netty。

首先修改 `io.shardingsphere.shardingproxy.runtime.ChannelRegistry`，添加一个释放缓存的方法。

```java
public void invalidate(final String channelId) {
    connectionIds.invalidate(channelId);
}
```

然后修改 `io.shardingsphere.shardingproxy.frontend.common.FrontendHandler`，这是连接处理的父类，继承的是Netty的ChannelInboundHandlerAdapter。我们修改 `channelInactive` 方法，添加一个剩余资源处理逻辑，并添加一个抽象方法供子类继承。

```java
@Override
@SneakyThrows
public final void channelInactive(final ChannelHandlerContext context) {
    context.fireChannelInactive();
    backendConnection.close(true);
    ChannelThreadExecutorGroup.getInstance().unregister(context.channel().id());
    // 添加的资源处理逻辑
    inactive(context);
}

// 添加的抽象方法
protected abstract void inactive(final ChannelHandlerContext context);
```

最后，修改`FrontendHandler`的子类，继承刚刚的抽象方法。

```java
@Override
protected void inactive(ChannelHandlerContext context) {
    ChannelRegistry.getInstance().invalidate(context.channel().id().asShortText());
}
```

这样，连接断开后就会自动释放缓存了。