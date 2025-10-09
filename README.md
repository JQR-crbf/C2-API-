# AI API 开发自动化平台

这是一个基于AI的API开发自动化平台，能够根据用户需求自动生成API代码、部署测试环境并进行自动化测试。

## 项目概述

### 核心功能
- **用户认证系统**：支持用户注册、登录和权限管理
- **任务管理**：用户可以提交API开发需求，系统自动处理
- **代码生成步骤记录**：将AI代码生成改为手动步骤记录，用户点击按钮完成代码生成步骤
- **增强工作流程引擎**：支持15步完整流程管理，包括代码生成、测试、部署等
- **自动化测试功能**：语法检查、单元测试、API测试和性能测试
- **Git操作自动化**：自动分支创建、代码提交、推送等版本控制操作
- **SSH连接管理**：安全的远程服务器连接和命令执行
- **测试环境部署**：自动部署生成的代码到Docker测试环境
- **管理员审核系统**：完整的任务审核流程，支持通过/拒绝操作，审核记录持久化保存
- **通知系统**：实时通知用户任务进度和状态变化
- **增强用户界面**：错误处理、帮助系统、实时反馈等用户体验改进
- **引导式部署**：提供完整的服务器连接和部署向导功能

### 技术架构
- **前端**：Next.js 14 + React + TypeScript + Tailwind CSS
- **后端**：FastAPI + SQLAlchemy + MySQL
- **数据库**：MySQL 8.0+（推荐本地安装）
- **容器化**：Docker（用于测试环境部署）
- **AI集成**：OpenRouter API（支持多种AI模型）

## 🚀 简单理解：什么是部署会话和服务器连接？

### 部署会话是什么？
**部署会话**就像是一个"工作记录本"，记录了你把AI生成的代码放到服务器上的整个过程。

想象一下：
- 你有一个AI生成的网站代码
- 你想把这个网站放到服务器上让别人能访问
- 部署会话就是记录这个"搬家"过程的每一步

### 服务器连接是什么？
**服务器连接**就是让你的电脑能够"远程控制"另一台电脑（服务器）。

就像：
- 你在家里的电脑上
- 通过网络连接到公司的电脑
- 然后可以在公司电脑上运行程序、复制文件等

### 为什么需要连接数据库？
这里的"数据库"不是指你要连接的服务器，而是指：
- 系统需要把你的部署过程记录下来
- 比如：连接了哪台服务器、执行了什么命令、是否成功等
- 这些信息都保存在系统自己的数据库里

### 简单来说：
1. **部署会话** = 记录你部署代码的整个过程
2. **服务器连接** = 让你能远程操作目标服务器
3. **数据库连接** = 系统保存这些操作记录的地方

你只需要关心：**输入服务器的IP地址、用户名、密码，系统就会帮你连接并部署代码！**

## 📋 如何连接到你的服务器？

### 第一步：准备服务器信息
你需要知道以下信息：
- **服务器地址**：比如 `192.168.1.100` 或 `myserver.com`
- **端口号**：通常是 `22`（SSH默认端口）
- **用户名**：比如 `root` 或 `ubuntu`
- **认证方式**：密码或SSH密钥
  - **密码**：你的服务器登录密码
  - **SSH密钥**：私钥文件内容（更安全的连接方式）
- **部署路径**：代码要放在服务器的哪个文件夹，比如 `/home/api_projects`

### 🔐 SSH密钥连接（推荐）

**什么是SSH密钥？**
SSH密钥是一种更安全的服务器连接方式，比密码更安全，不容易被破解。

**如何使用SSH密钥？**
1. 从你的云服务器提供商（如华为云、阿里云）下载私钥文件
2. 打开私钥文件，复制全部内容
3. 在系统中选择"SSH密钥"认证方式
4. 将私钥内容粘贴到"SSH私钥"文本框中

**预设服务器配置**
系统已预配置两台华为云服务器：
- **服务器1 - 主平台**：113.44.82.13（运行AI API开发平台）
- **服务器2 - API部署**：124.70.0.110（专门部署AI生成的API代码）

你可以直接选择预设服务器，系统会自动填入配置信息。

### 第二步：在系统中填写信息
1. 打开任务详情页面
2. 点击"引导部署"按钮
3. 在弹出的"服务器配置"对话框中填写：
   - 服务器地址：`你的服务器IP`
   - 端口：`22`
   - 用户名：`你的用户名`
   - 密码：`你的密码`
   - 部署路径：`/home/api_projects`
4. 点击"连接服务器"按钮

