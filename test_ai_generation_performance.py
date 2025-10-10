#!/usr/bin/env python3
"""
AI代码生成性能测试脚本
用于诊断代码生成缓慢的问题
"""

import asyncio
import time
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/.env')

# 配置
BASE_URL = "http://localhost:8080/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
TASKS_URL = f"{BASE_URL}/tasks/"

def get_auth_token():
    """获取认证token"""
    try:
        login_data = {
            "username": "jinqianru",  # 使用正确的用户名
            "password": "123456"      # 使用正确的密码
        }
        
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ 成功获取认证token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {str(e)}")
        return None

def create_test_task(token):
    """创建测试任务"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        task_data = {
            "name": f"性能测试任务_{datetime.now().strftime('%H%M%S')}",
            "description": "简单的用户管理API，包含用户注册和登录功能",
            "language": "python",
            "framework": "fastapi",
            "database": "mysql",
            "priority": "medium",
            "features": ["authentication", "api_documentation"]
        }
        
        print(f"📝 创建测试任务...")
        start_time = time.time()
        
        response = requests.post(TASKS_URL, headers=headers, json=task_data)
        
        create_time = time.time() - start_time
        print(f"⏱️  任务创建耗时: {create_time:.2f}秒")
        
        if response.status_code == 200:
            task_info = response.json()
            task_id = task_info.get("id")
            print(f"✅ 任务创建成功，ID: {task_id}")
            return task_id
        else:
            print(f"❌ 任务创建失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 任务创建异常: {str(e)}")
        return None

def monitor_task_progress(token, task_id, timeout=300):
    """监控任务进度"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        last_status = None
        status_changes = []
        
        print(f"🔍 开始监控任务 {task_id} 的进度...")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{TASKS_URL}{task_id}", headers=headers)
                
                if response.status_code == 200:
                    task_info = response.json()
                    current_status = task_info.get("status")
                    current_time = time.time() - start_time
                    
                    if current_status != last_status:
                        status_changes.append({
                            "status": current_status,
                            "time": current_time,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] 状态变更: {current_status} (耗时: {current_time:.1f}秒)")
                        last_status = current_status
                    
                    # 检查是否完成
                    if current_status in ["CODE_SUBMITTED", "APPROVED", "COMPLETED", "FAILED"]:
                        print(f"🎯 任务完成，最终状态: {current_status}")
                        break
                        
                else:
                    print(f"❌ 获取任务状态失败: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 监控异常: {str(e)}")
            
            time.sleep(2)  # 每2秒检查一次
        
        total_time = time.time() - start_time
        
        print(f"\n📈 性能分析报告:")
        print(f"总耗时: {total_time:.1f}秒")
        print(f"状态变更历史:")
        
        for i, change in enumerate(status_changes):
            if i == 0:
                print(f"  1. {change['timestamp']} - {change['status']} (开始)")
            else:
                prev_time = status_changes[i-1]['time']
                duration = change['time'] - prev_time
                print(f"  {i+1}. {change['timestamp']} - {change['status']} (耗时: {duration:.1f}秒)")
        
        return status_changes
        
    except Exception as e:
        print(f"❌ 监控异常: {str(e)}")
        return []

def check_ai_service_config():
    """检查AI服务配置"""
    print(f"\n🔧 检查AI服务配置:")
    
    # 检查环境变量
    api_key = os.getenv('OPENROUTER_API_KEY')
    model = os.getenv('AI_MODEL', 'anthropic/claude-3-5-sonnet-20241022')
    
    print(f"API密钥: {'已配置' if api_key else '❌ 未配置'}")
    print(f"AI模型: {model}")
    
    if api_key:
        # 测试API连接
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            test_data = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            print(f"🔗 测试API连接...")
            start_time = time.time()
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=30
            )
            
            api_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ API连接正常 (响应时间: {api_time:.2f}秒)")
            else:
                print(f"❌ API连接失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ API测试异常: {str(e)}")

def main():
    """主函数"""
    print("🚀 AI代码生成性能诊断开始")
    print("=" * 50)
    
    # 检查AI服务配置
    check_ai_service_config()
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    
    # 创建测试任务
    task_id = create_test_task(token)
    if not task_id:
        print("❌ 无法创建测试任务，测试终止")
        return
    
    # 监控任务进度
    status_changes = monitor_task_progress(token, task_id)
    
    print("\n🎯 诊断完成")
    
    # 分析结果
    if status_changes:
        ai_generating_time = None
        for i, change in enumerate(status_changes):
            if change['status'] == 'AI_GENERATING' and i < len(status_changes) - 1:
                next_change = status_changes[i + 1]
                ai_generating_time = next_change['time'] - change['time']
                break
        
        if ai_generating_time:
            print(f"\n📊 AI代码生成耗时: {ai_generating_time:.1f}秒")
            if ai_generating_time > 60:
                print("⚠️  代码生成时间过长，可能的原因:")
                print("   1. OpenRouter API响应慢")
                print("   2. 网络连接问题")
                print("   3. AI模型处理复杂")
                print("   4. 服务器资源不足")
            else:
                print("✅ 代码生成时间正常")

if __name__ == "__main__":
    main()