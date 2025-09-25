#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署功能数据库迁移脚本
添加引导部署相关的表结构
"""

import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from database import engine, SessionLocal
from models import DeploymentSession, DeploymentStep, DeploymentConnectionStatus, DeploymentStepStatus

def check_table_exists(table_name):
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate_deployment_tables():
    """
    迁移部署相关表
    """
    print("🚀 开始部署功能数据库迁移...")
    print("=" * 50)
    
    try:
        # 检查是否需要迁移
        tables_to_check = ['deployment_sessions', 'deployment_steps']
        existing_tables = []
        missing_tables = []
        
        for table in tables_to_check:
            if check_table_exists(table):
                existing_tables.append(table)
            else:
                missing_tables.append(table)
        
        if not missing_tables:
            print("✅ 所有部署相关表已存在，无需迁移")
            return True
        
        print(f"📋 需要创建的表: {', '.join(missing_tables)}")
        if existing_tables:
            print(f"📋 已存在的表: {', '.join(existing_tables)}")
        
        # 创建新表
        print("\n🏗️ 创建部署相关表...")
        
        # 只创建部署相关的表
        DeploymentSession.__table__.create(engine, checkfirst=True)
        DeploymentStep.__table__.create(engine, checkfirst=True)
        
        print("✅ 部署表创建成功！")
        
        # 验证表结构
        print("\n🔍 验证新创建的表结构:")
        with engine.connect() as connection:
            for table_name in ['deployment_sessions', 'deployment_steps']:
                if check_table_exists(table_name):
                    print(f"\n📊 表 '{table_name}' 结构:")
                    columns_result = connection.execute(text(f"DESCRIBE {table_name}"))
                    columns = columns_result.fetchall()
                    for col in columns:
                        field, type_, null, key, default, extra = col
                        key_info = f" ({key})" if key else ""
                        null_info = "NOT NULL" if null == "NO" else "NULL"
                        print(f"  - {field}: {type_} {null_info}{key_info}")
        
        print("\n🎉 部署功能迁移完成！")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 迁移失败: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_deployment_tables():
    """
    测试部署相关表的基本功能
    """
    print("\n🧪 测试部署表功能...")
    
    db = SessionLocal()
    try:
        # 测试创建部署会话
        test_session = DeploymentSession(
            task_id=1,  # 假设存在任务ID 1
            user_id=1,  # 假设存在用户ID 1
            server_host="test.example.com",
            server_port=22,
            server_username="testuser",
            deployment_path="/home/testuser/test_project"
        )
        
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        
        print(f"✅ 测试部署会话创建成功 (ID: {test_session.id})")
        
        # 测试创建部署步骤
        test_step = DeploymentStep(
            session_id=test_session.id,
            step_number=1,
            step_name="测试步骤",
            step_description="这是一个测试步骤",
            command="echo 'test'",
            expected_output="test"
        )
        
        db.add(test_step)
        db.commit()
        db.refresh(test_step)
        
        print(f"✅ 测试部署步骤创建成功 (ID: {test_step.id})")
        
        # 清理测试数据
        db.delete(test_step)
        db.delete(test_session)
        db.commit()
        
        print("✅ 测试数据清理完成")
        print("✅ 部署表功能测试通过！")
        
    except SQLAlchemyError as e:
        print(f"❌ 测试失败: {e}")
        db.rollback()
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

def rollback_deployment_tables():
    """
    回滚部署相关表（删除表）
    """
    print("\n⚠️ 警告：即将删除部署相关表！")
    confirm = input("确定要继续吗？(输入 'yes' 确认): ")
    
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False
    
    try:
        print("🗑️ 删除部署相关表...")
        
        with engine.connect() as connection:
            # 删除表（注意顺序，先删除有外键的表）
            tables_to_drop = ['deployment_steps', 'deployment_sessions']
            
            for table in tables_to_drop:
                if check_table_exists(table):
                    connection.execute(text(f"DROP TABLE {table}"))
                    print(f"✅ 表 '{table}' 已删除")
                else:
                    print(f"⚠️ 表 '{table}' 不存在，跳过")
            
            connection.commit()
        
        print("✅ 回滚完成")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 回滚失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("🗄️ 部署功能数据库迁移工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "rollback":
            success = rollback_deployment_tables()
        elif command == "test":
            success = migrate_deployment_tables()
            if success:
                success = test_deployment_tables()
        else:
            print(f"❌ 未知命令: {command}")
            print("可用命令:")
            print("  python migrate_deployment_tables.py        - 执行迁移")
            print("  python migrate_deployment_tables.py test   - 执行迁移并测试")
            print("  python migrate_deployment_tables.py rollback - 回滚迁移")
            sys.exit(1)
    else:
        success = migrate_deployment_tables()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 操作完成！")
        if len(sys.argv) <= 1 or sys.argv[1] != "rollback":
            print("\n📋 下一步操作:")
            print("1. 重启 API 服务")
            print("2. 在任务详情页面查看新的'引导部署'标签")
            print("3. 测试引导部署功能")
        sys.exit(0)
    else:
        print("\n💥 操作失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
