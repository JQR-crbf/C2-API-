# AI API 开发自动化平台

这是一个基于AI的API开发自动化平台，能够根据用户需求自动生成API代码、部署测试环境并进行自动化测试。

## 项目概述

### 核心功能
- **用户认证系统**：支持用户注册、登录和权限管理
- **任务管理**：用户可以提交API开发需求，系统自动处理
- **AI代码生成**：基于用户需求自动生成FastAPI代码
- **测试环境部署**：自动部署生成的代码到Docker测试环境
- **管理员审核**：管理员可以审核和管理所有任务
- **通知系统**：实时通知用户任务进度和状态变化

### 技术架构
- **前端**：Next.js 14 + React + TypeScript + Tailwind CSS
- **后端**：FastAPI + SQLAlchemy + MySQL
- **数据库**：MySQL（本地或远程数据库）
- **容器化**：Docker（用于测试环境部署）
- **AI集成**：OpenAI API（可配置）

## 项目结构

```
C2-API project/
├── ai-api-platform/          # 前端项目
│   ├── app/                   # Next.js 应用目录
│   │   ├── admin/            # 管理员页面
│   │   ├── auth/             # 认证页面
│   │   ├── tasks/            # 任务管理页面
│   │   └── testing/          # 测试环境页面
│   ├── components/           # 共享组件
│   └── public/              # 静态资源
├── backend/                  # 后端项目
│   ├── routers/             # API路由
│   │   ├── auth.py          # 认证相关API
│   │   ├── tasks.py         # 任务管理API
│   │   ├── admin.py         # 管理员API
│   │   └── notifications.py # 通知API
│   ├── services/            # 业务服务
│   │   ├── ai_service.py    # AI代码生成服务
│   │   ├── test_service.py  # 测试环境服务
│   │   └── task_processor.py # 后台任务处理器
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # API数据模式
│   ├── database.py          # 数据库配置
│   ├── auth_utils.py        # 认证工具
│   ├── main.py              # 应用入口
│   └── init_db.py           # 数据库初始化脚本
└── README.md                # 项目说明文档
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- Docker（可选，用于测试环境部署）

### 1. 后端设置

#### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 配置数据库

**当前使用 MySQL 数据库**

1. **安装MySQL服务器**：
   - Windows: 下载并安装 MySQL Community Server
   - macOS: `brew install mysql`
   - Linux: `sudo apt-get install mysql-server`

2. **创建数据库**：
```sql
CREATE DATABASE api_project_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **配置数据库连接**：
   - 修改 `backend/.env` 文件中的 `DATABASE_URL`
   - 格式：`mysql+mysqlclient://username:password@host:port/database_name`

4. **初始化数据库**：
```bash
cd backend
python init_db.py
```

#### 启动后端服务
```bash
python main.py
```

后端服务将在 `http://localhost:8000` 启动

### 2. 前端设置

#### 安装依赖
```bash
cd ai-api-platform
npm install
```

#### 启动前端服务
```bash
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

## 当前用户账户

**⚠️ 重要说明**：当前数据库中的实际用户与初始化脚本不同

### 实际存在的用户账户

| 用户ID | 用户名 | 邮箱 | 角色 | 状态 |
|--------|--------|------|------|------|
| 5 | admin | admin@test.com | user | 激活 |
| 6 | Test User | test@example.com | user | 激活 |
| 7 | **jinqianru** | 123@qq.com | user | 激活 |
| 8 | testuser | testuser@test.com | user | 激活 |

### 关键信息
- **jinqianru用户**（ID=7）是主要的任务创建者，拥有3个API开发任务
- **所有用户角色都是普通用户**，当前没有管理员用户
- **任务状态**：jinqianru的所有任务都处于"testing"状态

**⚠️ 重要提示：如需管理员权限，请手动修改数据库中的用户角色！**

## 主要功能使用说明

### 1. 用户注册和登录
- 访问 `http://localhost:3000/auth/login` 进行登录
- 访问 `http://localhost:3000/auth/register` 进行注册
- 支持用户名/邮箱登录

### 2. 创建API开发任务
1. 登录后访问 `http://localhost:3000/tasks/create`
2. 填写任务信息：
   - **任务标题**：简短描述API功能
   - **任务描述**：详细描述API需求
   - **输入参数**：定义API输入参数（JSON格式）
   - **输出参数**：定义API输出参数（JSON格式）
