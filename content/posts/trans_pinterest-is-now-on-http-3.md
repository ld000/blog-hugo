---
title: "[翻译]Pinterest 现在已支持 HTTP/3 协议"
date: 2023-03-13
tags: [""]
---

> 原文：[https://medium.com/pinterest-engineering/pinterest-is-now-on-http-3-608fb5581094](https://medium.com/pinterest-engineering/pinterest-is-now-on-http-3-608fb5581094)

Liang Ma | Software Engineer, Core Eng; Scott Beardsley | Engineering Manager, Traffic; Haowei Yuan | Software Engineer, Traffic

![https://void.oss-cn-beijing.aliyuncs.com/img/202303131136650.png](https://void.oss-cn-beijing.aliyuncs.com/img/202303131136650.png)

图1 - Pinterest 的HTTP/3

**现在 Pinterest 正在使用 HTTP/3**。我们已经在多个 CDN 边缘网络上启用了 HTTP/3，并升级了客户端应用程序的网络堆栈以支持新协议。这使我们能够跟上行业趋势。最重要的是，更快速和更可靠的网络改进了用户的体验和业务指标。

# 背景

网络性能（如延迟和吞吐量）对 Pinterest 用户的体验至关重要。

2021年，Pinterest 的一群客户端网络爱好者开始考虑在 Pinterest 上采用 HTTP/3（曾用名QUIC），从 traffic/CDN 到客户端应用程序。我们在2022年全年都在开发，我们已经实现了我们的初始目标（2023年及以后还需继续工作）。

术语:

- ***HTTP/3***: 下一代 HTTP 协议。它已经被IETF工作组稳定并最终确定。
- ***QUIC***: 由 Chromium/Google 为UDP上的HTTP创建；后来提交给IEFT进行标准化（HTTP/3）。

# **HTTP/3 怎么帮助 Pinterest**

HTTP/3 是一种现代的 HTTP 协议，与 HTTP/2 相比有许多优点，包括但不限于：

- 与 HTTP/2 相比没有 TCP 排队阻塞问题
- 可以在 IP 地址之间迁移连接，这对移动设备非常有用
- 能够改变/调整丢失检测和拥塞控制
- 减少连接时间（0-RTT，而 HTTP/2 仍需要 TCP 三次握手）
- 更有效地处理大负载用例，如图像下载、视频流等。

**这些进步很适合Pinterest的场景** - *加快连接建立（第一个请求的第一个字节的时间），改进拥塞控制（我们有大型媒体），无TCP阻塞（同时下载多个文件），并在 Pinner 设备网络/ IP更改时继续进行正在进行的请求。* 因此，当 Pinners 在 Pinterest 平台上进行灵感创作时，他们将拥有更快、更可靠的体验。

# 在 Pinterest 采用 HTTP/3

## **策略**

**安全和指标优先。虽然 Pinterest 专注于快速执行，但采用 HTTP/3 的方法必须经过深思熟虑。首先，我们升级了客户端网络堆栈，并为每种流量类型（例如图像、视频）创建了端到端的 A/B 测试。然后，在启用 CDN 和客户端的 HTTP/3 之前，我们进行了广泛的实验。**

挑战：

在 CDN 和客户端应用程序上启用 HTTP/3 的过程并不简单，主要有以下几个原因：

- 对于 Web 应用程序，一些浏览器已经支持 HTTP/3 或 QUIC。虽然这些浏览器使用 HTTP/3，但可能存在兼容性问题，这可能会破坏 Pinterest 的 Web 应用程序。
- 新的 iOS 版本（从 iOS 15 开始）已经支持 QUIC，除非我们在服务器端禁用 QUIC，否则我们无法通过代码来控制。
- 我们的 CDN 供应商处于 HTTP/3 支持的不同阶段。随着我们逐渐启用 CDN 的 HTTP/3，我们的多 CDN 边缘网络在相当长的一段时间内只能部分支持 HTTP/3，这使得在切换 CDN 流量时确保可靠性和性能成为一个有趣的问题（[链接](https://github.com/httpwg/http-extensions/issues/1673)）。

解决方案：

- 首先，我们创建了一个 A/B 域级（CDN）测试，其中克隆了一个域以启用 HTTP/3，并彻底验证了客户端（包括 Web）。例如：在图像 HTTP/3 验证计划中，我们使用 [i2.pinimg.com](http://i2.pinimg.com) 验证 HTTP/3 的图像流量。
- 对于多 CDN 问题，我们选择了相对较短的 [Alt-Svc](https://httpwg.org/specs/rfc7838.html) TTL，以接近 DNS 记录 TTL，并尝试在这些 CDN 上配置相同的协议集。
- 进行了广泛的测试，以验证使用最常用的浏览器时跨 CDN 的 HTTP/3 行为。
- 在 A/B 测试通过后，我们逐个 CDN 启用了 HTTP/3，然后使用带功能标志的网络客户端让客户端应用程序来控制 HTTP/3，这更安全，同时也可以收集和比较指标。

## 现在的状态

**我们已经在关键的网络流量类型上启用了 HTTP/3，并升级/利用移动客户端的网络栈来利用 HTTP/3。**

*网络流量*：我们在我们的多 CDN 边缘网络上为主要的 Pinterest 生产域启用了 HTTP/3。

*客户端*：

- *Web* 将在符合条件的浏览器和网络流量上免费获得它。
- *iOS - 图像/API 流量* 由 [Cronet](https://chromium.googlesource.com/chromium/src/+/master/components/cronet/) + HTTP/3 提供服务。现在，70%的 iOS 图像流量使用 HTTP/3。
- *iOS 的本地网络堆栈* 可以在网络流量侧启用之后利用 HTTP/3。苹果的 HTTP/3 采用率继续年复一年地提高。通过使用 HTTP/3（通过AVPlayer），我们在我们的视频指标中看到了这方面的显著好处。
- *Android 视频* 通过 Exoplayer+Cronet 利用了 HTTP3。

# **Showcase**

**我们的分析表明，HTTP/3（以及Cronet）已经改善了核心网络指标（往返延迟和可靠性）。改善延迟/吞吐量对于大型媒体功能（如视频、图像）至关重要。更快、更可靠的网络也能够提高用户参与度指标。**

**视频指标**

视频特写 GVV（iOS：苹果网络 + HTTP/3）：

![https://void.oss-cn-beijing.aliyuncs.com/img/202303131139385.png](https://void.oss-cn-beijing.aliyuncs.com/img/202303131139385.png)

视频特写 GVV（Android：Exoplayer + Cronet + HTTP/3）：

![https://void.oss-cn-beijing.aliyuncs.com/img/202303131140768.png](https://void.oss-cn-beijing.aliyuncs.com/img/202303131140768.png)

图2 - HTTP3 对视频启动延迟的直接影响

**参与度指标（iOS）**：HTTP/3 的直接影响

![https://void.oss-cn-beijing.aliyuncs.com/img/202303131141925.png](https://void.oss-cn-beijing.aliyuncs.com/img/202303131141925.png)

图3 — HTTP3 对用户参与度的影响

**网络指标**

- 往返延迟（毫秒）：

![https://void.oss-cn-beijing.aliyuncs.com/img/202303131142967.png](https://void.oss-cn-beijing.aliyuncs.com/img/202303131142967.png)

图4 —— HTTP/3 之前和之后的网络请求往返延迟

注意：1）从客户端测量，从请求发送到响应接收；2）基于在2022年第三季度使用苹果网络（HTTP/2）和2023年第一季度启用Cronet（HTTP/3）收集的一周网络日志。

- *可靠性*也有所提高。

# 未来工作

我们将继续投资 HTTP/3 以实现持续影响，包括:

- 扩大 HTTP/3 覆盖范围；在 Android 上探索其他网络堆栈。
- 进一步提高 HTTP/3 采用率；将最大年龄值设置为更高值。
- 尝试各种拥塞控制算法。
- 探索 0-RTT 连接建立。

*要了解Pinterest的工程技术，请查看我们的[Engineering Blog](https://medium.com/pinterest-engineering)，并访问我们的[Pinterest Labs](https://www.pinterestlabs.com/)网站。要了解Pinterest的生活，请访问我们的[Careers](https://www.pinterestcareers.com/)页面。*