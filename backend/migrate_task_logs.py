#!/usr/bin/env python3
"""
数据库迁移脚本：为task_logs表添加新字段
"""

from database import get_db
from sqlalchemy import text

def migrate_task_logs():
    """迁移task_logs表，添加user_id和action_type字段"""
    db = next(get_db())
    
    try:
        # 添加user_id字段
        try:
            db.execute(text('ALTER TABLE task_logs ADD COLUMN user_id INT NULL'))
            print('✅ 添加user_id字段成功')
        except Exception as e:
            print(f'⚠️ user_id字段可能已存在: {e}')
        
        # 添加action_type字段
        try:
            db.execute(text("ALTER TABLE task_logs ADD COLUMN action_type VARCHAR(50) NOT NULL DEFAULT 'system'"))
            print('✅ 添加action_type字段成功')
        except Exception as e:
            print(f'⚠️ action_type字段可能已存在: {e}')
        
        # 添加外键约束
        try:
            db.execute(text('ALTER TABLE task_logs ADD FOREIGN KEY (user_id) REFERENCES users(id)'))
            print('✅ 添加外键约束成功')
        except Exception as e:
            print(f'⚠️ 外键约束可能已存在: {e}')
        
        # 更新现有记录的action_type
        try:
            db.execute(text("UPDATE task_logs SET action_type = 'system' WHERE action_type IS NULL OR action_type = ''"))
            print('✅ 更新现有记录的action_type成功')
        except Exception as e:
            print(f'⚠️ 更新现有记录失败: {e}')
        
        db.commit()
        print('🎉 数据库迁移完成')
        
    except Exception as e:
        db.rollback()
        print(f'❌ 迁移失败: {e}')
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_task_logs()