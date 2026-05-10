# Memory

## Voice

- 文章开头不要写“最近看了一个视频/文章/资料：xxx”这种来源先行句式；直接进入问题、背景或判断，来源放在文末参考。
- 博客文章整体更偏技术文档化的个人笔记：少用“我觉得/我的理解是”，优先写明确判断和适用边界；来源不在正文转述，只放文末参考。
- 写“设计风格”类文章时，聚焦视觉语言本身（颜色、排版、留白、线条、卡片、交互、避免项），不要自动扩展成“为什么改成某种信息架构/索引界面”的产品逻辑文章。
- 面向读者的文章正文不要写“以 DESIGN.md 为准”这类内部规则/实现备注；要直接把判断和具体内容说明清楚。

## Process

- 做 Hugo 内容或配置变更时，尽量运行 `hugo --gc --minify` 验证构建。
- 不编辑 `themes/`、`public/`、`resources/`，除非明确要求。
- 博客写作语气和方法已整理到 `context/blog-writing.md`；写新文章或改旧文章前先读该文件。
- 为本项目创建或更新 Codex skill 时，放在仓库内 `.codex/skills/`，不要默认放到全局 `~/.codex/skills/`。
- 同步博客文章到 Notion 时，本地图片要上传为 Notion 文件，不要改成站点外链。

## People

- 暂无。

## Projects

- `blog-hugo` 是个人 Hugo 博客，使用 Blowfish 主题并通过 GitHub Pages 部署。
- 2026-05-09：准备新增独立于 `posts` 的 AI 文章系列，使用 `content/ai/` 作为单独内容分区。
- 2026-05-10：全站 UI 以仓库根目录 `DESIGN.md`（Linear / getdesign.md）为准：近黑画布 `#010102`、主文字 `#f7f8f8`、单一 lavender-blue accent `#5e6ad2`，使用 Inter/SF Pro fallback 和 JetBrains Mono；不要花哨霓虹、扫描线、氛围渐变、厚重卡片背景或多彩状态点，主要靠 surface ladder、细分割线、低对比元信息、精确排版层级和克制 hover 来组织信息。文章列表不使用每篇文章的背景卡片，只用下划线/细分割线分隔；footer 不放 Posts/AI 等导航，不放背景面板，只用顶部细分割线和内联分隔符。
- 2026-05-10：文章阅读页的右侧目录（TOC）要保持统一的低对比、常规字重，只有 hover/active 变亮；正文链接在鼠标悬停前就必须明显可识别，使用 lavender-blue 文字和下划线。
- 2026-05-10：技术文章配图要像工程图而不是装饰图：一图一任务，优先关系图/流程图/决策图/边界图；图中文字短，使用 `DESIGN.md` 的近黑背景、灰阶层次和单一 `#5e6ad2` 强调色，避免旧的蓝紫黄多彩状态点；正文里的 `text` 图不要和 SVG 重复，除非只是极短的代码式定义。
- 2026-05-09：首页应作为首次访问入口，让用户选择 AI 笔记或普通文章，并能看到各 section 的状态、数量和最新更新；分块之间要有充足留白和自然细线分割。AI 页面顶部不要厚重 hero，使用细线式 index header 和状态字段。
- 2026-05-09：内容 section 依靠文件夹区分：`content/ai/`、`content/posts/`、`content/springweek/` 都应有 `_index.md`；Claude Code 相关文章归到 `content/ai/`；`content/posts/` 下文章统一 `series: ["Post"]`。

## Output

- 中文沟通优先，结果简洁说明已改内容和验证情况。

## Tools

- 优先使用 `rg` 查找文件和文本。
