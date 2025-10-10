#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_admin_api():
    """测试admin用户API访问"""
    
    # Admin用户的token
    admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo1LCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6IlVzZXJSb2xlLkFETUlOIiwiZXhwIjoxNzYxMjM1NzkzfQ.7JQcIsyPZR_kPctLeCzssLE5Gr936zVu2Lx47Z10NRA"
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    print("=== 测试Admin用户API访问 ===")
    
    # 1. 测试获取当前用户信息
    print("\n1. 测试获取当前用户信息 (/auth/me)")
    try:
        response = requests.get(f"{base_url}/auth/me", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            user_info = response.json()
            print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试普通用户任务API
    print("\n2. 测试普通用户任务API (/api/tasks/)")
    try:
        response = requests.get(f"{base_url}/api/tasks/", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            tasks = response.json()
            print(f"普通用户任务数: {len(tasks.get('tasks', []))}")
            print(f"任务列表: {json.dumps(tasks, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 3. 测试管理员任务API
    print("\n3. 测试管理员任务API (/api/admin/tasks)")
    try:
        response = requests.get(f"{base_url}/api/admin/tasks", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            tasks = response.json()
            print(f"管理员任务数: {len(tasks.get('tasks', []))}")
            print(f"任务列表: {json.dumps(tasks, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_admin_api()