### 第三步：等待自动部署
系统会自动：
1. 连接到你的服务器
2. 创建必要的文件夹
3. 上传AI生成的代码
4. 安装依赖包
5. 启动你的API服务

### 常见问题解答

**Q: 我没有服务器怎么办？**
A: 你可以：
- 使用云服务器（如阿里云、腾讯云）
- 使用本地虚拟机
- 先用系统默认的测试服务器体验功能

**Q: 连接失败怎么办？**
A: 检查：
- 服务器地址是否正确
- 用户名和密码是否正确
- 服务器是否开启SSH服务
- 网络是否畅通

**Q: 部署失败怎么办？**
A: 系统会显示详细的错误信息，你可以：
- 查看终端输出了解具体错误
- 检查服务器权限设置
- 确保服务器有足够的磁盘空间

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
   │   ├── ui/              # 基础UI组件
   │   ├── enhanced-error-handler.tsx # 增强错误处理
   │   ├── help-system.tsx  # 帮助系统
   │   ├── real-time-feedback.tsx # 实时反馈
   │   └── guided-deployment.tsx # 引导式部署组件
   └── public/              # 静态资源
├── backend/                  # 后端项目
│   ├── routers/             # API路由
│   │   ├── auth.py          # 认证相关API
│   │   ├── tasks.py         # 任务管理API
│   │   ├── admin.py         # 管理员API
│   │   ├── notifications.py # 通知API
│   │   ├── workflow.py      # 工作流程管理API
│   │   ├── git_router.py    # Git操作API
│   │   ├── ai_router.py     # AI服务API
│   │   └── test_router.py   # 自动化测试API
│   ├── services/            # 业务服务
│   │   ├── ai_service.py    # AI代码生成服务
│   │   ├── test_service.py  # 测试环境服务
│   │   ├── task_processor.py # 后台任务处理器
│   │   ├── workflow_engine.py # 工作流程引擎
│   │   ├── git_service.py   # Git操作服务
│   │   └── ssh_service.py   # SSH连接服务
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # API数据模式
│   ├── database.py          # 数据库配置
│   ├── auth_utils.py        # 认证工具
│   ├── main.py              # 应用入口
│   └── init_db.py           # 数据库初始化脚本
└── README.md                # 项目说明文档
```

## 最新更新

### 2025年1月最新修复和改进

#### ✅ 已完成的修复
1. **数据库模型优化**：修复User模型缺少full_name字段的问题，完善API响应数据
2. **权限管理修复**：将admin用户角色正确设置为admin，确保管理员功能正常
3. **前端语法修复**：解决guided-deployment.tsx组件的JSX语法错误
4. **工作流程引擎优化**：完善task_workflow_service.py中的步骤检查逻辑
5. **数据库配置统一**：清理项目中混乱的MySQL/SQLite配置，统一使用mysql+mysqldb驱动
6. **引导式部署功能**：完善服务器连接和部署向导功能
7. **API路径修复**：修正前端deployment相关API调用路径不匹配问题，解决404错误

#### 🔧 技术改进
- 统一所有配置文件中的数据库连接字符串格式
- 移除SQLite相关的残留配置
- 优化前端组件的错误处理机制
- 完善数据库模型与实际表结构的一致性
- 修正前端API调用路径，确保与后端路由配置一致
- 添加Authorization头部认证，提升API安全性

#### 📋 当前状态
- ✅ 前端服务器：正常运行在 http://localhost:3000
- ✅ 后端服务器：正常运行在 http://localhost:8080
- ✅ 数据库连接：MySQL配置统一且稳定
- ✅ 所有核心功能：测试通过并可正常使用

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
   - 格式：`mysql+mysqldb://username:password@host:port/database_name`
   - 示例：`mysql+mysqldb://root:CRBF261900jqr@localhost:3306/api_project_database`

4. **初始化数据库**：
```bash
cd backend
python init_db.py
```

#### 启动后端服务
```bash
python main.py
```

后端服务将在 `http://localhost:8080` 启动

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

### 默认用户账户

系统初始化后会创建以下默认账户：

| 用户名 | 邮箱 | 密码 | 角色 | 状态 |
|--------|------|------|------|------|
| admin | admin@example.com | admin123 | admin | 激活 |
| testuser | test@example.com | test123 | user | 激活 |

### 关键信息
- **admin用户**：拥有管理员权限，可以审核任务和管理用户
- **testuser用户**：普通用户，可以创建和管理自己的任务
- 首次运行时请使用这些默认账户登录
- 登录后建议修改默认密码

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
- **Swagger UI**：`http://localhost:8080/docs`
- **ReDoc**：`http://localhost:8080/redoc`

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

