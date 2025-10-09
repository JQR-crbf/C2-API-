# 🚀 部署指南

本文档详细说明如何将 AI API 开发自动化平台部署到生产环境。

## 📋 目录

- [部署架构](#部署架构)
- [前端部署（Vercel）](#前端部署vercel)
- [后端部署](#后端部署)
  - [Railway 部署](#方案一railway-推荐)
  - [Render 部署](#方案二render)
  - [其他平台](#方案三其他平台)
- [数据库配置](#数据库配置)
- [环境变量配置](#环境变量配置)
- [部署后验证](#部署后验证)
- [常见问题](#常见问题)

---

## 部署架构

本项目采用前后端分离架构，需要分别部署：

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel        │  HTTP   │   Railway/Render │
│   (前端)        │ ◄─────► │   (后端 API)     │
│   Next.js       │         │   FastAPI        │
└─────────────────┘         └──────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │   云数据库        │
                            │   MySQL          │
                            └──────────────────┘
```

**为什么不能全部部署到 Vercel？**
- Vercel 主要为前端和 Serverless Functions 设计
- 本项目后端使用 FastAPI，需要：
  - WebSocket 支持（长连接）
  - 后台任务处理器（常驻进程）
  - MySQL 数据库连接池（持久连接）
- 这些功能不适合 Serverless 环境，需要部署到支持常驻进程的平台

---

## 前端部署（Vercel）

### 第一步：准备工作

1. **确保代码已推送到 Git 仓库**
   ```bash
   git add .
   git commit -m "准备部署"
   git push origin master
   ```

2. **注册 Vercel 账号**
   - 访问 [vercel.com](https://vercel.com)
   - 使用 GitHub 账号登录

### 第二步：导入项目

1. **在 Vercel Dashboard 点击 "Add New Project"**

2. **导入你的 Git 仓库**
   - 选择你的项目仓库
   - 点击 "Import"

3. **配置项目设置**
   
   **重要：由于前端在 `ai-api-platform` 子目录，需要配置根目录**
   
   - **Framework Preset**: Next.js
   - **Root Directory**: `ai-api-platform` ⚠️ 
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

4. **配置环境变量**
   
   在 Vercel 项目设置中添加以下环境变量：
   
   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app` | 后端API地址（稍后配置） |
   | `NEXT_PUBLIC_WS_URL` | `wss://your-backend.railway.app` | WebSocket地址（如需要） |

   > ⚠️ 注意：现在可以先留空 `NEXT_PUBLIC_API_URL`，等后端部署完成后再填入

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成（约 2-3 分钟）
   - 记录 Vercel 分配的域名，例如：`https://your-app.vercel.app`

### 第三步：配置自定义域名（可选）

1. 在 Vercel 项目设置中找到 "Domains"
2. 添加你的自定义域名
3. 按照提示配置 DNS 记录

---

## 后端部署

后端需要部署到支持 Python 应用和常驻进程的平台。推荐以下方案：

### 方案一：Railway（推荐）

**优点**：
- ✅ 免费额度充足（每月 $5 免费额度）
- ✅ 自动检测 Python 项目
- ✅ 内置 MySQL 数据库支持
- ✅ 支持 WebSocket
- ✅ 自动 HTTPS
- ✅ 部署简单快速

**部署步骤**：

1. **注册 Railway 账号**
   - 访问 [railway.app](https://railway.app)
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的项目仓库

3. **配置服务**
   - Railway 会自动检测到 Python 项目
   - 设置根目录为 `backend`
   - 确认启动命令：`uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **添加 MySQL 数据库**
   - 在项目中点击 "New Service"
   - 选择 "Database" → "MySQL"
   - Railway 会自动创建数据库并提供连接信息

5. **配置环境变量**
   
   在 Railway 项目设置中添加以下环境变量：
   
   ```bash
   # 数据库连接（Railway 会自动提供 MYSQL_URL）
   DATABASE_URL=${MYSQL_URL}  # 或手动配置
   
   # JWT 配置
   SECRET_KEY=你的强密钥（使用随机字符串）
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # AI 服务配置
   OPENROUTER_API_KEY=你的OpenRouter API密钥
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   AI_MODEL=anthropic/claude-3-5-sonnet-20241022
   
   # CORS 配置（填入 Vercel 前端域名）
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   
   # 环境配置
   ENVIRONMENT=production
   DEBUG=False
   ```

6. **部署**
   - 保存环境变量后，Railway 会自动部署
   - 等待部署完成
   - 记录 Railway 分配的域名，例如：`https://your-backend.railway.app`

7. **初始化数据库**
   - 在 Railway 控制台找到你的服务
   - 打开终端（Terminal）
   - 运行：`python init_db.py`

8. **更新前端配置**
   - 回到 Vercel 项目设置
   - 更新环境变量 `NEXT_PUBLIC_API_URL` 为 Railway 域名
   - 触发重新部署

### 方案二：Render

**优点**：
- ✅ 免费套餐
- ✅ 自动 HTTPS
- ✅ 支持 Docker
- ✅ 持续部署

**缺点**：
- ⚠️ 免费套餐在无活动 15 分钟后会休眠
- ⚠️ 冷启动时间较长（30-60 秒）

**部署步骤**：

1. **注册 Render 账号**
   - 访问 [render.com](https://render.com)
   - 使用 GitHub 账号登录

2. **创建 Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的 Git 仓库
   - 选择你的项目

3. **配置服务**
   ```
   Name: ai-api-backend
   Region: Singapore (或其他亚洲节点)
   Branch: master
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **选择套餐**
   - Free 套餐（会休眠）
   - 或 Starter 套餐（$7/月，不休眠）

5. **添加环境变量**
   - 在 "Environment" 标签页添加上述环境变量
   - 数据库需要单独创建（见下方数据库配置）

6. **部署并初始化数据库**
   - 保存配置后会自动部署
   - 通过 Render Shell 运行 `python init_db.py`

### 方案三：其他平台

- **Heroku**：经典平台，但免费套餐已取消
- **AWS/GCP/Azure**：需要更多配置，适合有云平台经验的用户
- **DigitalOcean App Platform**：简单易用，最低 $5/月
- **Fly.io**：免费额度有限，但性能好

---

## 数据库配置

### 选项 1：Railway MySQL（推荐）

如果使用 Railway 部署后端，推荐使用 Railway 的 MySQL 服务：

1. 在 Railway 项目中点击 "New Service"
2. 选择 "MySQL"
3. Railway 会自动创建数据库并提供连接字符串
4. 环境变量 `MYSQL_URL` 会自动注入

### 选项 2：PlanetScale（推荐用于 Render）

PlanetScale 是 serverless MySQL 数据库，有免费套餐：

1. 注册 [PlanetScale](https://planetscale.com)
2. 创建数据库
3. 获取连接字符串：`mysql://user:pass@host/database?sslaccept=strict`
4. 转换为 SQLAlchemy 格式：`mysql+mysqldb://user:pass@host/database`
5. 在后端环境变量中配置 `DATABASE_URL`

### 选项 3：其他云数据库

- **Supabase**：PostgreSQL 数据库（需修改代码）
- **AWS RDS**：需要 AWS 账号和配置
- **阿里云/腾讯云 RDS**：中国用户推荐

---

## 环境变量配置

### 前端环境变量（Vercel）

```bash
# 必需
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# 可选
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

### 后端环境变量（Railway/Render）

```bash
# 数据库（必需）
DATABASE_URL=mysql+mysqldb://user:pass@host:port/database

# JWT 认证（必需）
SECRET_KEY=你的超长随机字符串
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI 服务（必需）
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=anthropic/claude-3-5-sonnet-20241022

# CORS（必需 - 填入 Vercel 域名）
ALLOWED_ORIGINS=https://your-app.vercel.app

# 环境配置
ENVIRONMENT=production
DEBUG=False
```

### 如何生成强密钥（SECRET_KEY）

```python
# 在 Python 中运行
import secrets
print(secrets.token_urlsafe(32))
# 输出: 8fjdksl_fjdkslfjdks-fdjsklfj3
```

或在线生成：[randomkeygen.com](https://randomkeygen.com/)

---

## 部署后验证

### 1. 检查后端健康状态

访问后端健康检查端点：

```bash
curl https://your-backend.railway.app/health
```

应该返回：
```json
{
  "status": "healthy",
  "service": "ai-api-platform-backend"
}
```

### 2. 检查前端是否能访问后端

打开前端应用：`https://your-app.vercel.app`

1. 尝试注册/登录
2. 检查浏览器开发者工具的 Network 标签
3. 确认 API 请求成功（状态码 200）

### 3. 测试完整流程

1. 注册新用户
2. 登录
3. 创建任务
4. 查看任务列表
5. 检查通知系统

---

## 常见问题

### Q1: Vercel 部署失败，提示找不到 package.json

**原因**：项目根目录不正确

**解决**：
1. 在 Vercel 项目设置中
2. 找到 "Build & Development Settings"
3. 设置 "Root Directory" 为 `ai-api-platform`
4. 重新部署

### Q2: 前端部署成功，但页面空白或报错

**可能原因**：
1. 环境变量未配置
2. 后端地址不正确

**检查步骤**：
1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签的错误信息
3. 查看 Network 标签，检查 API 请求是否失败
4. 确认 `NEXT_PUBLIC_API_URL` 已正确配置

### Q3: 后端部署失败

**常见原因**：
1. `requirements.txt` 缺少依赖
2. 数据库连接失败
3. 环境变量未配置

**解决步骤**：
1. 查看部署日志
2. 确认所有环境变量已配置
3. 测试数据库连接
4. 检查启动命令是否正确

### Q4: CORS 错误

**错误信息**：
```
Access to fetch at 'https://backend.com/api/...' from origin 'https://frontend.com' 
has been blocked by CORS policy
```

**解决**：
1. 在后端环境变量中添加前端域名：
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
2. 重新部署后端

### Q5: 数据库连接失败

**错误信息**：
```
sqlalchemy.exc.OperationalError: (MySQLdb.OperationalError) 
(2003, "Can't connect to MySQL server")
```

**解决**：
1. 检查 `DATABASE_URL` 格式是否正确
2. 确认数据库服务正在运行
3. 检查防火墙/安全组设置
4. 确认数据库允许外部连接

### Q6: Railway 免费额度不够

**Railway 免费额度**：
- 每月 $5 免费额度
- 约可运行 500 小时

**优化建议**：
1. 使用 Render 的免费套餐（会休眠但完全免费）
2. 升级 Railway 套餐（$5/月）
3. 使用其他平台

### Q7: WebSocket 连接失败

**原因**：
- 某些平台不支持 WebSocket
- 环境变量配置错误

**解决**：
1. 确认平台支持 WebSocket（Railway ✅, Render ✅）
2. 使用 `wss://` 协议（生产环境）
3. 检查防火墙设置

---

## 🎉 部署完成检查清单

- [ ] 后端已部署并可访问 `/health` 端点
- [ ] 数据库已创建并初始化（运行 `init_db.py`）
- [ ] 后端环境变量已全部配置
- [ ] 前端已部署到 Vercel
- [ ] 前端环境变量已配置（`NEXT_PUBLIC_API_URL`）
- [ ] CORS 配置正确（后端允许前端域名）
- [ ] 可以成功注册和登录
- [ ] 可以创建和查看任务
- [ ] WebSocket 通知正常工作

---

## 📞 获取帮助

如果遇到问题：

1. **查看日志**
   - Vercel: 项目 → Deployments → 点击部署 → Logs
   - Railway: 项目 → Service → Deployments → View Logs

2. **测试 API**
   - 使用 Postman 或 curl 直接测试后端 API
   - 访问后端 Swagger 文档：`https://your-backend.railway.app/docs`

3. **常见错误排查**
   - 检查环境变量是否完整
   - 确认数据库连接字符串格式
   - 查看浏览器开发者工具的 Console 和 Network

4. **联系支持**
   - GitHub Issues
   - 项目维护者邮箱

---

## 🔄 更新部署

### 更新前端

1. 推送代码到 Git 仓库
2. Vercel 会自动检测并重新部署
3. 或在 Vercel Dashboard 手动触发部署

### 更新后端

1. 推送代码到 Git 仓库
2. Railway/Render 会自动检测并重新部署
3. 或在平台 Dashboard 手动触发部署

---

## 💰 成本估算

### 免费方案（适合测试和小型项目）

- **前端（Vercel）**: 免费
- **后端（Railway）**: 每月 $5 免费额度
- **数据库（Railway MySQL）**: 包含在 Railway 免费额度中
- **总计**: $0/月（在免费额度内）

### 付费方案（适合生产环境）

- **前端（Vercel Pro）**: $20/月（团队协作）
- **后端（Railway）**: $5/月起
- **数据库（PlanetScale Scaler）**: $29/月
- **总计**: 约 $34-54/月

---

**祝你部署顺利！** 🚀

如有问题请参考常见问题部分或查看平台官方文档。
