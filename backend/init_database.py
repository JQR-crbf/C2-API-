#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库初始化脚本
用于创建所有数据库表结构
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from database import Base, engine
from models import User, Task, Notification, TaskLog, UserRole, DeploymentSession, DeploymentStep
from auth_utils import get_password_hash

def init_database():
    """
    初始化数据库表结构
    """
    print("🚀 开始初始化MySQL数据库...")
    print("=" * 50)
    
    try:
        # 创建所有表
        print("🏗️ 创建数据库表结构...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        
        # 检查创建的表
        with engine.connect() as connection:
            tables_result = connection.execute(text("""
                SHOW TABLES
            """))
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"\n📋 已创建的表: {', '.join(tables)}")
            
            # 检查每个表的结构
            for table in tables:
                print(f"\n🔍 检查表 '{table}' 结构:")
                columns_result = connection.execute(text(f"DESCRIBE {table}"))
                columns = columns_result.fetchall()
                for col in columns:
                    field, type_, null, key, default, extra = col
                    key_info = f" ({key})" if key else ""
                    print(f"  - {field}: {type_}{key_info}")
        
        # 创建默认管理员用户
        print("\n👤 创建默认管理员用户...")
        create_default_admin()
        
        print("\n🎉 数据库初始化完成！")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def create_default_admin():
    """
    创建默认管理员用户
    """
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(
            User.role == UserRole.ADMIN
        ).first()
        
        if existing_admin:
            print(f"✅ 管理员用户已存在: {existing_admin.username}")
            return
        
        # 创建默认管理员
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ 默认管理员用户创建成功!")
        print(f"   用户名: admin")
        print(f"   密码: admin123")
        print(f"   邮箱: admin@example.com")
        print(f"   ⚠️ 请在生产环境中修改默认密码！")
        
    except SQLAlchemyError as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def check_database_status():
    """
    检查数据库状态
    """
    print("\n🔍 检查数据库状态...")
    print("=" * 30)
    
    try:
        with engine.connect() as connection:
            # 检查表数量
            tables_result = connection.execute(text("SHOW TABLES"))
            table_count = len(tables_result.fetchall())
            print(f"📊 数据库表数量: {table_count}")
            
            # 检查用户数量
            user_count_result = connection.execute(text("SELECT COUNT(*) FROM users"))
            user_count = user_count_result.fetchone()[0]
            print(f"👥 用户数量: {user_count}")
            
            # 检查任务数量
            task_count_result = connection.execute(text("SELECT COUNT(*) FROM tasks"))
            task_count = task_count_result.fetchone()[0]
            print(f"📝 任务数量: {task_count}")
            
            # 检查通知数量
            notification_count_result = connection.execute(text("SELECT COUNT(*) FROM notifications"))
            notification_count = notification_count_result.fetchone()[0]
            print(f"🔔 通知数量: {notification_count}")
            
            # 检查日志数量
            log_count_result = connection.execute(text("SELECT COUNT(*) FROM task_logs"))
            log_count = log_count_result.fetchone()[0]
            print(f"📋 日志数量: {log_count}")
            
    except SQLAlchemyError as e:
        print(f"❌ 检查数据库状态失败: {e}")

def main():
    """
    主函数
    """
    print("🗄️ MySQL数据库初始化工具")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 初始化数据库
    success = init_database()
    
    if success:
        # 检查数据库状态
        check_database_status()
        
        print("\n" + "=" * 50)
        print("🎉 数据库初始化成功！")
        print("\n📋 下一步操作:")
        print("1. 运行 python main.py 启动API服务")
        print("2. 访问 http://localhost:8000/docs 查看API文档")
        print("3. 使用默认管理员账号登录: admin / admin123")
        sys.exit(0)
    else:
        print("\n💥 数据库初始化失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()