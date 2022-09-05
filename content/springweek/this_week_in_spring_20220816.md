---
title: Spring周报 - 2022.8.16
date: 2022-08-16
tags: []
---

嗨，Spring 粉丝们！欢迎来到另一个充满奇迹的 Spring 周报！已经一个星期了！有时我自己都不敢相信。你能相信已经是 8 月 16 日了吗？我女儿这周开始上学了！我们在北半球，她的暑假已经结束了。不过，夏天还有一个月和的一些变化。所以，我希望你们都尽你所能，在黑暗和寒冷的月份到来之前最大限度地享受它。

Hi, Spring fans! Welcome to another wonder-filled installment of *This Week in Spring*! It’s been a week! Sometimes I can scarcely believe it myself. And can you believe it’s August 16th already?? My daughter’s starting school this week! We’re in the northern hemisphere, and Summer break is already over and done with for her. There’s still another month and some change of summer, officially, though. So, I hope you all are doing whatever you can to maximize your enjoyment of it before the darker and colder months arrive.

Twitter 帮助我打发时间。我一直在编写一些代码，并希望在应用程序中使用 Twitter 的 OAuth 2 和 PKCE 支持，但无法完全实现。所以我联系了我的朋友（每个人的朋友，真的！）和 Spring Security 负责人 Rob Winch (@rob_winch) 寻找一些线索，他做得更好：他整理了一个示例，展示了这一切！谢谢，罗伯！我喜欢 Spring Security，一个重要的原因是它背后的团队令人惊叹、乐于助人和放纵。而且我喜欢推特（无论如何，大多数时候）。

Twitter helps me pass the time. I’ve been working on some code and wanted to use Twitter’s OAuth 2 and PKCE support in the application but couldn’t quite make it work. So I pinged my pal (everybody’s pal, really!) and Spring Security [lead Rob Winch (`@rob_winch`)](https://twitter.com/rob_winch) for some clues, and he did me one better: he put together a sample that [demonstrates it all in action](https://github.com/rwinch/spring-security-sample/tree/twitter-oauth)! Thanks, Rob! I love Spring Security and a huge reason is because of the amazing and helpful and indulgent team behind it. And I love Twitter (most of the time, anyway).

对我来说，这是 Twitter 上忙碌的一周！在上面，[我问人们在 Kubernetes 上使用什么来实现他们的可观测性](https://twitter.com/starbuxman/status/1559340838227812352?s=21&t=3Yx_5Cek8syZnby6q58Fjw)，发现[在我 25 多年的软件写作中，我什么都不知道](https://twitter.com/starbuxman/status/1559090990182322177?s=21&t=3Yx_5Cek8syZnby6q58Fjw)）等等！在这里，你这个愚蠢的读者，你可能很高兴在你的非 Twitter 生活中保持高效，不是吗？好吧，让我告诉你：你错过了！
或者，我不能强调这一点，你可能不是。这也可能是真的。所以，继续。
我们应该继续。毕竟，本周我们有一个 heckuva 综述！所以，事不宜迟……

It’s been a busy week on Twitter for me! On it, [I asked what people are using for their observability stacks on Kubernetes](https://twitter.com/starbuxman/status/1559340838227812352?s=21&t=3Yx_5Cek8syZnby6q58Fjw), figured out that [for my 25+ years in writing software, I don’t know *anything*](https://twitter.com/starbuxman/status/1559090990182322177?s=21&t=3Yx_5Cek8syZnby6q58Fjw), and so much more! And here, you silly reader you, you’ve probably been happy being all productive in your off-Twitter life, haven’t ya? Well, let me tell you: you’re missing out!

Or, and I can’t stress this enough, you’re *probably* not. That’s probably true, too. So, carry on.

And we *shall* carry on, too. After all, we’ve got one heckuva roundup this week! So, without further ado…

- Gradle Enterprise 的新版本, 2022.3, [带来一些新特性](https://gradle.com/enterprise/releases/2022.3/). 恭喜, Gradle 团队!
- (播客)In last week’s episode of the podcast, I talked with my friend, [the good Dr. Venkat Subramaniam](https://spring.io/blog/2022/08/11/a-bootiful-podcast-the-good-dr-venkat-subramaniam)
- [Apache SkyWalking 看起来是一个有趣的端到端可观测性方案，它们也有一个很好的 Spring 集成故事](https://skywalking.apache.org/docs/main/latest/en/setup/backend/spring-sleuth-setup/)
- [Blog: Enhancing Kubernetes one KEP at a Time](https://kubernetes.io/blog/2022/08/11/enhancing-kubernetes-one-kep-at-a-time/)
    
    这篇文章将重点介绍增强子团队以及您如何参与其中。
    
    KEP - Kubernetes Enhancement Proposal - Kubernetes 增强提案
    
- [Spring Boot 用注解依赖注入](https://medium.com/@naveentn/dependency-injection-with-spring-boot-annotations-c743806d7326)
- [不要称之为卷土重来：为什么 Java 仍然是冠军](https://github.com/readme/featured/java-programming-language)
- [Elastic Search with Spring Boot](https://medium.com/shoutloudz/elastic-search-with-spring-boot-357bb0f57972)
- [用 Docker Compose 执行多条命令](https://feeds.feedblitz.com/~/706318180/0/baeldung~Executing-Multiple-Commands-in-Docker-Compose)
- [介绍在 Spring Boot 里用 JBoss Drools](https://swapnilagarwal2001.medium.com/introduction-of-jboss-drool-in-spring-boot-d88c7b5b8903)
- 查看 JHipster Native 生成器 (jhipster/generator-jhipster-native) 中令人兴奋的新工作，它使构建 Spring Native 和 GraalVM 驱动的 JHipster 应用程序变得轻而易举：[v1.3.0](https://github.com/jhipster/generator-jhipster-native/releases/tag/v1.3.0)
- [Spring Boot: 什么是多请求映射](https://medium.com/shoutloudz/spring-boot-what-is-multi-request-mapping-5963baae395b)
- [Spring Cloud Dataflow 2.9.5 发布](https://spring.io/blog/2022/08/15/spring-cloud-dataflow-2-9-5-released)
- [Spring Data MongoDB – 连接配置](https://feeds.feedblitz.com/~/706480312/0/baeldung~Spring-Data-MongoDB-Configure-Connection)
- [Spring Tools 4.15.3 发布](https://spring.io/blog/2022/08/12/spring-tools-4-15-3-released)
- [Spring Web Flow 3.0 M1 发布](https://spring.io/blog/2022/08/10/spring-web-flow-3-0-m1-released)
- 这是我在五年多前做过的一次演讲，但它展示了当时很常见的很多事情。如果您是最近加入 Spring Boot 社区的一大群人，这可能会很有趣。这里有两个我感兴趣的方面：有多少事情改进了，有多少事情保持不变。享受! *[The Bootiful Application](https://www.youtube.com/watch?v=kGDcroKVECk)*
- [VMware 在开源领域的励志女性：聚焦 Olga Maciaszek-Sharma，她是 Spring Cloud 团队的传奇成员](https://blogs.vmware.com/opensource/2022/08/11/vmwares-inspirational-women-in-open-source-spotlight-on-olga-maciaszek-sharma/)