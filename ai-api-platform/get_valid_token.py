import requests
import json
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import get_db
from models import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# 后端API地址
API_BASE_URL = "http://localhost:8000"

def check_user_credentials():
    """检查jinqianru用户的登录凭据"""
    db = next(get_db())
    
    # 查找jinqianru用户
    user = db.query(User).filter(User.email == "123@qq.com").first()
    
    if user:
        print(f"找到用户: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"用户ID: {user.id}")
        print(f"角色: {user.role}")
        print(f"是否激活: {user.is_active}")
        print(f"密码哈希: {user.password_hash}")
        
        # 直接尝试常见密码进行API登录测试
        test_passwords = ["admin", "123456", "password", "jinqianru", "123@qq.com"]
        
        for password in test_passwords:
            print(f"尝试密码: {password}")
            if test_login_api(user.email, password):
                print(f"\n找到正确密码: {password}")
                return user.email, password
        
        print("\n未找到匹配的密码")
        return user.email, None

def test_login_api(username, password):
    """测试API登录"""
    try:
        login_url = f"{API_BASE_URL}/api/auth/login"
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(login_url, json=login_data)
        return response.status_code == 200
    except:
        return False
    else:
        print("未找到用户")
        return None, None

def get_token_for_jinqianru():
    """获取jinqianru用户的有效token"""
    # 首先检查用户凭据
    username, password = check_user_credentials()
    
    if not username or not password:
        print("无法获取有效的用户凭据")
        return
    
    login_url = f"{API_BASE_URL}/api/auth/login"
    
    # jinqianru用户的登录凭据
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            auth_response = response.json()
            token = auth_response.get('access_token')
            user_info = auth_response.get('user_info')
            
            print(f"登录成功！")
            print(f"用户信息: {user_info}")
            print(f"Token: {token}")
            
            # 测试使用token获取任务
            tasks_url = f"{API_BASE_URL}/api/tasks/"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            tasks_response = requests.get(tasks_url, headers=headers)
            
            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                print(f"\n任务获取成功！")
                print(f"任务数量: {len(tasks_data.get('tasks', []))}")
                print(f"任务列表: {json.dumps(tasks_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"\n任务获取失败: {tasks_response.status_code}")
                print(f"错误信息: {tasks_response.text}")
                
        else:
            print(f"登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    get_token_for_jinqianru()