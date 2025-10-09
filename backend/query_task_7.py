#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_db
from models import Task
import json

def query_task_7():
    """查询任务7的详细信息"""
    db = next(get_db())
    try:
        task = db.query(Task).filter(Task.id == 7).first()
        
        if not task:
            print("任务7不存在")
            return
        
        print("=== 任务7详细信息 ===")
        print(f"ID: {task.id}")
        print(f"标题: {task.title}")
        print(f"描述: {task.description}")
        print(f"状态: {task.status}")
        print(f"用户ID: {task.user_id}")
        print(f"分支名称: {task.branch_name}")
        print(f"创建时间: {task.created_at}")
        print(f"更新时间: {task.updated_at}")
        
        print("\n=== 输入参数 ===")
        if task.input_params:
            print(json.dumps(task.input_params, indent=2, ensure_ascii=False))
        else:
            print("无输入参数")
        
        print("\n=== 输出参数 ===")
        if task.output_params:
            print(json.dumps(task.output_params, indent=2, ensure_ascii=False))
        else:
            print("无输出参数")
        
        print("\n=== 生成代码信息 ===")
        if task.generated_code:
            print(f"代码长度: {len(task.generated_code)} 字符")
            print("代码内容预览:")
            print(task.generated_code[:500] + "..." if len(task.generated_code) > 500 else task.generated_code)
        else:
            print("未生成代码")
        
        print("\n=== 测试用例信息 ===")
        if task.test_cases:
            print(f"测试用例长度: {len(task.test_cases)} 字符")
            print("测试用例内容预览:")
            print(task.test_cases[:300] + "..." if len(task.test_cases) > 300 else task.test_cases)
        else:
            print("无测试用例")
            
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    query_task_7()