#### 自动化测试功能
- `POST /api/test/syntax-check` - 语法检查
- `POST /api/test/unit-test` - 单元测试
- `POST /api/test/api-test` - API测试
- `POST /api/test/performance-test` - 性能测试
- `POST /api/test/full-test` - 综合测试

#### 工作流程管理
- `POST /api/workflow/sessions` - 创建工作流程会话
- `GET /api/workflow/sessions/{session_id}` - 获取会话详情
- `POST /api/workflow/sessions/{session_id}/execute` - 执行工作流程
- `GET /api/workflow/sessions/{session_id}/steps` - 获取步骤列表

#### Git操作
- `POST /api/git/create-branch` - 创建分支
- `POST /api/git/commit` - 提交代码
- `POST /api/git/push` - 推送代码
- `GET /api/git/status` - 获取Git状态

#### AI服务
- `POST /api/ai/generate-code` - 生成代码
- `POST /api/ai/fix-issues` - 修复问题
- `POST /api/ai/optimize-code` - 优化代码

## 配置说明

### 环境变量
可以通过环境变量配置以下选项：

```bash
# MySQL 数据库配置
DATABASE_URL=mysql+mysqldb://root:CRBF261900jqr@localhost:3306/api_project_database

# AI服务配置（OpenRouter）
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=anthropic/claude-3-5-sonnet-20241022

# JWT配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 开发环境配置
ENVIRONMENT=development
DEBUG=True
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
- id, user_id, title, description, input_params, output_params, status, branch_name, generated_code, test_cases, test_result_image, test_url, test_status, test_results, admin_comment, created_at, updated_at

**notifications表**：
- id, user_id, task_id, title, content, type, is_read, created_at

**task_logs表**：
- id, task_id, status, message, created_at

**workflow_sessions表**：
- id, task_id, session_name, current_step, total_steps, status, created_at, updated_at

**workflow_steps表**：
- id, session_id, step_number, step_name, step_type, status, input_data, output_data, error_message, started_at, completed_at

**step_actions表**：
- id, step_id, action_type, action_data, status, result, created_at

### 🔍 数据库类型映射说明

**重要提示**：本项目使用MySQL数据库，存在以下类型映射行为：

#### BOOLEAN字段的MySQL映射
SQLAlchemy模型中定义的`Boolean`类型字段，在MySQL中会自动映射为`TINYINT(1)`类型：

| SQLAlchemy模型定义 | MySQL实际存储 | 说明 |
|-------------------|---------------|------|
| `Boolean` | `TINYINT(1)` | MySQL标准行为 |
| `True` | `1` | 布尔真值 |
| `False` | `0` | 布尔假值 |

#### 受影响的字段
以下字段在模型中定义为Boolean，在数据库中存储为TINYINT(1)：
- `users.is_active` - 用户激活状态
- `notifications.is_read` - 通知已读状态
- `workflow_steps.requires_user_input` - 步骤是否需要用户输入
- `step_actions.is_validated` - 动作是否已验证

#### 功能影响
- ✅ **应用功能完全正常**：SQLAlchemy自动处理类型转换
- ✅ **API返回正确**：布尔值在JSON中正确序列化为true/false
- ✅ **数据存储正确**：TINYINT(1)完全支持布尔值存储
- ⚠️ **文档差异**：模型定义与数据库schema存在类型描述差异

#### 开发注意事项
1. 这种类型映射是MySQL的标准行为，不是错误
2. 在编写SQL查询时，布尔字段使用0/1值
3. 在Python代码中，继续使用True/False值
4. 静态分析工具可能会标记类型不一致，这是正常现象

### 数据库一致性检查

项目提供了自动化的数据库模型检查工具：

```bash
# 运行全面的模型与数据库对比检查
cd backend
python comprehensive_model_check.py
```

该工具会：
- 检查所有表结构与模型定义的匹配情况
- 识别缺失或多余的表和字段
- 生成详细的对比报告
- 提供修复建议

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
   DATABASE_URL=mysql+mysqldb://root:CRBF261900jqr@localhost:3306/api_project_database
   ```

4. **安装Python依赖**
   ```bash
   pip install mysqlclient>=2.2.0
   ```
   
   **注意**：项目使用 `mysql+mysqldb` 驱动，需要安装 `mysqlclient` 包

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
- 项目统一使用 `mysql+mysqldb` 驱动，确保配置一致性
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

## 🔧 管理员审核功能使用指南

### 功能概述
管理员审核系统是任务工作流程中的重要环节，允许具有管理员权限的用户对处于"管理员审核"状态的任务进行审核操作。

### 使用步骤

