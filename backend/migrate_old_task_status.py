#!/usr/bin/env python3
"""
数据库任务状态迁移脚本
将旧的复杂工作流状态迁移到新的简化5步骤状态
"""

from database import get_db
from models import Task, TaskStatus
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 状态映射关系 - 注意：数据库中存储的是大写值
STATUS_MAPPING = {
    # 旧状态 -> 新状态（使用大写值）
    'CODE_PULLING': 'AI_GENERATING',
    'BRANCH_CREATED': 'AI_GENERATING', 
    'TEST_READY': 'CODE_SUBMITTED',
    'TESTING': 'CODE_SUBMITTED',
    'TEST_COMPLETED': 'CODE_SUBMITTED',
    'CODE_PUSHED': 'UNDER_REVIEW',
    'COMPLETED': 'DEPLOYED',
    # 保持不变的状态
    'SUBMITTED': 'SUBMITTED',
    'AI_GENERATING': 'AI_GENERATING',
    'CODE_SUBMITTED': 'CODE_SUBMITTED',
    'UNDER_REVIEW': 'UNDER_REVIEW',
    'DEPLOYED': 'DEPLOYED',
    'APPROVED': 'APPROVED',
    'REJECTED': 'REJECTED'
}

def migrate_task_status():
    """迁移任务状态"""
    db = next(get_db())
    
    try:
        # 首先查看所有任务的当前状态
        result = db.execute(text("SELECT DISTINCT status FROM tasks"))
        current_statuses = [row[0] for row in result.fetchall()]
        logger.info(f"数据库中发现的状态: {current_statuses}")
        
        # 统计需要迁移的任务
        migration_count = 0
        
        for old_status in current_statuses:
            if old_status in STATUS_MAPPING:
                new_status = STATUS_MAPPING[old_status]
                
                # 如果状态需要改变
                if old_status != new_status:
                    # 更新任务状态
                    result = db.execute(
                        text("UPDATE tasks SET status = :new_status WHERE status = :old_status"),
                        {"new_status": new_status, "old_status": old_status}
                    )
                    affected_rows = result.rowcount
                    migration_count += affected_rows
                    logger.info(f"将 {affected_rows} 个任务从 '{old_status}' 迁移到 '{new_status}'")
                    
                    # 同时更新task_logs表
                    db.execute(
                        text("UPDATE task_logs SET status = :new_status WHERE status = :old_status"),
                        {"new_status": new_status, "old_status": old_status}
                    )
                    logger.info(f"同时更新了task_logs表中的相关记录")
            else:
                logger.warning(f"未知状态 '{old_status}' 需要手动处理")
        
        # 提交更改
        db.commit()
        logger.info(f"迁移完成！共更新了 {migration_count} 个任务的状态")
        
        # 验证迁移结果
        result = db.execute(text("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
        status_counts = result.fetchall()
        logger.info("迁移后的状态分布:")
        for status, count in status_counts:
            logger.info(f"  {status}: {count} 个任务")
            
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("开始任务状态迁移...")
    migrate_task_status()
    logger.info("任务状态迁移完成！")