import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 完全禁用所有日志
import logging
logging.disable(logging.CRITICAL)

from sqlalchemy.orm import sessionmaker
from database import engine
from models import User, Task
from auth_utils import create_access_token, create_user_token
from datetime import datetime, timedelta

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== 为jinqianru生成新的Token ===")
    
    # 查找jinqianru用户
    jinqianru_user = db.query(User).filter(User.username == 'jinqianru').first()
    if jinqianru_user:
        print(f"✅ 找到用户: {jinqianru_user.username} (ID: {jinqianru_user.id})")
        
        # 查看该用户的任务
        user_tasks = db.query(Task).filter(Task.user_id == jinqianru_user.id).all()
        print(f"📋 该用户的任务数量: {len(user_tasks)}")
        
        if user_tasks:
            print("任务列表:")
            for i, task in enumerate(user_tasks, 1):
                print(f"   {i}. [{task.id}] {task.title} (状态: {task.status})")
        
        # 生成新的token（使用正确的格式）
        new_token = create_user_token(jinqianru_user.id, jinqianru_user.username, jinqianru_user.role.value)
        
        print(f"\n🔑 新生成的Token:")
        print(f"{new_token}")
        
        print(f"\n📋 请在浏览器控制台执行以下代码:")
        print(f"localStorage.setItem('access_token', '{new_token}');")
        print(f"location.reload();")
        
        print(f"\n或者复制以下完整代码到浏览器控制台:")
        print(f"localStorage.setItem('access_token', '{new_token}'); location.reload();")
        
    else:
        print("❌ 未找到jinqianru用户")
        
        # 显示所有用户
        all_users = db.query(User).all()
        print(f"\n数据库中的所有用户:")
        for user in all_users:
            print(f"   - {user.username} (ID: {user.id})")
    
except Exception as e:
    print(f"❌ 错误: {e}")
finally:
    db.close()