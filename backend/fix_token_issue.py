import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 完全禁用所有日志
import logging
logging.disable(logging.CRITICAL)

from sqlalchemy.orm import sessionmaker
from database import engine
from models import User, Task
from auth_utils import create_access_token

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== 修复Token问题 ===")
    
    # 1. 查找jinqianru用户
    jinqianru_user = db.query(User).filter(User.username == 'jinqianru').first()
    if jinqianru_user:
        print(f"✅ 找到jinqianru用户 (ID: {jinqianru_user.id})")
        
        # 查看该用户的任务
        user_tasks = db.query(Task).filter(Task.user_id == jinqianru_user.id).all()
        print(f"📋 jinqianru的任务数量: {len(user_tasks)}")
        
        if user_tasks:
            for task in user_tasks:
                print(f"   - [{task.id}] {task.title} (状态: {task.status})")
        
        # 生成token
        token = create_access_token(data={"sub": jinqianru_user.username})
        print(f"\n🔑 正确的解决方案 - 在浏览器控制台执行:")
        print(f"localStorage.setItem('access_token', '{token}'); location.reload();")
        print(f"\n注意：前端API客户端读取的是'access_token'，不是'token'！")
        
    else:
        print("❌ 未找到jinqianru用户")
    
    # 2. 检查当前登录的用户（testuser）
    testuser = db.query(User).filter(User.username == 'testuser').first()
    if testuser:
        print(f"\n📝 当前登录用户: testuser (ID: {testuser.id})")
        testuser_tasks = db.query(Task).filter(Task.user_id == testuser.id).all()
        print(f"   testuser的任务数量: {len(testuser_tasks)}")
        
        if len(testuser_tasks) == 0:
            print("   ✅ 确认：testuser没有任务，这是正确的")
    
    print(f"\n=== 问题分析 ===")
    print(f"1. 数据库中jinqianru用户确实有{len(user_tasks)}个任务")
    print(f"2. 前端当前登录的是testuser用户，该用户没有任务")
    print(f"3. 前端API客户端从localStorage读取'access_token'")
    print(f"4. 需要用jinqianru的token替换当前的token")
    
except Exception as e:
    print(f"❌ 错误: {e}")
finally:
    db.close()