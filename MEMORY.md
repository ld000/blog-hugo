# Memory

## Voice

- 暂无固定偏好。

## Process

- 做 Hugo 内容或配置变更时，尽量运行 `hugo --gc --minify` 验证构建。
- 不编辑 `themes/`、`public/`、`resources/`，除非明确要求。

## People

- 暂无。

## Projects

- `blog-hugo` 是个人 Hugo 博客，使用 Blowfish 主题并通过 GitHub Pages 部署。
- 2026-05-09：准备新增独立于 `posts` 的 AI 文章系列，使用 `content/ai/` 作为单独内容分区。
- 2026-05-09：全站视觉方向固定为参考 Linear / Linear Now/Craft 的极简深色系统界面：核心背景 `#111111`、主文字 `#FFFFFF`，使用 Instrument Sans / Inter 和 JetBrains Mono；不要花哨霓虹、不要厚重卡片背景、不要绿色状态点，主要靠留白、细分割线、低对比元信息、精确排版层级和克制 hover 来组织信息。文章列表不使用每篇文章的背景卡片，只用下划线/细分割线分隔；footer 不放 Posts/AI 等导航，不放背景面板，只用顶部细分割线和内联分隔符。
- 2026-05-09：首页应作为首次访问入口，让用户选择 AI 笔记或普通文章，并能看到各 section 的状态、数量和最新更新；分块之间要有充足留白和自然细线分割。AI 页面顶部不要厚重 hero，使用细线式 index header 和状态字段。
- 2026-05-09：内容 section 依靠文件夹区分：`content/ai/`、`content/posts/`、`content/springweek/` 都应有 `_index.md`；Claude Code 相关文章归到 `content/ai/`；`content/posts/` 下文章统一 `series: ["Post"]`。

## Output

- 中文沟通优先，结果简洁说明已改内容和验证情况。

## Tools

- 优先使用 `rg` 查找文件和文本。
