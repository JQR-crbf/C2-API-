#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_homepage_stats():
    """测试首页统计数据的API调用"""
    
    # Admin用户的token
    admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo1LCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6IlVzZXJSb2xlLkFETUlOIiwiZXhwIjoxNzYxMjM1NzkzfQ.7JQcIsyPZR_kPctLeCzssLE5Gr936zVu2Lx47Z10NRA"
    
    # jinqianru用户的token
    jinqianru_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqaW5xaWFucnUiLCJleHAiOjE3NjEyMzU3MTJ9.1wYqh5uLMmdHl3r8ro5NgY4aLWFVVhJEbL-i_UIhBLs"
    
    base_url = "http://localhost:8000"
    
    print("=== 测试首页统计数据API调用 ===")
    
    # 1. 测试admin用户看到的任务数
    print("\n1. Admin用户 - 管理员API (/api/admin/tasks)")
    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{base_url}/api/admin/tasks", headers=admin_headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"管理员API返回任务总数: {data.get('total', 0)}")
            print(f"任务列表长度: {len(data.get('tasks', []))}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试admin用户调用普通用户API
    print("\n2. Admin用户 - 普通用户API (/api/tasks/)")
    try:
        response = requests.get(f"{base_url}/api/tasks/", headers=admin_headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"普通用户API返回任务总数: {data.get('total', 0)}")
            print(f"任务列表长度: {len(data.get('tasks', []))}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 3. 测试jinqianru用户看到的任务数
    print("\n3. jinqianru用户 - 普通用户API (/api/tasks/)")
    jinqianru_headers = {
        "Authorization": f"Bearer {jinqianru_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{base_url}/api/tasks/", headers=jinqianru_headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"jinqianru用户API返回任务总数: {data.get('total', 0)}")
            print(f"任务列表长度: {len(data.get('tasks', []))}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== 总结 ===")
    print("\n预期结果:")
    print("- Admin用户在首页应该看到所有任务（3个）")
    print("- jinqianru用户在首页应该看到自己的任务（3个）")
    print("- 任务页面(/tasks)应该根据用户角色显示相应的任务")
    print("\n如果首页显示的数字与API返回的数字不一致，说明前端逻辑需要进一步调试。")

if __name__ == "__main__":
    test_homepage_stats()