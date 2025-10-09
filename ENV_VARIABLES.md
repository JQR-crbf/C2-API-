# 环境变量配置指南

本文档详细说明项目所需的所有环境变量。

---

## 📋 前端环境变量（Next.js）

前端环境变量需要在 **Vercel Dashboard** 或本地 `.env.local` 文件中配置。

### 开发环境（`.env.local`）

```bash
# 后端API地址
NEXT_PUBLIC_API_URL=http://localhost:8080

# WebSocket地址（如果需要）
NEXT_PUBLIC_WS_URL=ws://localhost:8080

# 环境标识
NODE_ENV=development
```

### 生产环境（Vercel Dashboard）

在 Vercel 项目设置 → Environment Variables 中添加：

| 变量名 | 值 | 环境 | 必需 |
|--------|-----|------|------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app` | Production, Preview | ✅ 是 |
| `NEXT_PUBLIC_WS_URL` | `wss://your-backend.railway.app` | Production, Preview | ❌ 否 |
| `NODE_ENV` | `production` | Production | ✅ 是 |

**⚠️ 重要提示**：
- 所有需要在客户端访问的变量**必须**以 `NEXT_PUBLIC_` 开头
- 修改环境变量后需要**重新部署**才能生效
- 不要在前端环境变量中存储敏感信息（如API密钥）

---

## 📋 后端环境变量（FastAPI）

后端环境变量需要在 **Railway/Render Dashboard** 或本地 `.env` 文件中配置。

### 开发环境（`.env`）

在 `backend` 目录创建 `.env` 文件：

```bash
# ==================== 数据库配置 ====================
# MySQL 数据库连接字符串
# 格式: mysql+mysqldb://用户名:密码@主机:端口/数据库名
DATABASE_URL=mysql+mysqldb://root:your_password@localhost:3306/api_project_database

# ==================== JWT 认证配置 ====================
# JWT 密钥 - 用于加密用户token（必须保密！）
# 生成方式: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_secret_key_here_change_in_production

# JWT 算法
ALGORITHM=HS256

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ==================== AI 服务配置 ====================
# OpenRouter API 密钥
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# OpenRouter API 基础URL
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# 使用的AI模型
AI_MODEL=anthropic/claude-3-5-sonnet-20241022

# ==================== CORS 配置 ====================
# 允许的前端域名（多个用逗号分隔）
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# ==================== 环境配置 ====================
# 环境类型: development, production
ENVIRONMENT=development

# 调试模式
DEBUG=True

# ==================== 服务器配置 ====================
# 服务器地址
HOST=0.0.0.0

# 服务器端口
PORT=8080
```

### 生产环境（Railway/Render Dashboard）

在平台的环境变量配置页面添加：

#### 必需变量 ✅

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `mysql+mysqldb://user:pass@host:3306/db` | 数据库连接字符串 |
| `SECRET_KEY` | `8fjdksl_fjdkslfjdks-fdjsklfj3` | JWT密钥（必须强随机字符串）|
| `ALGORITHM` | `HS256` | JWT算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token有效期 |
| `OPENROUTER_API_KEY` | `sk-or-v1-xxxxx` | AI服务密钥 |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | AI服务地址 |
| `AI_MODEL` | `anthropic/claude-3-5-sonnet-20241022` | AI模型 |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | 前端域名 |
| `ENVIRONMENT` | `production` | 环境标识 |

#### 可选变量 ❌

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEBUG` | `False` | 调试模式 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8080` | 监听端口（通常由平台自动设置）|

---

## 🔐 Railway 专用配置

### Railway 自动变量

Railway 会自动提供以下变量：

| 变量名 | 说明 | 使用方式 |
|--------|------|----------|
| `PORT` | 应用端口 | 自动设置，无需配置 |
| `RAILWAY_ENVIRONMENT` | 环境名称 | 自动设置 |
| `MYSQL_URL` | MySQL连接URL | 如果添加了MySQL服务 |

### 引用其他服务

