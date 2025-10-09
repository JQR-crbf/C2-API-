#!/usr/bin/env python3
"""
数据库迁移脚本：为Task表添加priority字段
为现有任务设置默认优先级为medium
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL, Base
from models import Task, TaskPriority
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_priority():
    """添加priority字段并为现有任务设置默认值"""
    try:
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # 检查priority字段是否已存在（MySQL语法）
            result = db.execute(text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'tasks' 
                AND COLUMN_NAME = 'priority'
            """))
            
            priority_exists = result.fetchone()[0] > 0
            
            if not priority_exists:
                logger.info("添加priority字段到tasks表...")
                
                # 添加priority字段
                db.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN priority VARCHAR(10) DEFAULT 'medium'
                """))
                
                # 为现有任务设置默认优先级
                db.execute(text("""
                    UPDATE tasks 
                    SET priority = 'medium' 
                    WHERE priority IS NULL
                """))
                
                db.commit()
                logger.info("成功添加priority字段并设置默认值")
            else:
                logger.info("priority字段已存在，跳过迁移")
                
            # 验证迁移结果
            result = db.execute(text("SELECT COUNT(*) as count FROM tasks WHERE priority IS NULL"))
            null_count = result.fetchone()[0]
            
            if null_count == 0:
                logger.info("迁移验证成功：所有任务都有优先级")
            else:
                logger.warning(f"发现 {null_count} 个任务没有优先级")
                
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("开始数据库迁移：添加任务优先级字段...")
    migrate_add_priority()
    print("迁移完成！")