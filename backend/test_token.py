#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_login_and_get_token():
    """测试登录并获取token"""
    base_url = "http://localhost:8000"
    
    # 测试用户登录
    login_data = {
        "username": "jinqianru",
        "password": "123456"
    }
    
    try:
        # 登录获取token
        print("正在尝试登录...")
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user_info = data.get('user_info')
            print(f"登录成功！")
            print(f"Token: {token[:50]}..." if token else "No token")
            print(f"用户信息: {user_info}")
            
            # 测试获取任务3
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                task_response = requests.get(f"{base_url}/api/tasks/3", headers=headers)
                print(f"\n获取任务3的响应状态码: {task_response.status_code}")
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    print(f"任务数据: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"获取任务失败: {task_response.text}")
            
            return token
        else:
            print(f"登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    test_login_and_get_token()