#!/usr/bin/env python3
"""
测试管理员审核API功能
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8080"
TASK_ID = 4

# 获取管理员token
def get_admin_token():
    login_data = {
        "username": "jinqianru",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

# 测试审核API
def test_review_api():
    token = get_admin_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试拒绝操作
    print("\n=== 测试拒绝操作 ===")
    reject_params = {
        "action": "reject",
        "comment": "代码有bug，需要重新生成"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/tasks/{TASK_ID}/review",
        headers=headers,
        params=reject_params
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        print("✅ 拒绝操作成功")
    else:
        print("❌ 拒绝操作失败")
        try:
            error_detail = response.json()
            print(f"错误详情: {error_detail}")
        except:
            pass

if __name__ == "__main__":
    test_review_api()