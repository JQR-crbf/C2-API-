#!/usr/bin/env python3
"""
修复数据库status字段长度问题
"""

from database import get_db
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_status_column():
    """修复status字段长度"""
    db = next(get_db())
    
    try:
        # 检查当前字段定义
        result = db.execute(text("DESCRIBE tasks"))
        columns = result.fetchall()
        
        for column in columns:
            if column[0] == 'status':
                logger.info(f"当前status字段定义: {column}")
                break
        
        # 修改字段长度
        logger.info("正在修改status字段长度...")
        db.execute(text("ALTER TABLE tasks MODIFY COLUMN status VARCHAR(50) NOT NULL"))
        
        # 同样修改task_logs表的status字段
        logger.info("正在修改task_logs表的status字段长度...")
        db.execute(text("ALTER TABLE task_logs MODIFY COLUMN status VARCHAR(50) NOT NULL"))
        
        db.commit()
        logger.info("字段长度修改完成！")
        
        # 验证修改结果
        result = db.execute(text("DESCRIBE tasks"))
        columns = result.fetchall()
        
        for column in columns:
            if column[0] == 'status':
                logger.info(f"修改后status字段定义: {column}")
                break
                
    except Exception as e:
        logger.error(f"修改字段过程中发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("开始修复status字段长度...")
    fix_status_column()
    logger.info("status字段长度修复完成！")