Railway 可以引用同项目中其他服务的变量：

```bash
# 引用 MySQL 服务的 URL
DATABASE_URL=${{MySQL.DATABASE_URL}}

# 引用自定义变量
API_KEY=${{SERVICE_NAME.API_KEY}}
```

---

## 🔐 敏感信息管理

### 生成强密钥

**方法 1：Python**
```python
import secrets
print(secrets.token_urlsafe(32))
# 输出: 8fjdksl_fjdkslfjdks-fdjsklfj3
```

**方法 2：OpenSSL**
```bash
openssl rand -base64 32
```

**方法 3：在线生成**
- [RandomKeygen](https://randomkeygen.com/)
- [Password Generator](https://passwordsgenerator.net/)

### 环境变量安全规则

✅ **应该做**：
- 使用强随机字符串作为密钥
- 不同环境使用不同的密钥
- 定期轮换敏感密钥
- 使用环境变量而不是硬编码

❌ **不应该做**：
- 将 `.env` 文件提交到 Git
- 在前端代码中使用后端密钥
- 在日志中输出敏感信息
- 使用简单或默认密钥

---

## 📝 环境变量检查清单

### 开发环境

- [ ] 后端 `.env` 文件已创建
- [ ] 数据库连接信息正确
- [ ] 可以成功连接数据库
- [ ] 后端服务启动正常
- [ ] 前端可以访问后端 API

### 生产环境

#### 后端（Railway/Render）

- [ ] `DATABASE_URL` 已配置且正确
- [ ] `SECRET_KEY` 已设置为强随机字符串
- [ ] `OPENROUTER_API_KEY` 已配置
- [ ] `ALLOWED_ORIGINS` 包含前端域名
- [ ] `ENVIRONMENT=production`
- [ ] 服务部署成功
- [ ] 可以访问 `/health` 端点

#### 前端（Vercel）

- [ ] `NEXT_PUBLIC_API_URL` 已配置
- [ ] 指向正确的后端地址
- [ ] 部署成功
- [ ] 可以访问前端页面
- [ ] API 请求成功（无 CORS 错误）

---

## 🔍 故障排查

### 问题 1：数据库连接失败

**症状**：
```
sqlalchemy.exc.OperationalError: (MySQLdb.OperationalError) 
(2003, "Can't connect to MySQL server")
```

**检查**：
- [ ] `DATABASE_URL` 格式正确？
- [ ] 数据库服务正在运行？
- [ ] 用户名和密码正确？
- [ ] 主机和端口可访问？
- [ ] 防火墙允许连接？

### 问题 2：CORS 错误

**症状**：
```
Access to fetch at '...' has been blocked by CORS policy
```

**检查**：
- [ ] `ALLOWED_ORIGINS` 包含前端域名？
- [ ] 域名格式正确（包含 https://）？
- [ ] 后端已重新部署？
- [ ] 没有多余的斜杠或空格？

### 问题 3：前端无法访问后端

**症状**：
- 网络请求失败
- Console 显示 404 或 502 错误

**检查**：
- [ ] `NEXT_PUBLIC_API_URL` 正确？
- [ ] 后端服务正在运行？
- [ ] 后端 URL 可访问（直接在浏览器打开）？
- [ ] 前端已重新部署？

### 问题 4：JWT Token 无效

**症状**：
```
{"detail": "Could not validate credentials"}
```

**检查**：
- [ ] `SECRET_KEY` 在所有后端实例中一致？
- [ ] `ALGORITHM` 设置正确？
- [ ] Token 未过期？
- [ ] 前后端时间同步？

---

## 📚 相关文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) - 完整部署指南
- [QUICK_DEPLOY.md](./QUICK_DEPLOY.md) - 快速部署指南
- [VERCEL_CONFIG.md](./VERCEL_CONFIG.md) - Vercel 配置说明
- [Railway 文档](https://docs.railway.app)
- [Vercel 文档](https://vercel.com/docs)

---

**需要帮助？** 检查完整的部署文档或联系项目维护者。