#### 1. 管理员登录
- 使用管理员账户登录系统
- 确认用户角色为 `admin`
- 默认管理员账户：用户名 `admin`，密码 `admin123`

#### 2. 访问任务审核
- 进入任务详情页面：`http://localhost:3000/tasks/{task_id}`
- 点击"进度"标签页查看任务工作流程
- 找到"管理员审核"步骤

#### 3. 执行审核操作

**审核通过：**
- 点击绿色的"通过"按钮
- 系统显示成功提示
- 任务状态自动更新为"已部署"
- 工作流程进入下一步

**审核拒绝：**
- 点击红色的"拒绝"按钮
- 在弹出的对话框中填写拒绝理由（必填）
- 点击"确认拒绝"按钮
- 任务状态回退到"代码生成中"
- 系统自动发送通知给任务创建者

### 功能特点
- **权限控制**：只有管理员用户才能看到审核按钮
- **状态验证**：只有处于"under_review"状态的任务才能进行审核
- **数据持久化**：审核结果、状态变更、日志记录都会永久保存
- **通知系统**：审核结果会自动通知任务创建者
- **错误处理**：完整的错误捕获和用户友好的提示

### API接口
- **审核接口**：`POST /api/admin/tasks/{task_id}/review`
- **参数**：
  - `action`: "approve" 或 "reject"
  - `comment`: 审核意见（拒绝时必填）
- **权限要求**：需要管理员身份认证

### 测试指南
详细的测试步骤和验证方法请参考：`管理员审核功能测试指南.md`

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

## 更新日志

### 2025-09-28 - 管理员删除任务功能
**功能描述：** 为管理员添加删除任务的功能，允许管理员删除任何状态的任务

**主要修改：**
1. **后端API接口：**
   - 在 `backend/routers/admin.py` 中添加 `DELETE /api/admin/tasks/{task_id}` 接口
   - 实现管理员权限验证，只有管理员可以删除任务
   - 删除任务时会先清理相关的日志和通知数据，避免数据库完整性错误
   - 删除后会向任务所有者发送通知

2. **前端API客户端：**
   - 在 `ai-api-platform/lib/api.ts` 中添加 `admin.deleteTask()` 方法
   - 支持调用后端删除任务接口

3. **前端管理员界面：**
   - 在 `ai-api-platform/app/admin/page.tsx` 中添加删除任务按钮
   - 在任务操作下拉菜单中增加"删除任务"选项
   - 添加删除确认对话框，包含警告信息和任务标题显示
   - 实现删除成功后的提示和数据刷新

**使用方法：**
1. 管理员登录后进入管理员页面
2. 在任务列表中找到要删除的任务
3. 点击任务操作按钮（三个点图标）
4. 选择"删除任务"选项
5. 在确认对话框中点击"确认删除"
6. 系统会显示删除成功提示，任务列表会自动刷新

**技术细节：**
- 删除操作会清理任务相关的所有数据（日志、通知等）
- 删除后会向任务所有者发送通知
- 前端包含完整的错误处理和用户反馈
- 支持任何状态的任务删除（与普通用户删除限制不同）

### 2025-09-28 - 代码生成步骤功能修改
**重要功能更新：将AI代码生成改为手动步骤记录**

#### 修改内容
1. **后端接口修改**
   - 修改 `regenerate_task_code` 接口，不再调用AI生成代码
   - 直接将任务状态从 `submitted` 更新为 `test_ready`
   - 返回消息改为"代码生成步骤已完成"

2. **任务状态流转优化**
   - 简化状态流转：`submitted` → `test_ready`
   - 跳过 `ai_generating` 状态，直接进入测试准备阶段
   - 保持工作流程的连续性

3. **前端界面更新**
   - 按钮文本：从"生成代码"改为"完成代码生成步骤"
   - 按钮描述：从"代码生成"改为"代码生成步骤"
   - 加载状态：从"正在生成代码..."改为"正在记录步骤..."
   - 成功提示：从"代码生成已开始"改为"代码生成步骤已完成"

4. **状态显示统一**
   - 任务工作流组件中的状态显示更新
   - 任务状态工具函数中的映射更新
   - 保持界面显示的一致性

#### 使用说明
- 用户在任务详情页面点击"完成代码生成步骤"按钮
- 系统记录该步骤完成，任务状态更新为"代码生成步骤"
- 用户可以继续进行后续的测试和部署操作

#### 技术细节
- 修改文件：`backend/routers/tasks.py`、`backend/services/task_workflow_service.py`
- 前端文件：`ai-api-platform/app/tasks/[id]/page.tsx`、相关组件和工具函数
- 保持API接口兼容性，仅修改内部逻辑

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