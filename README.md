# Blog Hugo

[![Deploy Status](https://github.com/ld000/blog-hugo/actions/workflows/deploy.yml/badge.svg)](https://github.com/ld000/blog-hugo/actions/workflows/deploy.yml)

个人博客，使用 Hugo 静态站点生成器构建。

## 🚀 部署

本项目使用 GitHub Actions 自动部署到 GitHub Pages。

每次推送到 `master` 分支时，会自动触发构建和部署流程。

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