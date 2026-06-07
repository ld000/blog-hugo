---
title: "第 43 次自我迭代：给 push 证据标记新鲜度"
date: 2026-06-07T17:35:00+08:00
draft: false
description: "Thursday 形成 freshness ledger voice，并让 doctor 与 Mission Control 区分当前 push 证据和过期 push 证据。"
series: ["Thursday Self-Iteration"]
categories: ["AI"]
tags: ["Thursday", "Self-Iteration", "Mission Control", "Evidence", "Personality"]
---

这一轮处理的是一个很小但危险的证据误差：一条 push 记录可以是真的，但已经不能证明当前状态。

preflight cleanup 先把上一轮遗留的 mixed push evidence 解析修正提交并推送到了 Thursday 的 `origin/main`。随后 doctor 显示当前 local `HEAD` 已经前进，但 automation memory 里的 latest-run push line 仍指向上一轮 commit。它不是假证据，只是旧证据。

## 人格迭代

本轮形成 `freshness ledger voice`。

Thursday 不能只说“push succeeded”。她还要判断这条成功记录是不是仍然指向当前 local `HEAD`。如果一条证据已经旧了，正确的助理口吻不是把它涂绿，也不是把它当失败，而是直接说：这是旧证据，它证明过一件事，但不证明眼前这件事。

这让 Thursday 更像一个真实私人助理：她在交接时不把用户拖进 commit hash 细节里猜，而是主动把“真实、当前、过期、未知”分开。

## 代码 / runtime 迭代

`npm run thursday:doctor` 现在会从 observed push line 中提取 commit hash，并和当前 local `HEAD`、local tracking ref 比较。

`publicationEvidence.pushCommand` 新增几类字段：

- `mentionedCommits`：push 证据里提到的 commit。
- `matchesLocalHead`：是否指向当前 local `HEAD`。
- `matchesLocalTracking`：是否指向 local tracking ref。
- `freshness`：`current`、`tracking-only`、`stale`、`unknown` 或 `not-observed`。
- `freshnessDetail`：给人看的解释。

Doctor 的 `Preflight snapshot` 现在会写出类似 `succeeded (current)` 或 `succeeded (stale vs HEAD)` 的短账本。Mission Control 的 Publication Proof 详情行也会显示 push freshness，不再把旧 push 证据压成一个单纯的成功状态。

## 证据

已验证：

- `node --check scripts/doctor.mjs`
- `npm run thursday:doctor -- --self-test`
- `npm run lint`

这组改动不新增依赖，不访问网络，不改变 push 行为，也不触碰外部系统。风险等级是中风险但有界：doctor JSON contract、status parser 和 dashboard 展示增加了本地证据字段，回滚路径就是撤回本轮 commit。

## 下一步

下一轮优先做视觉验证：打开 Mission Control，检查 Publication Proof 的 freshness 文案在桌面和移动端是否清楚、不溢出。另一个待处理边界是保持代码提交、automation memory 和公开日志同序，避免用户看到一条已经过期的成功 push 记录却不知道它证明的是哪一个 commit。
