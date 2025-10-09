# 🚀 部署检查清单

使用此清单确保顺利部署项目到生产环境。

---

## 📋 部署前准备

### 代码准备

- [ ] 所有代码已提交到 Git 仓库
- [ ] 代码已推送到 GitHub/GitLab
- [ ] 没有未提交的更改
- [ ] 分支为 `main` 或 `master`

### 配置文件检查

- [ ] `vercel.json` 已创建并配置正确
- [ ] `backend/Procfile` 已创建
- [ ] `backend/railway.json` 已创建
- [ ] `backend/Dockerfile` 已创建
- [ ] `.gitignore` 正确配置（包含 `.env`, `node_modules` 等）

### 文档准备

- [ ] 已阅读 [QUICK_DEPLOY.md](./QUICK_DEPLOY.md)
- [ ] 已阅读 [DEPLOYMENT.md](./DEPLOYMENT.md)
- [ ] 已阅读 [ENV_VARIABLES.md](./ENV_VARIABLES.md)

---

## 🔧 后端部署（Railway）

### 账号准备

- [ ] 已注册 [Railway](https://railway.app) 账号
- [ ] 已连接 GitHub 账号
- [ ] 已验证邮箱

### 项目创建

- [ ] 创建新项目
- [ ] 从 GitHub 导入仓库
- [ ] 选择正确的仓库和分支

### 服务配置

- [ ] Root Directory 设置为 `backend`
- [ ] Start Command 设置为：`uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] 服务名称已设置（如：`ai-api-backend`）

### 数据库配置

- [ ] 已添加 MySQL 服务
- [ ] MySQL 服务在同一项目中
- [ ] 已获取数据库连接信息

### 环境变量配置

- [ ] `DATABASE_URL` = `${{MySQL.DATABASE_URL}}`
- [ ] `SECRET_KEY` = （强随机字符串）
- [ ] `ALGORITHM` = `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` = `30`
- [ ] `OPENROUTER_API_KEY` = （你的 API Key）
- [ ] `OPENROUTER_BASE_URL` = `https://openrouter.ai/api/v1`
- [ ] `AI_MODEL` = `anthropic/claude-3-5-sonnet-20241022`
- [ ] `ALLOWED_ORIGINS` = （Vercel 前端域名，稍后填写）
- [ ] `ENVIRONMENT` = `production`
- [ ] `DEBUG` = `False`

### 部署验证

- [ ] 部署成功（无错误日志）
- [ ] 服务状态为 "Active"
- [ ] 已生成公开域名
- [ ] 记录域名：`https://_____.railway.app`
- [ ] 可以访问 `/health` 端点
- [ ] 返回正确的健康状态 JSON

### 数据库初始化

- [ ] 在 Railway Shell 中运行 `python init_db.py`
- [ ] 数据库表创建成功
- [ ] 默认用户创建成功

---

## 🎨 前端部署（Vercel）

### 账号准备

- [ ] 已注册 [Vercel](https://vercel.com) 账号
- [ ] 已连接 GitHub 账号
- [ ] 已完成身份验证

### 项目导入

- [ ] 点击 "Add New Project"
- [ ] 选择正确的 Git 仓库
- [ ] 点击 "Import"

### 框架配置

- [ ] Framework Preset: `Next.js`
- [ ] Root Directory: `ai-api-platform` ✅ **重要**
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `.next`
- [ ] Install Command: `npm install`
- [ ] Node.js Version: `18.x`

### 环境变量配置

- [ ] `NEXT_PUBLIC_API_URL` = `https://_____.railway.app`（Railway 域名）
- [ ] `NEXT_PUBLIC_WS_URL` = `wss://_____.railway.app`（可选）
- [ ] `NODE_ENV` = `production`

### 部署验证

- [ ] 部署成功（无构建错误）
- [ ] 已生成域名
- [ ] 记录域名：`https://_____.vercel.app`
- [ ] 可以访问前端页面
- [ ] 页面正常加载（无空白）

---

## 🔄 后端 CORS 更新

### 更新 Railway 配置

- [ ] 回到 Railway 后端服务
- [ ] 进入 Variables 标签
- [ ] 更新 `ALLOWED_ORIGINS` = `https://_____.vercel.app,http://localhost:3000`
- [ ] 保存更改
- [ ] 等待自动重新部署
- [ ] 重新部署成功

---

## ✅ 功能测试

### 基础功能

- [ ] 可以访问前端首页
- [ ] 页面布局正常显示
- [ ] 无控制台错误（F12 检查）
- [ ] API 请求无 CORS 错误

### 用户认证

- [ ] 可以打开注册页面
- [ ] 可以成功注册新用户
- [ ] 可以打开登录页面
- [ ] 可以使用新账号登录
- [ ] 登录后跳转到仪表板
- [ ] 用户信息正确显示

### 任务功能

- [ ] 可以打开创建任务页面
- [ ] 可以填写任务信息
- [ ] 可以成功创建任务
- [ ] 可以查看任务列表
- [ ] 可以打开任务详情页面
- [ ] 任务状态正确显示

### 管理员功能（如果是管理员账号）

- [ ] 可以访问管理员页面
- [ ] 可以查看所有用户
- [ ] 可以查看所有任务
- [ ] 可以审核任务

### 通知功能

- [ ] 通知图标显示正常
- [ ] 可以查看通知列表
- [ ] 未读通知数量正确
- [ ] 可以标记通知为已读

---

## 🔍 性能和安全检查

### 性能

- [ ] 首次加载时间 < 3秒
- [ ] API 响应时间 < 1秒
- [ ] 图片正常加载
- [ ] 无明显卡顿

### 安全

- [ ] HTTPS 正常工作
- [ ] SSL 证书有效
- [ ] 无混合内容警告
- [ ] 敏感信息未暴露在客户端代码中
- [ ] `.env` 文件未提交到 Git

### SEO 和元数据

- [ ] 页面标题正确显示
- [ ] Meta 描述已设置
- [ ] Favicon 正常显示

---

## 📊 监控和日志

### Vercel

- [ ] 可以查看部署历史
- [ ] 可以查看构建日志
- [ ] 可以查看函数日志（如有）
- [ ] Analytics 已启用（可选）

### Railway

- [ ] 可以查看部署历史
- [ ] 可以查看应用日志
- [ ] 可以查看数据库状态
- [ ] Metrics 显示正常

---

## 🎉 部署完成后

### 文档更新

- [ ] 更新 README.md 中的部署链接
- [ ] 记录生产环境 URL
- [ ] 更新项目文档

### 团队通知

- [ ] 通知团队成员部署完成
- [ ] 分享前端 URL
- [ ] 分享 API 文档 URL（后端 `/docs`）
- [ ] 提供测试账号（如需要）

### 备份

- [ ] 保存环境变量配置（安全位置）
- [ ] 保存数据库连接信息
- [ ] 保存域名和部署信息

### 后续优化（可选）

- [ ] 配置自定义域名
- [ ] 设置 CDN 加速
- [ ] 配置监控告警
- [ ] 设置自动备份
- [ ] 优化性能指标

---

## 🐛 故障排查

如果遇到问题，按以下顺序检查：

### 1. 前端无法访问

- 检查 Vercel 部署状态
- 查看构建日志
- 确认 Root Directory 配置

### 2. API 请求失败

- 检查 `NEXT_PUBLIC_API_URL` 配置
- 确认后端服务运行中
- 访问后端 `/health` 端点
- 检查 CORS 配置

### 3. 数据库连接错误

- 检查 `DATABASE_URL` 格式
- 确认 MySQL 服务运行中
- 测试数据库连接
- 检查防火墙设置

### 4. 认证失败

- 检查 `SECRET_KEY` 配置
- 确认 JWT 配置正确
- 清除浏览器缓存
- 重新登录测试

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. **查看文档**
   - [DEPLOYMENT.md](./DEPLOYMENT.md)
   - [VERCEL_CONFIG.md](./VERCEL_CONFIG.md)
   - [ENV_VARIABLES.md](./ENV_VARIABLES.md)

2. **检查日志**
   - Vercel 部署日志
   - Railway 应用日志
   - 浏览器开发者工具

3. **运行检查工具**
   ```bash
   python check_deployment.py
   ```

4. **联系支持**
   - GitHub Issues
   - 项目维护者
   - 平台支持文档

---

## ✨ 恭喜！

如果所有检查项都已完成，你的应用已成功部署到生产环境！

**部署信息记录**：

```
前端 URL: https://_____.vercel.app
后端 URL: https://_____.railway.app
API 文档: https://_____.railway.app/docs
部署日期: ___________
```

**下一步**：
- 监控应用性能
- 收集用户反馈
- 计划功能迭代
- 定期更新依赖

🎊 **祝你的项目大获成功！** 🎊
