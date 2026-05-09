---
title: 从 Travis CI 迁移到 GitHub Actions：Hugo 博客部署现代化实践
date: 2026-05-01T22:32:24+08:00
tags: ["GitHub Actions", "Travis CI", "Hugo", "CI/CD"]
categories: ["技术"]
series: ["DevOps 与工具"]
description: 记录 Hugo 博客从 Travis CI 迁移到 GitHub Actions 的完整过程，构建速度提升 50%，配置更简单，完全免费，包含详细的配置示例和最佳实践建议
---

最近对博客的部署流程进行了现代化改造，将持续集成和部署从 Travis CI 迁移到了 GitHub Actions。这篇文章记录了整个迁移过程和背后的思考。

<!-- more -->

## 为什么要迁移？

### Travis CI 的现状

Travis CI 曾经是开源项目 CI/CD 的首选，但近年来情况发生了变化：

- **免费额度限制**：对开源项目的免费支持大幅缩减
- **构建速度慢**：平均需要 3-5 分钟才能完成部署
- **配置复杂**：需要手动下载 Hugo、配置 Token 等
- **维护成本高**：需要在外部服务中管理配置

### GitHub Actions 的优势

相比之下，GitHub Actions 提供了更好的体验：

- ⚡ **更快的构建速度**：1-2 分钟即可完成部署
- 🆓 **完全免费**：公开仓库无限制使用
- 🔧 **配置简单**：原生集成，无需额外 Token
- 🚀 **生态丰富**：大量现成的 Actions 可用
- 📊 **更好的可视化**：直接在仓库中查看构建状态

## 迁移过程

### 1. 分析现有配置

首先查看原有的 `.travis.yml` 配置：

```yaml
language: node_js
env:
  HUGO=0.161.1
  URL=https://github.com/gohugoio/hugo/releases/download

script:
    - mkdir hugo
    - cd hugo
    - curl -L "${URL}/v${HUGO}/hugo_extended_${HUGO}_Linux-64bit.tar.gz" | gunzip | tar xvf -
    - cd ..
    - ./hugo/hugo

deploy:
  provider: pages
  skip_cleanup: true
  local_dir: public
  github_token: $GITHUB_TOKEN
  keep_history: true
  on:
    branch: master
```

可以看到，Travis CI 需要手动下载 Hugo 二进制文件，配置相对繁琐。

### 2. 创建 GitHub Actions 工作流

在 `.github/workflows/deploy.yml` 创建新的工作流：

```yaml
name: Deploy Hugo site to GitHub Pages

on:
  push:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.161.1
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: '${{ env.HUGO_VERSION }}'
          extended: true

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Build with Hugo
        env:
          HUGO_CACHEDIR: ${{ runner.temp }}/hugo_cache
          HUGO_ENVIRONMENT: production
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 3. 关键改进点

#### 使用官方 Actions

不再手动下载 Hugo，而是使用 `peaceiris/actions-hugo@v3`，这个 Action 会自动处理 Hugo 的安装和缓存。

#### 支持 Hugo Extended

通过 `extended: true` 参数，确保安装的是 Hugo Extended 版本，支持 SCSS/SASS 处理。

#### 自动处理子模块

```yaml
submodules: recursive
fetch-depth: 0
```

自动拉取 Hugo 主题子模块，并获取完整的 Git 历史（用于 `.GitInfo` 和 `.Lastmod`）。

#### 构建优化

```bash
hugo --gc --minify
```

- `--gc`：清理未使用的缓存文件
- `--minify`：压缩 HTML/CSS/JS，减小文件体积

#### 动态 baseURL

```yaml
--baseURL "${{ steps.pages.outputs.base_url }}/"
```

自动获取 GitHub Pages 的 URL，无需硬编码。

#### 手动触发支持

```yaml
workflow_dispatch:
```

除了自动触发，还支持在 Actions 页面手动运行工作流。

### 4. 配置 GitHub Pages

在仓库设置中：

1. 进入 **Settings** → **Pages**
2. 将 **Source** 改为 **GitHub Actions**
3. 保存设置

### 5. 清理旧配置

迁移成功后，可以删除 `.travis.yml` 文件：

```bash
git rm .travis.yml
git commit -m "Remove Travis CI configuration"
git push origin master
```

## 效果对比

| 指标 | Travis CI | GitHub Actions | 改进 |
|------|-----------|----------------|------|
| 构建时间 | 3-5 分钟 | 1-2 分钟 | **50-60% 提升** |
| 配置复杂度 | 需要手动下载 Hugo | 使用现成 Action | **大幅简化** |
| 免费额度 | 有限 | 无限（公开仓库）| **完全免费** |
| 集成度 | 外部服务 | 原生集成 | **无缝体验** |
| 维护成本 | 需要管理 Token | 自动处理权限 | **零维护** |

## 最佳实践建议

### 1. 版本固定

在工作流中明确指定 Hugo 版本：

```yaml
env:
  HUGO_VERSION: 0.161.1
```

避免使用 `latest`，确保构建的可重复性。

### 2. 使用缓存

GitHub Actions 会自动缓存 Hugo 安装，加速后续构建。

### 3. 并发控制

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

确保同一时间只有一个部署任务运行，避免冲突。

### 4. 环境隔离

```yaml
environment:
  name: github-pages
```

使用 GitHub Environments 功能，可以添加部署保护规则。

### 5. 权限最小化

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

只授予必要的权限，提高安全性。

## 故障排查

### 构建失败

如果遇到构建失败，检查以下几点：

1. **Hugo 版本**：确认版本与本地一致
2. **子模块**：验证主题子模块已正确初始化
3. **Extended 版本**：如果使用 SCSS，必须启用 `extended: true`

### 页面 404

如果部署后页面显示 404：

1. 确认 GitHub Pages 设置为 "GitHub Actions"
2. 检查 `baseURL` 配置
3. 等待几分钟让 CDN 更新

### 样式丢失

如果样式无法加载：

1. 确认使用 Hugo Extended 版本
2. 检查静态资源路径
3. 验证 `baseURL` 设置正确

## 总结

从 Travis CI 迁移到 GitHub Actions 是一次非常值得的升级：

- **性能提升**：构建速度提升 50% 以上
- **成本降低**：完全免费，无需担心额度
- **体验改善**：配置更简单，维护更轻松
- **生态更好**：丰富的 Actions 市场

如果你的项目还在使用 Travis CI 或其他传统 CI 服务，强烈建议尝试迁移到 GitHub Actions。对于 Hugo 博客来说，这个过程非常简单，只需要创建一个工作流文件即可。

## 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Hugo 官方文档](https://gohugo.io/documentation/)
- [peaceiris/actions-hugo](https://github.com/peaceiris/actions-hugo)
- [GitHub Pages 部署指南](https://docs.github.com/en/pages)

---

完整的配置文件和迁移指南可以在我的 [GitHub 仓库](https://github.com/ld000/blog-hugo) 中找到。
