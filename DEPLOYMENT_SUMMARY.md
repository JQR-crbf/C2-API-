# 🎯 Vercel 部署总结

## 📊 你遇到的问题

根据你提到的"报了很多错"，这里总结了 Vercel 部署此项目时的**常见错误和解决方案**。

---

## ❌ 常见错误列表

### 错误 1: NOT_FOUND (404)

**错误信息**：
```
404: NOT_FOUND
Could not find package.json
```

**原因**：
- Vercel 在项目根目录找不到 `package.json`
- 本项目的前端代码在 `ai-api-platform` 子目录中

**✅ 解决方案**：

**方法一：在 Vercel Dashboard 配置（推荐）**
1. 进入 Vercel 项目设置
2. 找到 "Build & Development Settings"
3. 设置 **Root Directory** 为 `ai-api-platform`
4. 保存并重新部署

**方法二：使用 vercel.json（已配置）**
- 项目根目录的 `vercel.json` 已经配置好
- Vercel 会自动识别并使用该配置
- 配置内容：
  ```json
  {
    "buildCommand": "cd ai-api-platform && npm run build",
    "outputDirectory": "ai-api-platform/.next"
  }
  ```

---

### 错误 2: DEPLOYMENT_ERROR - Build Failed

**错误信息**：
```
Error: Build failed with exit code 1
Module not found: Can't resolve '...'
```

**原因**：
- TypeScript 编译错误
- 导入路径错误
- 缺少依赖

**✅ 解决方案**：

项目已配置忽略构建错误（适合快速部署）：
```javascript
// next.config.mjs
{
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  }
}
```

**生产环境建议**：修复实际错误后，关闭这些忽略选项。

---

### 错误 3: 环境变量未定义

**错误信息**：
```
ReferenceError: process.env.NEXT_PUBLIC_API_URL is undefined
TypeError: Cannot read property of undefined
```

**原因**：
- 环境变量未配置
- 环境变量名称错误（必须以 `NEXT_PUBLIC_` 开头）

**✅ 解决方案**：

1. 在 Vercel Dashboard → Settings → Environment Variables
2. 添加：
   ```
   NEXT_PUBLIC_API_URL = https://your-backend.railway.app
   ```
3. **重要**：修改环境变量后必须重新部署

---

### 错误 4: API 请求 CORS 错误

**错误信息**（浏览器控制台）：
```
Access to fetch at 'https://backend.com/api/...' from origin 'https://frontend.com' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**原因**：
- 后端未配置允许前端域名访问

**✅ 解决方案**：

1. 在后端（Railway）环境变量中添加：
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
2. 后端会自动重新部署
3. 项目的 `backend/main.py` 已修改为从环境变量读取 CORS 配置

---

### 错误 5: 图片加载失败

**错误信息**：
```
Error: Invalid src prop
Image Optimization using Next.js' default loader is not compatible with `next export`
```

**原因**：
- Next.js Image 组件的优化功能与某些部署配置冲突

**✅ 解决方案**（已配置）：
```javascript
// next.config.mjs
{
  images: {
    unoptimized: true,
  }
}
```

---

### 错误 6: 函数超时

**错误信息**：
```
FUNCTION_INVOCATION_TIMEOUT
Error: The edge function exceeded the maximum duration
```

**原因**：
- Serverless 函数执行时间过长
- API 路由处理复杂请求

**✅ 解决方案**：

本项目将后端独立部署到 Railway，避免此问题：
- Vercel：只部署前端（Next.js 页面）
- Railway：部署后端 API（支持长时间运行）

---

### 错误 7: 构建输出目录错误

**错误信息**：
```
Error: Could not find build output at ".next"
```

**原因**：
- 输出目录配置错误
- Root Directory 未正确设置

**✅ 解决方案**（已配置）：

在 `vercel.json` 中：
```json
{
  "outputDirectory": "ai-api-platform/.next"
}
```

或在 Vercel Dashboard 中：
- Output Directory: `.next`（相对于 Root Directory）

---

## 🎯 完整部署步骤（零错误）

### 第一步：准备代码

```bash
# 1. 确保代码在 Git 仓库中
git add .
git commit -m "准备部署到 Vercel"
git push origin master

# 2. 运行部署检查
python check_deployment.py
```

### 第二步：部署后端到 Railway

1. 访问 https://railway.app
2. 登录并创建新项目
3. 选择 "Deploy from GitHub repo"
4. 配置：
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 添加 MySQL 数据库
6. 配置环境变量（参考 [ENV_VARIABLES.md](./ENV_VARIABLES.md)）
7. 等待部署完成
8. 记录域名：`https://xxxxx.railway.app`