3. 提交任务后，系统会自动处理

### 3. 任务处理流程
任务提交后会经历以下状态：
1. **已提交** (submitted) - 任务已提交，等待处理
2. **拉取代码中** (code_pulling) - 系统正在拉取代码仓库
3. **分支已创建** (branch_created) - Git分支已创建
4. **AI生成代码中** (ai_generating) - AI正在生成代码
5. **测试环境准备就绪** (test_ready) - 代码生成完成，准备部署
6. **测试中** (testing) - 正在部署到测试环境
7. **测试完成** (test_completed) - 测试环境部署完成
8. **代码已推送** (code_pushed) - 等待管理员审核
9. **管理员审核中** (under_review) - 管理员正在审核
10. **审核通过** (approved) - 任务完成
11. **已部署** (deployed) - 代码已部署到生产环境
12. **审核拒绝** (rejected) - 任务被拒绝

### 4. 查看任务状态
- 访问 `http://localhost:3000/tasks` 查看任务列表
- 点击任务可查看详细信息和处理日志
- 系统会实时更新任务状态

### 5. 管理员功能
使用管理员账户登录后：
- 访问 `http://localhost:3000/admin` 查看管理面板
- 可以查看所有用户和任务
- 可以审核任务（通过/拒绝）
- 可以管理用户状态（启用/禁用）
- 可以发送系统通知

### 6. 测试环境
- 访问 `http://localhost:3000/testing` 查看测试环境
- 可以测试已部署的API
- 查看API文档和测试结果

## API文档

后端启动后，可以访问以下地址查看API文档：
- **Swagger UI**：`http://localhost:8000/docs`
- **ReDoc**：`http://localhost:8000/redoc`

### 主要API端点

#### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

#### 任务管理
- `POST /api/tasks/` - 创建任务
- `GET /api/tasks/` - 获取任务列表
- `GET /api/tasks/{task_id}` - 获取任务详情
- `GET /api/tasks/{task_id}/logs` - 获取任务日志
- `DELETE /api/tasks/{task_id}` - 删除任务

#### 管理员功能
- `GET /api/admin/stats` - 获取系统统计
- `GET /api/admin/tasks` - 获取所有任务
- `PUT /api/admin/tasks/{task_id}` - 更新任务状态
- `GET /api/admin/users` - 获取用户列表
- `PUT /api/admin/users/{user_id}/status` - 更新用户状态

#### 通知管理
- `GET /api/notifications/` - 获取通知列表
- `GET /api/notifications/unread-count` - 获取未读通知数量
- `PUT /api/notifications/{notification_id}/read` - 标记通知已读
- `PUT /api/notifications/mark-all-read` - 标记所有通知已读

## 配置说明

### 环境变量
可以通过环境变量配置以下选项：

```bash
# MySQL 数据库配置（当前使用）
DATABASE_URL=mysql+mysqlclient://root:your_password@localhost:3306/api_project_database

# OpenAI API配置（可选）
OPENAI_API_KEY=your_openai_api_key_here

# JWT配置
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# 开发环境配置
ENVIRONMENT=development
```

## 数据库结构

### MySQL数据库表结构

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| `users` | 用户账户信息 | id, username, email, password_hash, role, is_active |
| `tasks` | API开发任务 | id, user_id, title, description, status, generated_code |
| `notifications` | 系统通知 | id, user_id, task_id, title, content, type, is_read |
| `task_logs` | 任务执行日志 | id, task_id, status, message, created_at |

### 数据库字段说明

**users表**：
- id, username, email, password_hash, role, is_active, created_at, updated_at

**tasks表**：
- id, user_id, title, description, input_params, output_params, status, branch_name, generated_code, test_cases, test_result_image, test_url, admin_comment, created_at, updated_at

**notifications表**：
- id, user_id, task_id, title, content, type, is_read, created_at

**task_logs表**：
- id, task_id, status, message, created_at

### MySQL配置要求

1. **字符集设置**：
   - 数据库字符集：`utf8mb4`
   - 排序规则：`utf8mb4_unicode_ci`
   - 支持emoji和特殊字符

2. **连接池配置**：
   - 连接池大小：10
   - 最大溢出连接：20
   - 连接回收时间：3600秒

### 高级MySQL配置

