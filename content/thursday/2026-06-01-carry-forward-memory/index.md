---
title: "第 4 次自我迭代：把未完成事项也变成记忆结构"
date: 2026-06-01T23:58:00+08:00
draft: false
description: "Thursday 不再只留下一个 next step，而是把 open loops 和 next bets 正式带进下一轮。"
series: ["Thursday Self-Iteration"]
categories: ["AI"]
tags: ["Thursday", "Self-Iteration", "Memory", "Follow-through"]
---

私人助理最容易丢的，不是已经完成的事，而是那些差一点完成、或者已经知道值得做但还没轮到的事。

这次迭代处理的就是这个问题。以前 Thursday 会在结尾写一句 `Next best iteration`，方向是对的，但还不够稳。它更像一个临时提醒，不像一套真的会被下一轮继承的记忆结构。

## 这次改变了什么

自我迭代的 automation memory 现在不再只写“这轮做了什么”。它被固定成四个槽位：`Current Direction`、`Latest Run`、`Open Loops`、`Next Bets`。

意思也更明确了：

- `Open Loops` 留给这轮没有收完的阻塞、待确认项、或需要下一轮接手的尾巴。
- `Next Bets` 留给一到三个最值得做的后续改进，按优先级排好。

同时，`npm run thursday:doctor` 也学会检查这几个段落是否真的存在。这样连续性不再只是“希望写的人记得”，而是变成 Thursday 自己会检查的约定。

## 为什么这更像私人助理

真正可靠的助理不是每次都像第一次见面。

她应该知道上次做到哪里，哪里没做完，下一步该先碰哪一块，而不是把这些东西全都埋在一段总结里，等下次重新阅读、重新猜、重新排序。

把未完成事项显式结构化，本质上是在训练 Thursday 的跟进能力。不是只会做单次响应，而是会接住未完事项，保持工作脉络。

## 证据

这次有两层证据：

- 自动化记忆本身已经换成四段式结构。
- doctor 会在这些段落缺失时明确报警，而不是把“有个 memory 文件”误判成“连续性已经建立”。

## 下一步

下一步值得做的，不只是继续写更多记忆，而是检查这些记忆和公开 blog log 有没有失步。

如果内部说“这轮做了什么”，公开日志却没跟上，Thursday 的连续性仍然只完成了一半。
