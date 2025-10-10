#!/usr/bin/env python3
"""
任务创建API调试测试脚本
用于排查422错误的具体原因
"""

import requests
import json
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def get_auth_token():
    """获取认证token"""
    try:
        # 尝试从文件读取token
        token_file = os.path.join(os.path.dirname(__file__), 'backend', 'valid_token.txt')
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                return f.read().strip()
        
        # 如果没有token文件，尝试登录获取
        login_url = "http://localhost:8080/api/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(login_url, data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"获取token失败: {e}")
        return None

def test_task_creation_api():
    """测试任务创建API"""
    print("=== 任务创建API调试测试 ===\n")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return False
    
    print(f"✅ 成功获取认证token: {token[:20]}...")
    
    # 准备测试数据 - 模拟前端发送的数据
    test_cases = [
        {
            "name": "测试用例1 - 基本数据",
            "data": {
                "name": "用户管理API",
                "description": "创建一个用户管理API，包含用户注册、登录、个人资料管理功能",
                "language": "python",
                "framework": "fastapi",
                "database": "mysql",
                "priority": "medium",
                "features": ["authentication", "api_documentation"]
            }
        },
        {
            "name": "测试用例2 - 最小数据",
            "data": {
                "name": "简单API",
                "description": "简单的API测试"
            }
        },
        {
            "name": "测试用例3 - 完整数据",
            "data": {
                "name": "完整功能API",
                "description": "包含所有功能的完整API",
                "language": "python",
                "framework": "fastapi", 
                "database": "postgresql",
                "priority": "high",
                "features": ["authentication", "file_upload", "api_documentation", "test_cases"]
            }
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    api_url = "http://localhost:8080/api/tasks/"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- {test_case['name']} ---")
        print(f"请求数据: {json.dumps(test_case['data'], indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(api_url, json=test_case['data'], headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200 or response.status_code == 201:
                print("✅ 任务创建成功!")
                response_data = response.json()
                print(f"任务ID: {response_data.get('id')}")
                print(f"任务标题: {response_data.get('title')}")
                print(f"任务状态: {response_data.get('status')}")
            else:
                print(f"❌ 任务创建失败!")
                print(f"错误响应: {response.text}")
                
                # 尝试解析错误详情
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        print(f"错误详情: {error_data['detail']}")
                        
                        # 如果是验证错误，显示具体字段错误
                        if isinstance(error_data['detail'], list):
                            print("字段验证错误:")
                            for error in error_data['detail']:
                                print(f"  - 字段: {error.get('loc', 'unknown')}")
                                print(f"    错误: {error.get('msg', 'unknown')}")
                                print(f"    输入值: {error.get('input', 'unknown')}")
                except:
                    pass
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except Exception as e:
            print(f"❌ 未知错误: {e}")
    
    return True

def test_database_connection():
    """测试数据库连接"""
    print("\n=== 数据库连接测试 ===")
    
    try:
        from database import get_db, engine
        from models import Task, User
        from sqlalchemy.orm import Session
        
        # 测试数据库连接
        db = next(get_db())
        
        # 查询用户表
        user_count = db.query(User).count()
        print(f"✅ 用户表连接正常，共有 {user_count} 个用户")
        
        # 查询任务表
        task_count = db.query(Task).count()
        print(f"✅ 任务表连接正常，共有 {task_count} 个任务")
        
        # 检查表结构
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        # 检查tasks表的列
        task_columns = inspector.get_columns('tasks')
        print(f"✅ 任务表字段: {[col['name'] for col in task_columns]}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    print("开始任务创建API调试测试...\n")
    
    # 测试数据库连接
    if not test_database_connection():
        print("数据库连接失败，请检查数据库配置")
        return
    
    # 测试API
    test_task_creation_api()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()