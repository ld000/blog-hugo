# Blog Hugo

[![Deploy Status](https://github.com/ld000/blog-hugo/actions/workflows/deploy.yml/badge.svg)](https://github.com/ld000/blog-hugo/actions/workflows/deploy.yml)
[![Hugo Version](https://img.shields.io/badge/Hugo-0.161.1-blue.svg)](https://gohugo.io)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)

个人技术博客，使用 Hugo 静态站点生成器构建。访问地址：[https://ld000.space](https://ld000.space)

## ✨ 特性

- 🚀 使用 GitHub Actions 自动部署
- 🎨 基于 MemE 主题的优雅设计
- 📱 响应式布局，支持移动端
- 🌓 深色/浅色模式切换
- 💬 Gitalk 评论系统
- 📊 Google Analytics 统计
- ⚡ 构建优化（minify + gc）
- 🏷️ 完善的分类和标签体系
- 📝 所有文章包含 SEO 友好的 description

## 📚 内容分类

博客包含 **32 篇技术文章**，按以下 Series 组织：

### 技术文章
- **Java 开发** (3篇) - Java 核心技术、JVM、集合框架
- **Spring 生态** (1篇) - Spring Boot 部署与配置
- **数据库与中间件** (4篇) - MySQL、Redis、MyBatis、Sharding-Proxy
- **DevOps 与工具** (3篇) - CI/CD、GitHub Actions、自动化工具
- **网络与架构** (3篇) - Traefik、微服务、单点登录
- **Go 开发** (1篇) - Go 语言与 ORM
- **前端开发** (1篇) - 响应式设计

### 翻译与周报
- **翻译文章** (4篇) - Spring AOP、技术设计文档、Tumblr 架构、HTTP/3
- **Spring 周报** (10篇) - Spring 官方周报中文翻译
- **AI 手记** (2篇) - AI 工具使用与实践

## 🚀 部署

本项目使用 GitHub Actions 自动部署到 GitHub Pages。

每次推送到 `master` 分支时，会自动触发构建和部署流程（约 1-2 分钟完成）。

详细配置步骤请查看 [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)。

## 💻 本地开发

```bash
# 安装 Hugo (macOS)
brew install hugo

# 克隆仓库（包含子模块）
git clone --recursive git@github.com:ld000/blog-hugo.git

# 如果已克隆，初始化子模块
git submodule update --init --recursive

# 启动开发服务器
hugo server -D

# 构建生产版本
hugo --gc --minify
```

## 📝 创建文章

```bash
# 创建新文章
hugo new posts/my-new-post.md

# 编辑文章
# 文章位于 content/posts/ 目录下
```

## 🎨 主题

使用 [MemE](https://github.com/reuixiy/hugo-theme-meme) 主题。

更新主题：

```bash
git submodule update --remote --rebase
```

## 📄 License

内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh) 许可协议。