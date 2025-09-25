#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断前后端字段不匹配问题的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import sessionmaker
from database import engine, get_db
from models import User, Task
import json
import requests

def check_backend_api_response():
    """检查后端API返回的数据格式"""
    print("=== 后端API响应格式检查 ===")
    
    try:
        # 首先获取一个有效的token
        from auth_utils import create_user_token
        
        db = next(get_db())
        jinqianru_user = db.query(User).filter(User.username == "jinqianru").first()
        
        if not jinqianru_user:
            print("   ✗ 未找到jinqianru用户")
            return
            
        # 生成token
        token = create_user_token(jinqianru_user.id, jinqianru_user.username, jinqianru_user.role.value)
        
        # 调用API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('http://localhost:8080/api/tasks/', headers=headers)
        
        if response.status_code == 200:
            tasks_data = response.json()
            print(f"   ✓ API调用成功，返回 {len(tasks_data)} 个任务")
            
            if tasks_data:
                print("\n   第一个任务的字段:")
                first_task = tasks_data[0]
                for key, value in first_task.items():
                    print(f"     - {key}: {type(value).__name__}")
                    
                print("\n   关键字段检查:")
                if 'title' in first_task:
                    print(f"     ✓ 包含 'title' 字段: {first_task['title']}")
                else:
                    print("     ✗ 缺少 'title' 字段")
                    
                if 'name' in first_task:
                    print(f"     ✓ 包含 'name' 字段: {first_task['name']}")
                else:
                    print("     ✗ 缺少 'name' 字段")
                    
                if 'id' in first_task:
                    print(f"     ✓ 包含 'id' 字段: {first_task['id']}")
                else:
                    print("     ✗ 缺少 'id' 字段")
                    
                if 'status' in first_task:
                    print(f"     ✓ 包含 'status' 字段: {first_task['status']}")
                else:
                    print("     ✗ 缺少 'status' 字段")
        else:
            print(f"   ✗ API调用失败: {response.status_code} - {response.text}")
            
        db.close()
        
    except Exception as e:
        print(f"   ✗ 检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def check_frontend_expectations():
    """检查前端期望的数据格式"""
    print("\n=== 前端期望数据格式检查 ===")
    
    # 读取前端API类型定义
    api_file = os.path.join(os.path.dirname(__file__), 'ai-api-platform', 'lib', 'api.ts')
    
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("\n1. Task接口定义:")
        
        # 查找Task接口定义
        import re
        task_interface_match = re.search(r'export interface Task \{([^}]+)\}', content, re.DOTALL)
        if task_interface_match:
            interface_content = task_interface_match.group(1)
            lines = interface_content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    print(f"     {line}")
        else:
            print("     ✗ 未找到Task接口定义")
            
        # 检查前端页面中使用的字段
        print("\n2. 前端页面使用的字段:")
        tasks_page = os.path.join(os.path.dirname(__file__), 'ai-api-platform', 'app', 'tasks', 'page.tsx')
        if os.path.exists(tasks_page):
            with open(tasks_page, 'r', encoding='utf-8') as f:
                page_content = f.read()
                
            # 查找task.字段的使用
            field_uses = re.findall(r'task\.(\w+)', page_content)
            unique_fields = list(set(field_uses))
            for field in sorted(unique_fields):
                print(f"     - task.{field}")
        else:
            print("     ✗ 未找到tasks页面文件")
    else:
        print("   ✗ 未找到api.ts文件")

def check_backend_schema():
    """检查后端数据库模式"""
    print("\n=== 后端数据库模式检查 ===")
    
    # 读取models.py
    models_file = os.path.join(os.path.dirname(__file__), 'backend', 'models.py')
    if os.path.exists(models_file):
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("\n1. Task模型字段:")
        
        # 查找Task类定义
        import re
        task_class_match = re.search(r'class Task\(Base\):(.*?)(?=class|$)', content, re.DOTALL)
        if task_class_match:
            class_content = task_class_match.group(1)
            # 查找Column定义
            column_matches = re.findall(r'(\w+)\s*=\s*Column\(([^)]+)\)', class_content)
            for field_name, column_def in column_matches:
                print(f"     - {field_name}: {column_def}")
        else:
            print("     ✗ 未找到Task类定义")
    else:
        print("   ✗ 未找到models.py文件")

def provide_solutions():
    """提供解决方案"""
    print("\n=== 问题分析和解决方案 ===")
    
    print("\n问题分析:")
    print("1. 后端数据库模型使用 'title' 字段存储任务名称")
    print("2. 前端TypeScript接口定义期望 'name' 字段")
    print("3. 前端页面代码使用 task.name 访问任务名称")
    print("4. 这导致前端无法正确显示任务数据")
    
    print("\n解决方案选项:")
    print("\n方案1: 修改前端接口定义和页面代码 (推荐)")
    print("   - 将前端Task接口中的 'name' 改为 'title'")
    print("   - 将前端页面中的 task.name 改为 task.title")
    print("   - 优点: 保持后端数据库结构不变")
    print("   - 缺点: 需要修改前端多个文件")
    
    print("\n方案2: 修改后端API响应格式")
    print("   - 在后端API中添加字段映射，将 'title' 映射为 'name'")
    print("   - 优点: 前端代码无需修改")
    print("   - 缺点: 增加后端复杂性，可能影响其他API")
    
    print("\n方案3: 数据库迁移")
    print("   - 将数据库中的 'title' 字段重命名为 'name'")
    print("   - 优点: 前后端统一")
    print("   - 缺点: 需要数据库迁移，风险较高")
    
    print("\n推荐执行方案1，具体步骤:")
    print("1. 修改 ai-api-platform/lib/api.ts 中的Task接口")
    print("2. 修改 ai-api-platform/app/tasks/page.tsx 中的字段引用")
    print("3. 检查其他可能使用task.name的文件")
    print("4. 测试前端任务列表显示")

def main():
    print("前后端字段不匹配问题诊断")
    print("=" * 50)
    
    check_backend_schema()
    check_frontend_expectations()
    check_backend_api_response()
    provide_solutions()

if __name__ == "__main__":
    main()