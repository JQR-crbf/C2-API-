# 🚀 从这里开始部署

欢迎！如果你想将此项目部署到生产环境，这份指南会帮你快速上手。

---

## 📋 你需要什么？

### 必需的账号（全部免费）

1. **GitHub 账号** - 存放代码
2. **Vercel 账号** - 部署前端（免费）
3. **Railway 账号** - 部署后端+数据库（每月$5免费额度）

### 需要的时间

- **完整部署**：约 10-15 分钟
- **快速部署**：约 5 分钟（使用快速指南）

---

## 🎯 选择你的部署路径

### 路径 1: 我想快速部署（推荐新手）

**适合**：第一次部署，想快速看到效果

📖 阅读：**[5分钟快速部署指南](./QUICK_DEPLOY.md)**

这份指南：
- ✅ 步骤最少
- ✅ 配图说明
- ✅ 保证能成功

---

### 路径 2: 我遇到了部署错误

**适合**：部署失败，需要排查问题

📖 阅读：**[部署错误总结](./DEPLOYMENT_SUMMARY.md)**

这份指南：
- ✅ 列出所有常见错误
- ✅ 提供具体解决方案
- ✅ 包含错误日志分析

---

### 路径 3: 我想了解详细原理

**适合**：想理解每个步骤的作用

📖 阅读：**[完整部署指南](./DEPLOYMENT.md)**

这份指南：
- ✅ 详细解释每个步骤
- ✅ 多种部署方案对比
- ✅ 高级配置选项

---

## 📚 完整文档索引

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| **[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** | 5分钟快速部署 | 5 分钟 |
| **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** | 错误排查和解决 | 10 分钟 |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | 完整部署指南 | 20 分钟 |
| **[VERCEL_CONFIG.md](./VERCEL_CONFIG.md)** | Vercel 专用配置 | 15 分钟 |
| **[ENV_VARIABLES.md](./ENV_VARIABLES.md)** | 环境变量详解 | 10 分钟 |
| **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** | 部署检查清单 | 5 分钟 |

---

## 🔧 部署前准备

### 1. 检查代码是否准备好

```bash
# 运行自动检查脚本
python check_deployment.py
```

这个脚本会检查：
- ✅ 项目结构是否正确
- ✅ 配置文件是否完整
- ✅ 依赖是否正确安装

### 2. 确保代码在 Git 仓库中

```bash
# 查看状态
git status

# 提交更改
git add .
git commit -m "准备部署"
git push origin master
```

---

## ⚡ 最快部署流程（3步）

### 步骤 1: 部署后端（3分钟）

1. 访问 https://railway.app
2. 用 GitHub 登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择此项目
5. 设置 Root Directory 为 `backend`
6. 添加 MySQL 数据库
7. 配置环境变量（复制模板）
8. 等待部署完成
9. 记录域名

### 步骤 2: 部署前端（2分钟）

1. 访问 https://vercel.com
2. 用 GitHub 登录
3. 点击 "Add New Project"
4. 选择此项目
5. **重要**：设置 Root Directory 为 `ai-api-platform`
6. 添加环境变量：`NEXT_PUBLIC_API_URL`=后端域名
7. 点击 Deploy
8. 等待部署完成

### 步骤 3: 更新 CORS（1分钟）

1. 回到 Railway
2. 添加环境变量：`ALLOWED_ORIGINS`=前端域名
3. 等待重新部署
4. 完成！

---

## ✅ 验证部署成功

### 测试后端

打开浏览器，访问：
```
https://your-backend.railway.app/health
```

应该看到：
```json
{"status":"healthy","service":"ai-api-platform-backend"}
```

### 测试前端

访问你的 Vercel 域名：
```
https://your-app.vercel.app
```

尝试：
- ✅ 注册新用户
- ✅ 登录
- ✅ 创建任务

---

## 🐛 遇到问题？

### 快速排查

1. **前端页面空白**
   - 打开浏览器开发者工具（F12）
   - 查看 Console 标签的错误信息
   - 通常是环境变量问题

2. **API 请求失败**
   - 检查 `NEXT_PUBLIC_API_URL` 是否正确
   - 检查后端 `ALLOWED_ORIGINS` 是否包含前端域名
   - 访问后端 `/health` 确认服务运行

3. **构建失败**
   - 查看 Vercel 构建日志
   - 确认 Root Directory 设置为 `ai-api-platform`
   - 检查 `package.json` 是否存在

### 获取帮助

📖 **查看详细错误解决方案**：[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)

---

## 💡 重要提示

### ⚠️ 常见错误

1. **忘记设置 Root Directory**
   - Vercel: 必须设置为 `ai-api-platform`
   - Railway: 必须设置为 `backend`

2. **忘记配置环境变量**
   - 前端需要：`NEXT_PUBLIC_API_URL`
   - 后端需要：`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS` 等

3. **忘记更新 CORS**
   - 后端部署后，必须添加前端域名到 `ALLOWED_ORIGINS`

### ✅ 成功的关键

- 📍 正确设置 Root Directory
- 🔑 完整配置环境变量
- 🔄 按顺序部署（后端 → 前端 → 更新 CORS）

---

## 🎉 部署成功后

记录你的部署信息：

```
✅ 前端 URL: https://_____.vercel.app
✅ 后端 URL: https://_____.railway.app
✅ API 文档: https://_____.railway.app/docs
```

分享给团队成员，开始使用！

---

## 📞 需要更多帮助？

- 📖 [完整文档列表](#-完整文档索引)
- 🔍 运行 `python check_deployment.py` 检查配置
- 💬 查看项目 Issues
- 📧 联系项目维护者

---

**祝你部署顺利！** 🚀

*有了这些文档，你应该能够顺利将项目部署到生产环境。如果遇到问题，按照错误提示查找对应的文档章节即可。*
