# ⚡ 快速部署指南（5分钟）

这是最简化的部署流程，适合快速上线测试。

## 🎯 部署目标

- ✅ 前端部署到 Vercel（免费）
- ✅ 后端部署到 Railway（免费额度）
- ✅ 使用 Railway 的 MySQL 数据库（免费）

---

## 第一步：部署后端到 Railway（3分钟）

1. **访问并登录 Railway**
   - 打开 https://railway.app
   - 点击 "Login with GitHub"

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择这个项目仓库

3. **配置 Python 服务**
   - Railway 自动检测到 Python 项目
   - 点击服务名称进入设置
   - 在 "Settings" → "Service" 中：
     - **Root Directory**: 设置为 `backend`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **添加 MySQL 数据库**
   - 在项目中点击 "New"
   - 选择 "Database" → "Add MySQL"
   - Railway 会自动创建数据库

5. **配置环境变量**
   - 点击 Python 服务
   - 进入 "Variables" 标签
   - 点击 "New Variable"，添加以下变量：

   ```bash
   DATABASE_URL=${{MySQL.DATABASE_URL}}
   SECRET_KEY=your-secret-key-change-this-in-production-123456
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   AI_MODEL=anthropic/claude-3-5-sonnet-20241022
   ALLOWED_ORIGINS=http://localhost:3000
   ENVIRONMENT=production
   DEBUG=False
   ```

   > ⚠️ `DATABASE_URL=${{MySQL.DATABASE_URL}}` 会自动引用 MySQL 服务的连接字符串

6. **生成公开 URL**
   - 在 "Settings" → "Networking" 中
   - 点击 "Generate Domain"
   - 复制生成的域名，例如：`https://your-backend.railway.app`

7. **初始化数据库**
   - 等待部署完成（约1-2分钟）
   - 点击服务，进入 "Deployments"
   - 点击最新的部署，然后点击 "View Logs"
   - 确认服务启动成功
   - 访问 `https://your-backend.railway.app/health` 检查状态

   如需初始化数据库表：
   - 在服务页面找到 "..." 菜单
   - 选择 "Shell"
   - 运行：`python init_db.py`

---

## 第二步：部署前端到 Vercel（2分钟）

1. **访问并登录 Vercel**
   - 打开 https://vercel.com
   - 点击 "Login" → "Continue with GitHub"

2. **导入项目**
   - 点击 "Add New..." → "Project"
   - 找到你的项目仓库
   - 点击 "Import"

3. **配置项目（重要！）**
   
   **Framework Preset**: Next.js
   
   **Root Directory**: 点击 "Edit"，输入 `ai-api-platform` ⚠️
   
   **Build & Development Settings**:
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

4. **配置环境变量**
   
   展开 "Environment Variables"，添加：
   
   | Name | Value |
   |------|-------|
   | `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app` |
   
   > ⚠️ 将 `https://your-backend.railway.app` 替换为第一步中 Railway 生成的域名

5. **部署**
   - 点击 "Deploy"
   - 等待构建（约2-3分钟）
   - 部署完成后，点击 "Visit" 或复制域名

6. **更新后端 CORS 配置**
   - 复制 Vercel 分配的域名，例如：`https://your-app.vercel.app`
   - 回到 Railway 的后端服务
   - 编辑环境变量 `ALLOWED_ORIGINS`：
     ```bash
     ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
     ```
   - 保存后 Railway 会自动重新部署

---

## 第三步：验证部署（1分钟）

1. **测试后端**
   ```bash
   curl https://your-backend.railway.app/health
   ```
   应该返回：
   ```json
   {"status":"healthy","service":"ai-api-platform-backend"}
   ```

2. **测试前端**
   - 访问你的 Vercel 域名
   - 尝试注册新用户
   - 尝试登录
   - 创建一个测试任务

3. **检查错误**
   - 如果有问题，打开浏览器开发者工具（F12）
   - 查看 Console 和 Network 标签的错误信息

---

## ✅ 部署完成！

你的应用现在已经在线运行了！

- **前端地址**: https://your-app.vercel.app
- **后端地址**: https://your-backend.railway.app
- **API 文档**: https://your-backend.railway.app/docs

---

## 🔧 后续配置（可选）

### 配置自定义域名

**Vercel 前端**:
1. 在 Vercel 项目设置 → Domains
2. 添加你的域名
3. 配置 DNS 记录

**Railway 后端**:
1. 在 Railway 服务设置 → Networking
2. 添加自定义域名
3. 配置 DNS 记录

### 配置环境变量

记得配置真实的 API 密钥：
- `OPENROUTER_API_KEY`: 用于 AI 代码生成
- `SECRET_KEY`: 使用强随机字符串

### 启用 WebSocket

确保后端环境变量中包含前端域名，WebSocket 会自动工作。

---

## 🐛 遇到问题？

### 前端访问后端 API 失败

**症状**: 前端页面加载但功能不可用，浏览器 Console 显示网络错误

**解决**:
1. 检查 `NEXT_PUBLIC_API_URL` 是否正确
2. 检查后端 `ALLOWED_ORIGINS` 是否包含前端域名
3. 访问后端 `/health` 端点确认服务运行正常

### Railway 部署失败

**症状**: 部署日志显示错误

**常见原因**:
1. `requirements.txt` 中的包安装失败
   - 解决：检查包版本兼容性
2. 启动命令错误
   - 确认：`uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Root Directory 设置错误
   - 确认设置为 `backend`

### 数据库连接失败

**症状**: 后端日志显示数据库连接错误

**解决**:
1. 确认 MySQL 服务已添加
2. 检查 `DATABASE_URL` 变量：`${{MySQL.DATABASE_URL}}`
3. 确认 MySQL 服务和 Python 服务在同一个项目中
4. 查看 MySQL 服务的 Variables，确认连接信息

---

## 📚 详细文档

需要更详细的配置和高级功能？查看：
- [完整部署指南](./DEPLOYMENT.md)
- [项目 README](./README.md)

---

**恭喜！你的应用已经成功部署！** 🎉
