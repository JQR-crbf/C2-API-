#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试37步部署指南的实现
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 禁用SQLAlchemy日志
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

from services.guided_deployment_service import GuidedDeploymentService
from models.task import Task

def test_37_steps():
    """
    测试37步部署指南的生成
    """
    print("开始测试37步部署指南...")
    
    # 创建服务实例
    service = GuidedDeploymentService()
    
    # 创建一个模拟任务
    task = Task(
        id=7,
        name="测试任务",
        description="测试37步部署指南",
        generated_code="模拟生成的代码"
    )
    
    # 生成部署步骤
    steps = service.generate_deployment_steps(task)
    
    print(f"\n生成的步骤总数: {len(steps)}")
    
    # 验证是否为37步
    if len(steps) != 37:
        print(f"❌ 错误：期望37步，实际生成{len(steps)}步")
        return False
    
    print("✅ 步骤数量正确：37步")
    
    # 验证关键步骤
    expected_steps = {
        1: "进入项目目录",
        2: "切换到主分支", 
        3: "获取最新的代码",
        4: "创建新的分支",
        5: "打开文件写入",
        6: "写入代码",
        7: "保存代码",
        8: "退出文件编辑",
        21: "打开文件写入（写入到最后）",
        24: "退出文件编辑（键盘快捷键 ctrl+）",
        30: "创建虚拟环境",
        31: "激活虚拟环境",
        32: "启动服务",
        33: "是否报错",
        34: "代码打包",
        35: "代码备注",
        36: "代码推送",
        37: "部署完成"
    }
    
    print("\n验证关键步骤:")
    all_correct = True
    
    for step_num, expected_name in expected_steps.items():
        actual_step = steps[step_num - 1]  # 数组索引从0开始
        if actual_step['step_name'] != expected_name:
            print(f"❌ 步骤{step_num}错误：期望'{expected_name}'，实际'{actual_step['step_name']}'")
            all_correct = False
        else:
            print(f"✅ 步骤{step_num}: {expected_name}")
    
    # 验证关键命令
    key_commands = {
        1: f"cd /opt/api/ai_interface_project",
        2: "git switch main",
        3: "git pull origin main",
        4: "git switch -c feature/your-new-api",
        5: "nano app/models/your_model.py",
        30: "python3 -m venv venv",
        31: "source venv/bin/activate",
        32: "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
        34: "git add .",
        35: 'git commit -m "本次修改的内容，可用中文描述"',
        36: "git push -u origin feature/your-new-api"
    }
    
    print("\n验证关键命令:")
    for step_num, expected_command in key_commands.items():
        actual_step = steps[step_num - 1]
        if actual_step['command'] != expected_command:
            print(f"❌ 步骤{step_num}命令错误：期望'{expected_command}'，实际'{actual_step['command']}'")
            all_correct = False
        else:
            print(f"✅ 步骤{step_num}命令正确")
    
    # 验证没有expected_output字段（用户要求不要预期结果）
    print("\n验证是否移除了预期结果:")
    has_expected_output = False
    for step in steps:
        if 'expected_output' in step:
            print(f"❌ 步骤{step['step_number']}仍包含expected_output字段")
            has_expected_output = True
            all_correct = False
    
    if not has_expected_output:
        print("✅ 所有步骤都已移除expected_output字段")
    
    # 打印前10个步骤的详细信息
    print("\n前10个步骤详情:")
    for i in range(min(10, len(steps))):
        step = steps[i]
        print(f"步骤{step['step_number']}: {step['step_name']} - {step['command']}")
    
    if all_correct:
        print("\n🎉 所有验证通过！37步部署指南实现正确。")
        return True
    else:
        print("\n❌ 验证失败，存在错误。")
        return False

if __name__ == "__main__":
    success = test_37_steps()
    sys.exit(0 if success else 1)