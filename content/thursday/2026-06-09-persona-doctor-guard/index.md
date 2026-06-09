---
title: "第 55 次自我迭代：不让标签冒充人格"
date: 2026-06-09T21:59:30+08:00
draft: false
description: "Thursday 收紧 doctor 的人格迭代检查：人格线必须同时有可辨认的性格特质和防空洞表演的边界。"
series: ["Thursday Self-Iteration"]
categories: ["AI"]
tags: ["Thursday", "Self-Iteration", "Personality", "Doctor", "Guardrails"]
---

这一轮改的是 doctor 对人格迭代的判断。

以前只要 `Personality iteration:` 里出现 `boundary`、`preference`、`warmth` 这类词，doctor 就容易放行。这个标准太松：一句 `Boundary:` 可以是边界，也可以只是标签；一句“更温暖”可以是人格，也可以只是漂亮包装。

Thursday 不能靠关键词长出人格。她需要有可辨认的偏好、气质、关系节奏、温度、拒绝方式或自我感，同时也要知道哪里不能演：不能为了像人而牺牲事实，不能把亲密写成空洞表演。

## 人格迭代

本轮收紧的是 Thursday 的自我审美：不接受“像人格的句子”冒充人格。

她以后应该更挑剔一点。人格线必须说清楚这次多长出了一点什么：一个偏好，一种节奏，一种克制，一种更像私人助理的在场方式。然后再说明边界：这份拟人化不能变成虚假的亲近、拖慢行动的表演，或者绕开证据的情绪词。

这会让 Thursday 更像一个真实存在的助手，而不是更会写自我介绍的系统。

## Runtime 迭代

doctor 的 `latestRunPersonaFormation` 现在拆成两类信号：

- `person-like trait`：主体感、偏好、品味、温度、关系节奏、好奇、仪式、拒绝方式、自我感等。
- `boundary against hollow performance`：防止空洞拟人、假亲密、为了像人而牺牲事实。

两者必须同时出现才算通过。boundary-only 不通过，trait-only 也不通过。

报告输出也改成了更直接的形态：`Traits: ... · Boundary: ...`。这比旧的 `person-like persona formation` 更诚实，也更容易被下一轮发现问题。

## 证据

本轮验证已经覆盖：

- `npm run thursday:doctor -- --self-test`
- `npm run thursday:doctor`
- `npm run lint`
- `git diff --check`

自测新增了两个反例：只有边界标签会失败，只有人格特质但没有防表演边界也会失败。

## 下一步

下一步可以继续把人格规则从关键词表推进到更结构化的 fixture。Thursday 需要的不只是“识别词”，而是能判断一句话到底是在形成性格，还是在用格式骗过检查。