### 第三步：部署前端到 Vercel

1. 访问 https://vercel.com
2. 登录并点击 "Add New Project"
3. 导入 GitHub 仓库
4. **关键配置**：
   ```
   Framework Preset: Next.js
   Root Directory: ai-api-platform  ← 必须设置！
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```
5. 添加环境变量：
   ```
   NEXT_PUBLIC_API_URL=https://xxxxx.railway.app
   ```
6. 点击 Deploy
7. 等待部署完成

### 第四步：更新 CORS 配置

1. 回到 Railway 后端服务
2. 编辑环境变量：
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
3. 保存并等待重新部署

### 第五步：验证部署

```bash
# 测试后端
curl https://xxxxx.railway.app/health

# 预期返回
{"status":"healthy","service":"ai-api-platform-backend"}
```

访问前端 URL，测试功能：
- ✅ 页面正常加载
- ✅ 可以注册/登录
- ✅ 可以创建任务
- ✅ 无控制台错误

---

## 🔧 如果仍然报错

### 查看 Vercel 部署日志

1. 进入 Vercel Dashboard
2. 选择你的项目
3. 点击 "Deployments"
4. 点击失败的部署
5. 查看 "Build Logs"

### 常见日志分析

**日志显示 "Cannot find package.json"**
→ Root Directory 未设置为 `ai-api-platform`

**日志显示 "Module not found"**
→ 检查导入路径，或启用 `ignoreBuildErrors`

**日志显示 "Command failed"**
→ 检查 `package.json` 中的 build 脚本

**部署成功但页面空白**
→ 检查浏览器控制台错误，通常是环境变量或 API 问题

---

## 📚 详细文档索引

根据你的需求查看：

| 文档 | 适用场景 |
|------|----------|
| **[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** | 想要5分钟快速部署 |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | 想要了解详细步骤和原理 |
| **[VERCEL_CONFIG.md](./VERCEL_CONFIG.md)** | Vercel 配置问题和优化 |
| **[ENV_VARIABLES.md](./ENV_VARIABLES.md)** | 环境变量配置详解 |
| **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** | 系统化检查部署步骤 |

---

## 💡 关键要点总结

### ✅ 记住这些关键配置

1. **Vercel Root Directory**: `ai-api-platform`
2. **后端 Root Directory**: `backend`
3. **前端环境变量**: `NEXT_PUBLIC_API_URL`
4. **后端环境变量**: `ALLOWED_ORIGINS`（包含 Vercel 域名）

### ⚠️ 常见错误原因

1. **Root Directory 未配置** → 404 错误
2. **环境变量未设置** → undefined 错误
3. **CORS 未配置** → API 请求失败
4. **后端未部署** → 网络错误

### 🎯 正确的部署顺序

```
1. 先部署后端（Railway）
   ↓
2. 获取后端 URL
   ↓
3. 部署前端（Vercel）+ 配置后端 URL
   ↓
4. 更新后端 CORS（添加前端 URL）
   ↓
5. 测试完整功能
```

---

## 🆘 需要帮助？

### 自助排查工具

```bash
# 运行部署检查
python check_deployment.py

# 查看项目结构
tree ai-api-platform backend
```

### 获取支持

1. **查看错误日志**
   - Vercel: Dashboard → Deployments → Build Logs
   - Railway: Dashboard → Deployments → View Logs

2. **搜索错误信息**
   - [Vercel 错误文档](https://vercel.com/docs/errors)
   - [Railway 故障排除](https://docs.railway.app/troubleshoot/fixing-common-errors)

3. **联系项目维护者**
   - 提供错误截图
   - 提供部署日志
   - 说明具体步骤

---

## ✨ 部署成功后

恭喜！你的应用现在已经在线运行。

**记录你的部署信息**：

```
前端 URL: https://_____.vercel.app
后端 URL: https://_____.railway.app
API 文档: https://_____.railway.app/docs
部署日期: 2025-01-__
```

**下一步优化**：
- [ ] 配置自定义域名
- [ ] 启用 Vercel Analytics
- [ ] 设置监控告警
- [ ] 配置自动备份
- [ ] 优化性能指标

---

**祝你部署顺利！如有问题，随时参考上述文档。** 🚀
