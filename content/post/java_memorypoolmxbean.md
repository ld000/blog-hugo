---
title: MemoryPoolMXBean 各内存池名字
date: 2020-04-13
tags: ["java"]
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

## Metaspace

### JDK7

ParallelGC:  `PS Perm Gen`

ConcMarkSweepGC: `CMS Perm Gen`

SerialGC: `Perm Gen`

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