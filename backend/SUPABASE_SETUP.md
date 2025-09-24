# Supabase 数据库配置指南

## 🎯 概述

本项目已成功从 SQLite 迁移到 Supabase PostgreSQL 数据库。本指南将帮助你完成最后的配置步骤。

## 📋 已完成的迁移工作

✅ 创建了 `.env` 环境变量文件  
✅ 更新了 `requirements.txt`，添加了 PostgreSQL 驱动  
✅ 修改了 `database.py`，配置了 Supabase 连接  
✅ 验证了数据模型与 PostgreSQL 的兼容性  
✅ 创建了数据库连接测试脚本  

## 🔧 需要你完成的配置

### 步骤 1: 获取数据库密码

1. 访问你的 Supabase 项目: https://supabase.com/dashboard/project/qrfkbxlnharrwlldkztz
2. 点击左侧菜单的 **Settings** (设置)
3. 选择 **Database** 选项卡
4. 在 **Connection string** 部分，你会看到数据库密码
5. 复制这个密码

### 步骤 2: 更新环境变量

1. 打开 `backend/.env` 文件
2. 找到这一行：
   ```
   DATABASE_URL=postgresql://postgres.qrfkbxlnharrwlldkztz:[YOUR_PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```
3. 将 `[YOUR_PASSWORD]` 替换为你在步骤1中获取的实际密码

### 步骤 3: 测试数据库连接

在 `backend` 目录下运行测试脚本：

```bash
cd backend
python test_db_connection.py
```

如果看到 "✅ 数据库连接成功！" 说明配置正确。

### 步骤 4: 启动应用

```bash
python main.py
```

## 🔍 故障排除

### 连接失败的常见原因：

1. **密码错误**: 确保密码复制正确，没有多余的空格
2. **网络问题**: 确保网络连接正常
3. **防火墙**: 确保防火墙允许连接到 Supabase

### 备用连接方式：

如果默认连接失败，可以尝试以下备用方式：

**方法 2: Session pooler (端口 5432)**
```
DATABASE_URL=postgresql://postgres.qrfkbxlnharrwlldkztz:[YOUR_PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```

**方法 3: 直接连接 (需要 SSL 证书)**
```
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.qrfkbxlnharrwlldkztz.supabase.co:5432/postgres
```

## 📊 数据迁移

### 自动表创建

当你首次启动应用时，SQLAlchemy 会自动在 Supabase 中创建以下表：

- `users` - 用户表
- `tasks` - 任务表  
- `notifications` - 通知表
- `task_logs` - 任务日志表

### 现有数据迁移 (可选)

如果你有现有的 SQLite 数据需要迁移，可以：

1. 导出 SQLite 数据为 SQL 文件
2. 在 Supabase SQL 编辑器中执行导入
3. 或者使用数据迁移工具

## 🎉 迁移优势

迁移到 Supabase 后，你的项目将获得：

- **云端托管**: 无需管理数据库服务器
- **自动备份**: 数据安全有保障
- **实时功能**: 支持实时数据订阅
- **更好性能**: PostgreSQL 比 SQLite 性能更强
- **多用户支持**: 支持并发访问
- **可扩展性**: 随业务增长自动扩展

## 📞 需要帮助？

如果遇到问题，请检查：

1. Supabase 项目是否正常运行
2. 网络连接是否正常
3. 密码是否正确
4. 防火墙设置

配置完成后，你的 AI API 开发平台就可以使用强大的 Supabase 数据库了！