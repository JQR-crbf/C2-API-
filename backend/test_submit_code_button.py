#!/usr/bin/env python3
"""
测试代码提交按钮的完整功能
"""

import requests
import json
from datetime import datetime

# API配置
API_BASE_URL = "http://localhost:8080"
TASK_ID = 14

def get_valid_token():
    """从文件读取有效的认证令牌"""
    try:
        with open("valid_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("❌ 未找到valid_token.txt文件")
        return None

def test_submit_code_button():
    """测试代码提交按钮功能"""
    
    print(f"🧪 测试任务 {TASK_ID} 的代码提交按钮功能...")
    
    # 获取有效token
    token = get_valid_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. 获取当前工作流程状态
        print(f"\n1️⃣ 获取当前工作流程状态...")
        workflow_url = f"{API_BASE_URL}/api/tasks/{TASK_ID}/workflow"
        response = requests.get(workflow_url, headers=headers)
        
        if response.status_code == 200:
            workflow_data = response.json()
            print(f"✅ 当前状态: {workflow_data.get('current_status')}")
            
            workflow = workflow_data.get('workflow', {})
            current_step_index = workflow.get('current_step_index', 0)
            all_steps = workflow.get('all_steps', [])
            
            if all_steps and current_step_index < len(all_steps):
                current_step = all_steps[current_step_index]
                print(f"✅ 当前步骤: {current_step.get('name')} ({current_step.get('status')})")
                print(f"✅ 步骤完成状态: {current_step.get('completed')}")
                print(f"✅ 需要的操作: {current_step.get('required_actions', [])}")
                
                # 2. 如果当前步骤需要submit_code操作，则执行
                if 'submit_code' in current_step.get('required_actions', []):
                    print(f"\n2️⃣ 执行代码提交操作...")
                    
                    # 标记submit_code操作为完成
                    action_url = f"{API_BASE_URL}/api/tasks/{TASK_ID}/actions/submit_code/complete"
                    action_data = {
                        "message": "用户点击了代码提交按钮"
                    }
                    
                    action_response = requests.post(action_url, headers=headers, json=action_data)
                    
                    if action_response.status_code == 200:
                        result = action_response.json()
                        print(f"✅ 代码提交操作成功: {result.get('message')}")
                        
                        # 3. 重新获取工作流程状态，检查是否可以推进
                        print(f"\n3️⃣ 检查是否可以推进到下一步...")
                        response = requests.get(workflow_url, headers=headers)
                        
                        if response.status_code == 200:
                            updated_workflow = response.json()
                            workflow = updated_workflow.get('workflow', {})
                            all_steps = workflow.get('all_steps', [])
                            
                            if all_steps and current_step_index < len(all_steps):
                                updated_step = all_steps[current_step_index]
                                print(f"✅ 更新后步骤完成状态: {updated_step.get('completed')}")
                                print(f"✅ 是否可以推进: {updated_step.get('can_advance', False)}")
                                
                                # 4. 如果可以推进，则推进到下一步
                                if updated_step.get('can_advance', False):
                                    print(f"\n4️⃣ 推进到下一步...")
                                    
                                    advance_url = f"{API_BASE_URL}/api/tasks/{TASK_ID}/advance"
                                    advance_response = requests.post(advance_url, headers=headers, json={})
                                    
                                    if advance_response.status_code == 200:
                                        advance_result = advance_response.json()
                                        print(f"✅ 步骤推进成功: {advance_result.get('message')}")
                                        print(f"✅ 新状态: {advance_result.get('new_status')}")
                                        
                                        # 5. 最终检查工作流程状态
                                        print(f"\n5️⃣ 最终工作流程状态...")
                                        final_response = requests.get(workflow_url, headers=headers)
                                        
                                        if final_response.status_code == 200:
                                            final_workflow = final_response.json()
                                            print(f"✅ 最终状态: {final_workflow.get('current_status')}")
                                            
                                            final_workflow_data = final_workflow.get('workflow', {})
                                            final_current_step_index = final_workflow_data.get('current_step_index', 0)
                                            final_all_steps = final_workflow_data.get('all_steps', [])
                                            
                                            if final_all_steps and final_current_step_index < len(final_all_steps):
                                                final_current_step = final_all_steps[final_current_step_index]
                                                print(f"✅ 最终当前步骤: {final_current_step.get('name')} ({final_current_step.get('status')})")
                                        
                                    else:
                                        print(f"❌ 步骤推进失败: {advance_response.text}")
                                else:
                                    print(f"⚠️ 当前步骤尚未完成，无法推进")
                        
                    else:
                        print(f"❌ 代码提交操作失败: {action_response.text}")
                else:
                    print(f"⚠️ 当前步骤不需要submit_code操作")
            else:
                print(f"❌ 无法获取当前步骤信息")
        else:
            print(f"❌ 获取工作流程状态失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    test_submit_code_button()
    print(f"\n🏁 测试完成！")