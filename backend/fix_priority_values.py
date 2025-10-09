from database import get_db
from models import Task
from sqlalchemy import text

def fix_priority_values():
    """修复数据库中的优先级值"""
    db = next(get_db())
    
    try:
        # 更新小写的优先级值为大写
        db.execute(text("UPDATE tasks SET priority = 'MEDIUM' WHERE priority = 'medium' OR priority IS NULL"))
        db.execute(text("UPDATE tasks SET priority = 'HIGH' WHERE priority = 'high'"))
        db.execute(text("UPDATE tasks SET priority = 'LOW' WHERE priority = 'low'"))
        
        db.commit()
        print("Priority values updated successfully")
        
        # 验证更新结果
        result = db.execute(text("SELECT COUNT(*) as count FROM tasks")).fetchone()
        print(f"Total tasks: {result.count}")
        
        # 显示优先级分布
        priorities = db.execute(text("SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority")).fetchall()
        for priority in priorities:
            print(f"Priority {priority.priority}: {priority.count} tasks")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_priority_values()