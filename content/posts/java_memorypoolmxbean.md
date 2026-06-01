---
title: MemoryPoolMXBean 各内存池名字
date: 2020-04-13T00:00:00+08:00
tags: ["Java", "JVM", "内存管理", "垃圾回收"]
series: ["Java 开发"]
description: 整理 Java 各版本中 MemoryPoolMXBean 内存池的名称，包括 Code Cache、Metaspace、SerialGC、ParallelGC、CMS、G1GC、ZGC 等不同垃圾回收器的内存池命名规则
---

MemoryPoolMXBean 是 Java 内存池的管理接口，如果要做内存监控，就会用到这个类。

下面整理下各版本内存池的名字。

## Code Cache

### JDK7, JDK8

```
    Code Cache
```

### JDK9 后

```
    CodeHeap 'non-nmethods'
    CodeHeap 'profiled nmethods'
    CodeHeap 'non-profiled nmethods'
```

## Perm Gen

### JDK7

ParallelGC:  `PS Perm Gen`

ConcMarkSweepGC: `CMS Perm Gen`

SerialGC: `Perm Gen`

## Metaspace

### JDK8 之后

```
    Metaspace
    Compressed Class Space
```

## SerialGC

```
    Eden Space
    Survivor Space
    Tenured Gen
```

## ParallelGC + ParallelOldGC

```
    PS Eden Space
    PS Survivor Space
    PS Old Gen
```

## ConcMarkSweepGC + ParNewGC

JDK9后 deprecated，JDK14后移除

```
    Par Eden Space
    Par Survivor Space
    CMS Old Gen
```

## G1GC

```
    G1 Eden Space
    G1 Survivor Space
    G1 Old Gen
```

## ZGC

```
    ZHeap
```