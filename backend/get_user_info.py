import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 完全禁用SQLAlchemy日志
import logging
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)

from sqlalchemy.orm import sessionmaker
from database import engine
from models import User, Task
from auth_utils import create_access_token

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== 任务显示问题解决方案 ===")
    
    # 查找jinqianru用户（用户ID=7）
    jinqianru_user = db.query(User).filter(User.id == 7).first()
    if jinqianru_user:
        print(f"\n任务创建者信息:")
        print(f"  用户ID: {jinqianru_user.id}")
        print(f"  用户名: {jinqianru_user.username}")
        print(f"  邮箱: {jinqianru_user.email}")
        
        # 查看该用户的任务
        user_tasks = db.query(Task).filter(Task.user_id == jinqianru_user.id).all()
        print(f"  任务数量: {len(user_tasks)}")
        for task in user_tasks:
            print(f"    - {task.title} (ID: {task.id}, 状态: {task.status})")
        
        # 生成该用户的登录token
        token = create_access_token(data={"sub": jinqianru_user.username})
        print(f"\n=== 解决方案 ===")
        print(f"方案1: 重新登录正确的用户")
        print(f"  用户名: {jinqianru_user.username}")
        print(f"  邮箱: {jinqianru_user.email}")
        print(f"\n方案2: 在浏览器控制台中直接设置token")
        print(f"  复制以下代码到浏览器控制台执行:")
        print(f"  localStorage.setItem('token', '{token}');")
        print(f"  location.reload();")
        print(f"\n执行后即可看到任务列表！")
        
    else:
        print("未找到用户ID=7的用户")
    
except Exception as e:
    print(f"获取用户信息时出现错误: {e}")
finally:
    db.close()