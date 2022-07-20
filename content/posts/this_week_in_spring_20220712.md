---
title: Spring周报 - 2022.7.12
date: 2022-07-12
tags: []
---

Hi，Spring 粉丝们！欢迎收看另一期的 Spring 周报！你好吗？本周，我在阳光明媚的华盛顿州西雅图给您写这个，我们将在那里进行 SpringOne Tour 系列的下一部分。再次看到所有这些有趣和友好的面孔并见到人们真是太有趣了，其中许多人在疫情之前我就再也没有见过！在这里见到一些来自微软和 AWS 等大型云公司的朋友，我也很开心。了解人们如何使用 Spring 的最新和最强大的技术来构建针对这些云平台的惊人系统和软件总是很有趣的。

Hi, Spring fans! Welcome to another installment of *This Week in Spring*! How are you? This week I’m writing you from sunny Seattle, Washington, where we’re having our next installment of the SpringOne Tour series. It’s been a ton of fun seeing all these fun and friendly faces again and getting to see people, many of whom I haven’t seen since before the pandemic! I’ve also had a lot of fun seeing some friends from some of the big cloud companies here, Microsoft and AWS. It’s always interesting to learn how people are using the latest and greatest from Spring to build amazing systems and software targeting these cloud platforms.

本周我们有很多内容要介绍，所以让我们开始吧！

We’ve got a lot to cover this week so let’s dive right into it!

- (播客)In last week’s podcast, I talked to [Kubernetes contributor and fellow Tanzu Developer Advocate Leigh Capili](https://spring.io/blog/2022/07/07/a-bootiful-podcast-kubernetes-contributor-and-fellow-tanzu-developer-advocate-leigh-capili)
- [用 OpenTelemetry, Spring Cloud Sleuth, Kafka 和 Jaeger 做分布式链路追踪](https://betterprogramming.pub/distributed-tracing-with-opentelemetry-spring-cloud-sleuth-kafka-and-jaeger-939e35f45821)
- [Kubernetes 里 Ingress 和 Load Balancer](https://feeds.feedblitz.com/~/701779764/0/baeldung~Ingress-vs-Load-Balancer-in-Kubernetes) 对比
- [用 Spring Annotations 实例化同一个 Class 的多个 Bean](https://feeds.feedblitz.com/~/702046988/0/baeldung~Instantiating-Multiple-Beans-of-the-Same-Class-with-Spring-Annotations)
- [Java 14 Records 和 Lombok 对比](https://feeds.feedblitz.com/~/702186894/0/baeldung~Java-Record-vs-Lombok)
- 我整理了这个小例子，感谢 Reactor 负责人 Simon Baslé，展示了如何使用 Project Reactor 中的 `expand` 扩展运算符处理分页： [反应式应用程序中的分页](https://joshlong.com/jl/blogpost/pagination_in_a_reactive_application.html)。它着眼于如何在新数据（在数据分页场景中）可用时优雅地扩展反应流的内容。
- [Spring Shell 2.1.0-RC1 发布](https://spring.io/blog/2022/07/07/spring-shell-2-1-0-rc1-is-now-available)
- [推送 Docker 镜像到自建镜像仓库](https://feeds.feedblitz.com/~/702188110/0/baeldung~Pushing-a-Docker-Image-to-a-SelfHosted-Registry)
- [Spring for Apache Kafka 2.9.0-RC1 发布](https://spring.io/blog/2022/07/07/spring-for-apache-kafka-2-9-release-candidate-available)
    - 使用 kafka-clients 3.2.0
    - 非堵塞重试 bootstrapping 现在更加健壮
    - 新的错误处理模式
        
        默认情况下，发生错误后，`DefaultErrorHandler` 对上次轮询的剩余记录执行搜索，并在下一次轮询时从代理重新获取它们。错误率高且 `max.poll.records` 较大的情况下，这可能会对网络造成不必要的压力。出于这个原因，错误处理程序有一个新属性 `seekAfterError`，当设置为 `false` 时，剩余的记录保留在内存中，消费者暂停下一次轮询（或者如果错误处理程序配置为使用 `ContainerPausingBackOffHandler` 则进行多次轮询）。
        
    - 暂停容器
        
        默认情况下，当您 `pause()` 容器时，它实际上会在上一次轮询的所有记录都已处理后暂停。此版本添加了 `pauseImmediate` 容器属性，当该属性为 `true` 时，容器在处理当前记录后暂停。
        
- [这篇 Apache Maven 生存指南非常有趣，至少对我来说是这样](https://github.com/rfichtner/maven-survival-guide)！
