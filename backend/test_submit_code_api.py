#!/usr/bin/env python3
"""
测试提交代码按钮的API调用
模拟前端调用后端API的过程
"""

import requests
import json
from datetime import datetime

# API配置
API_BASE_URL = "http://localhost:8080"
TASK_ID = 14

# 从文件读取有效token
def get_valid_token():
    """从文件读取有效的认证令牌"""
    try:
        with open("valid_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("❌ 未找到valid_token.txt文件，请先运行get_token_with_direct_auth.py")
        return None

def test_submit_code_api():
    """测试提交代码API调用"""
    
    print(f"🧪 开始测试任务 {TASK_ID} 的提交代码API...")
    
    # 获取有效token
    token = get_valid_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. 首先获取任务的工作流程信息
    print("\n1. 获取任务工作流程信息...")
    try:
        workflow_url = f"{API_BASE_URL}/api/tasks/{TASK_ID}/workflow"
        response = requests.get(workflow_url, headers=headers)
        
        print(f"   请求URL: {workflow_url}")
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            workflow_data = response.json()
            print(f"   ✅ 工作流程信息获取成功")
            print(f"   当前步骤: {workflow_data.get('current_step', 'N/A')}")
            print(f"   总步骤数: {workflow_data.get('total_steps', 'N/A')}")
            print(f"   进度: {workflow_data.get('progress_percentage', 'N/A')}%")
        else:
            print(f"   ❌ 获取工作流程信息失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 2. 测试提交代码操作
    print("\n2. 测试提交代码操作...")
    try:
        submit_url = f"{API_BASE_URL}/api/tasks/{TASK_ID}/actions/submit_code/complete"
        
        payload = {
            "message": "用户手动完成了代码提交操作",
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(submit_url, json=payload, headers=headers)
        
        print(f"   请求URL: {submit_url}")
        print(f"   请求载荷: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 提交代码操作成功")
            print(f"   响应消息: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ 提交代码操作失败")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
    
    # 3. 再次获取工作流程信息，检查状态变化
    print("\n3. 检查操作后的工作流程状态...")
    try:
        response = requests.get(workflow_url, headers=headers)
        
        if response.status_code == 200:
            workflow_data = response.json()
            print(f"   ✅ 工作流程信息获取成功")
            print(f"   当前步骤: {workflow_data.get('current_step', 'N/A')}")
            print(f"   总步骤数: {workflow_data.get('total_steps', 'N/A')}")
            print(f"   进度: {workflow_data.get('progress_percentage', 'N/A')}%")
            
            # 检查步骤详情
            if 'all_steps' in workflow_data:
                print(f"   步骤详情:")
                for step in workflow_data['all_steps']:
                    status_icon = "✅" if step.get('completed') else "⏳"
                    current_icon = "👉" if step.get('current') else "  "
                    print(f"   {current_icon} {status_icon} {step.get('name', 'N/A')} - {step.get('status', 'N/A')}")
        else:
            print(f"   ❌ 获取工作流程信息失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_submit_code_api()
    print(f"\n🏁 测试完成！")