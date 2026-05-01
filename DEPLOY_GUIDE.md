# GitHub Actions 部署指南

## 迁移说明

本项目已从 Travis CI 迁移到 GitHub Actions。新的部署流程更快、更可靠，且完全免费。

## 配置步骤

### 1. 启用 GitHub Pages

前往你的 GitHub 仓库设置：

1. 进入 **Settings** → **Pages**
2. 在 **Source** 部分，选择 **GitHub Actions**
3. 保存设置

### 2. 推送代码

将更新后的代码推送到 `master` 分支：

```bash
git add .
git commit -m "Migrate from Travis CI to GitHub Actions"
git push origin master
```

### 3. 查看部署状态

1. 进入仓库的 **Actions** 标签页
2. 查看 "Deploy Hugo site to GitHub Pages" 工作流
3. 等待构建和部署完成（通常 1-2 分钟）

### 4. 访问网站

部署完成后，访问 `https://ld000.github.io/blog-hugo/` 或你的自定义域名。

## 工作流特性

- ✅ 自动触发：每次推送到 `master` 分支时自动部署
- ✅ 手动触发：可在 Actions 页面手动运行
- ✅ Hugo Extended：支持 SCSS/SASS 处理
- ✅ 子模块支持：自动拉取主题子模块
- ✅ 优化构建：启用 `--gc` 和 `--minify` 参数
- ✅ 缓存支持：加速后续构建

## 清理旧配置

部署成功后，可以删除 `.travis.yml` 文件：

```bash
git rm .travis.yml
git commit -m "Remove Travis CI configuration"
git push origin master
```

## 故障排查

### 构建失败

1. 检查 Actions 日志中的错误信息
2. 确认 Hugo 版本与本地一致
3. 验证主题子模块已正确初始化

### 页面 404

1. 确认 GitHub Pages 设置为 "GitHub Actions"
2. 检查 `baseURL` 配置是否正确
3. 等待 DNS 传播（如使用自定义域名）

### 样式丢失

1. 确认使用 Hugo Extended 版本
2. 检查 `config.toml` 中的 `baseURL` 设置
3. 验证静态资源路径正确

## 优势对比

| 特性 | Travis CI | GitHub Actions |
|------|-----------|----------------|
| 构建速度 | ~3-5 分钟 | ~1-2 分钟 |
| 配置复杂度 | 中等 | 简单 |
| 免费额度 | 有限 | 无限（公开仓库）|
| 集成度 | 外部服务 | 原生集成 |
| 维护成本 | 需要 Token | 无需额外配置 |

## 更新 Hugo 版本

编辑 `.github/workflows/deploy.yml`，修改 `HUGO_VERSION` 环境变量：

```yaml
env:
  HUGO_VERSION: 0.161.1  # 改为你需要的版本
```
