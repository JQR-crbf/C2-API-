#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的部署步骤生成功能
验证是否按照用户提供的37步指南生成步骤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.guided_deployment_service import guided_deployment_service
from models import Task
from sqlalchemy.orm import sessionmaker
from database import engine

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_deployment_steps_generation():
    """
    测试部署步骤生成功能
    """
    try:
        # 获取Task 7的数据
        task = db.query(Task).filter(Task.id == 7).first()
        
        if not task:
            print("错误：未找到Task 7")
            return
        
        print(f"任务信息：")
        print(f"ID: {task.id}")
        print(f"标题: {task.title}")
        print(f"描述: {task.description}")
        print(f"状态: {task.status}")
        print("\n" + "="*50 + "\n")
        
        # 生成部署步骤
        print("正在生成部署步骤...")
        steps = guided_deployment_service.generate_deployment_steps(
            task=task,
            deployment_path="/opt/api/ai_interface_project",
            git_repo_url="https://github.com/example/repo.git"
        )
        
        print(f"\n生成了 {len(steps)} 个部署步骤：\n")
        
        # 验证关键步骤
        expected_steps = [
            "进入项目目录",
            "切换到主分支", 
            "获取最新的代码",
            "创建新的分支",
            "打开文件写入",
            "写入代码",
            "保存代码",
            "退出文件编辑",
            "创建虚拟环境",
            "激活虚拟环境",
            "启动服务",
            "是否报错",
            "代码打包",
            "代码备注",
            "代码推送",
            "部署完成"
        ]
        
        # 显示所有步骤
        for i, step in enumerate(steps, 1):
            print(f"步骤 {step['step_number']}: {step['step_name']}")
            print(f"  描述: {step['step_description']}")
            print(f"  命令: {step['command']}")
            if 'user_action' in step:
                print(f"  用户操作: {step['user_action']}")
            if 'user_instruction' in step:
                print(f"  用户指令: {step['user_instruction']}")
            print(f"  预期输出: {step['expected_output']}")
            print()
        
        # 验证是否包含关键步骤
        step_names = [step['step_name'] for step in steps]
        missing_steps = []
        
        for expected in expected_steps:
            found = any(expected in name for name in step_names)
            if not found:
                missing_steps.append(expected)
        
        if missing_steps:
            print(f"\n⚠️  缺少以下关键步骤: {missing_steps}")
        else:
            print("\n✅ 所有关键步骤都已包含")
        
        # 验证特定的用户要求
        print("\n验证用户特定要求：")
        
        # 检查是否使用git switch而不是git checkout
        git_switch_found = any('git switch main' in step['command'] for step in steps)
        print(f"✅ 使用git switch main: {git_switch_found}")
        
        # 检查是否包含nano编辑器操作
        nano_steps = [step for step in steps if 'nano' in step['command']]
        print(f"✅ 包含nano编辑器步骤: {len(nano_steps)} 个")
        
        # 检查是否包含Ctrl+O和Ctrl+X操作
        ctrl_o_steps = [step for step in steps if 'Ctrl + O' in step['command']]
        ctrl_x_steps = [step for step in steps if 'Ctrl + X' in step['command']]
        print(f"✅ 包含Ctrl+O保存操作: {len(ctrl_o_steps)} 个")
        print(f"✅ 包含Ctrl+X退出操作: {len(ctrl_x_steps)} 个")
        
        # 检查是否包含虚拟环境操作
        venv_create = any('python3 -m venv venv' in step['command'] for step in steps)
        venv_activate = any('source venv/bin/activate' in step['command'] for step in steps)
        print(f"✅ 包含创建虚拟环境: {venv_create}")
        print(f"✅ 包含激活虚拟环境: {venv_activate}")
        
        # 检查是否使用uvicorn启动服务
        uvicorn_start = any('uvicorn app.main:app' in step['command'] for step in steps)
        print(f"✅ 使用uvicorn启动服务: {uvicorn_start}")
        
        # 检查是否包含错误检查步骤
        error_check = any('是否报错' in step['step_name'] for step in steps)
        print(f"✅ 包含错误检查步骤: {error_check}")
        
        print(f"\n🎉 测试完成！生成的步骤数量: {len(steps)}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_deployment_steps_generation()