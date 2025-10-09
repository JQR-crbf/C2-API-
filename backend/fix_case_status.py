#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_status_case():
    """修复数据库中的状态值大小写"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 查看当前状态
        result = conn.execute(text("SELECT DISTINCT status FROM tasks"))
        current_statuses = [row[0] for row in result]
        logger.info(f"当前数据库中的状态: {current_statuses}")
        
        # 修复小写状态为大写
        status_fixes = {
            'code_submitted': 'CODE_SUBMITTED',
            'ai_generating': 'AI_GENERATING',
            'submitted': 'SUBMITTED',
            'under_review': 'UNDER_REVIEW',
            'deployed': 'DEPLOYED',
            'approved': 'APPROVED',
            'rejected': 'REJECTED'
        }
        
        total_updated = 0
        for old_status, new_status in status_fixes.items():
            if old_status in current_statuses:
                result = conn.execute(
                    text("UPDATE tasks SET status = :new_status WHERE status = :old_status"),
                    {"new_status": new_status, "old_status": old_status}
                )
                updated_count = result.rowcount
                if updated_count > 0:
                    logger.info(f"将 {updated_count} 个任务从 '{old_status}' 更新为 '{new_status}'")
                    total_updated += updated_count
                    
                    # 同时更新task_logs表
                    conn.execute(
                        text("UPDATE task_logs SET status = :new_status WHERE status = :old_status"),
                        {"new_status": new_status, "old_status": old_status}
                    )
        
        conn.commit()
        logger.info(f"状态修复完成！共更新了 {total_updated} 个任务")
        
        # 验证修复结果
        result = conn.execute(text("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
        logger.info("修复后的状态分布:")
        for row in result:
            logger.info(f"  {row[0]}: {row[1]} 个任务")

if __name__ == "__main__":
    fix_status_case()