import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import get_db
from models import User, UserRole
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
import requests
import json

# 后端API地址
API_BASE_URL = "http://localhost:8000"

def create_test_user():
    """创建一个测试用户"""
    db = next(get_db())
    
    # 检查是否已存在测试用户
    existing_user = db.query(User).filter(User.username == "testuser").first()
    
    if existing_user:
        print(f"测试用户已存在: {existing_user.username} (邮箱: {existing_user.email})")
        return existing_user.email, "testpassword"
    
    # 创建新的测试用户
    password = "testpassword"
    hashed_password = generate_password_hash(password)
    
    new_user = User(
        username="testuser2",
        email="test2@test.com",
        password_hash=hashed_password,
        role=UserRole.USER,
        is_active=True
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"创建测试用户成功: {new_user.username} (ID: {new_user.id})")
        return "test2@test.com", "testpassword"
    except Exception as e:
        db.rollback()
        print(f"创建用户失败: {e}")
        return None, None

def create_new_test_user():
    """创建一个全新的测试用户"""
    db = next(get_db())
    
    # 使用时间戳创建唯一用户名
    import time
    timestamp = str(int(time.time()))
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@test.com"
    password = "testpassword123"
    
    hashed_password = generate_password_hash(password)
    
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        role=UserRole.USER,
        is_active=True
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"创建新测试用户成功: {new_user.username} (邮箱: {new_user.email})")
        return email, password, username
    except Exception as e:
        db.rollback()
        print(f"创建用户失败: {e}")
        return None, None, None

def test_login_and_get_tasks():
    """测试登录并获取任务"""
    # 创建全新的测试用户
    username, password, actual_username = create_new_test_user()
    
    if not username or not password:
        print("无法创建测试用户")
        return
    
    print(f"\n使用新创建的用户进行测试: {username}")
    print(f"密码: {password}")
    
    # 测试登录 - 注意：登录接口需要用户名，不是邮箱
    login_url = f"{API_BASE_URL}/api/auth/login"
    
    login_data = {
        "username": actual_username,
        "password": password
    }
    
    print(f"登录用户名: {actual_username}")
    print(f"登录密码: {password}")
    
    try:
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            auth_response = response.json()
            token = auth_response.get('access_token')
            user_info = auth_response.get('user_info')
            
            print(f"\n✅ 登录成功！")
            print(f"用户信息: {user_info}")
            print(f"Token: {token[:50]}...")
            
            # 测试使用token获取任务
            tasks_url = f"{API_BASE_URL}/api/tasks/"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            tasks_response = requests.get(tasks_url, headers=headers)
            
            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                print(f"\n✅ 任务获取成功！")
                print(f"任务数量: {len(tasks_data.get('tasks', []))}")
                print(f"任务列表: {json.dumps(tasks_data, indent=2, ensure_ascii=False)}")
                
                print("\n=== API认证功能验证完成 ===")
                print("✅ 后端API认证功能正常工作")
                print("✅ Token生成和验证机制正常")
                print("✅ 用户可以正常登录并访问受保护的接口")
                
            else:
                print(f"\n❌ 任务获取失败: {tasks_response.status_code}")
                print(f"错误信息: {tasks_response.text}")
                
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_login_and_get_tasks()