本项目使用 MySQL 作为关系型数据库，提供以下优势：

- **成熟稳定**：经过多年验证的关系型数据库
- **高性能**：优秀的查询性能和并发处理能力
- **广泛支持**：丰富的工具和社区支持
- **本地控制**：完全控制数据和配置
- **成本效益**：开源免费，无云服务费用
- **可扩展性**：支持从小型项目到企业级应用

**配置步骤：**

1. **安装MySQL服务器**
   - 下载并安装 MySQL 8.0 或更高版本
   - 推荐版本：MySQL 8.0.39（2024年稳定版）
   
2. **创建数据库**
   ```sql
   CREATE DATABASE api_project_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **配置环境变量**
   在 `.env` 文件中设置：
   ```
   DATABASE_URL=mysql+mysqldb://用户名:密码@localhost:3306/数据库名
   ```

4. **安装Python依赖**
   ```bash
   pip install mysqlclient
   ```

5. **测试连接**
   ```bash
   python test_db_connection.py
   ```

6. **初始化数据库**
   ```bash
   python init_database.py
   ```

**⚠️ 重要提示：**
- 确保MySQL服务正在运行
- 请妥善保管数据库密码
- 生产环境建议使用专用数据库用户
- 定期备份重要数据
- 建议启用MySQL的慢查询日志进行性能监控

### AI服务配置
- 默认使用模拟AI响应，适合开发和演示
- 如需使用真实的OpenAI API，请：
  1. 设置 `OPENAI_API_KEY` 环境变量
  2. 修改 `backend/services/ai_service.py` 中的API调用代码

### Docker配置
- 测试环境部署需要Docker服务
- 确保Docker daemon正在运行
- 系统会自动管理测试容器的生命周期

## 开发指南

### 添加新的API端点
1. 在 `backend/routers/` 目录下创建或修改路由文件
2. 在 `backend/schemas.py` 中定义请求/响应模型
3. 在 `backend/main.py` 中注册新路由

### 添加新的数据库模型
1. 在 `backend/models.py` 中定义新模型
2. 运行数据库迁移（或重新初始化）
3. 在相关的API中使用新模型

### 前端页面开发
1. 在 `ai-api-platform/app/` 目录下创建新页面
2. 使用现有的UI组件库（shadcn/ui）
3. 遵循现有的代码风格和结构

## 故障排除

### 常见问题

#### 1. 后端启动失败
- 检查Python版本（需要3.9+）
- 确保所有依赖已安装：`pip install -r requirements.txt`
- 检查数据库是否已初始化：`python init_db.py`

#### 2. 前端启动失败
- 检查Node.js版本（需要18+）
- 清除缓存：`npm cache clean --force`
- 重新安装依赖：`rm -rf node_modules && npm install`

#### 3. Docker相关问题
- 确保Docker服务正在运行
- 检查Docker权限设置
- 查看容器日志：`docker logs <container_name>`

#### 4. MySQL数据库问题
- 检查MySQL服务是否启动：`sudo systemctl status mysql` (Linux) 或 `brew services list | grep mysql` (macOS)
- 测试数据库连接：`mysql -u root -p -h localhost`
- 重新初始化数据库：`python backend/init_db.py`
- 检查数据库用户权限和密码
- 确认数据库字符集为utf8mb4

#### 5. 前端认证问题
- **问题表现**：登录后无法访问受保护页面、API调用返回401错误、token过期等
- **快速修复**：
  1. 打开浏览器开发者工具（F12）
  2. 切换到Console（控制台）标签页
  3. 复制并运行 `ai-api-platform/console_fix.js` 中的代码
  4. 脚本会自动清除过期token并重新登录
  5. 看到"修复完成"提示后刷新页面
- **详细诊断**：使用 `ai-api-platform/fix_frontend_auth.js` 进行完整的认证状态诊断
- **手动修复**：
  ```javascript
  // 清除认证信息
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
  // 然后重新登录
  ```
- **参考文档**：详见 `ai-api-platform/认证问题修复指南.md`

### 日志查看
- 后端日志：控制台输出
- 前端日志：浏览器开发者工具
- Docker日志：`docker logs <container_name>`

## 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 GitHub Issue
- 发送邮件至项目维护者

---

**注意**：这是一个演示项目，请在生产环境使用前进行充分的安全性评估和配置调整。