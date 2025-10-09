#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from database import engine
from models import Task, WorkflowSession, WorkflowStep, StepAction, TaskStatus, WorkflowStepStatus, WorkflowStepType, ActionType
from datetime import datetime
import json

def create_workflow_session_for_task(task_id):
    """为指定任务创建工作流程会话"""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 获取任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务 {task_id} 不存在")
            return False
            
        print(f"为任务 {task_id} ({task.title}) 创建工作流程会话")
        
        # 检查是否已有工作流程会话
        existing_session = db.query(WorkflowSession).filter(
            WorkflowSession.task_id == task_id
        ).first()
        
        if existing_session:
            print(f"任务 {task_id} 已有工作流程会话 {existing_session.id}")
            return True
        
        # 创建工作流程会话
        workflow_session = WorkflowSession(
            task_id=task_id,
            user_id=task.user_id,
            session_name=f"Workflow for {task.title}",
            current_step=1,
            total_steps=5,  # 根据实际工作流程步骤数设置
            status="IN_PROGRESS",
            progress_percentage=20.0,  # 假设代码提交是第一步，完成20%
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(workflow_session)
        db.flush()  # 获取会话ID
        
        print(f"创建工作流程会话 {workflow_session.id}")
        
        # 创建工作流程步骤 - 使用正确的WorkflowStepType枚举值
        steps = [
            {
                "step_number": 1,
                "step_type": WorkflowStepType.CODE_COMMIT,
                "step_name": "代码提交",
                "status": WorkflowStepStatus.COMPLETED,  # 代码已提交
                "required_actions": ["SUBMIT_CODE"]
            },
            {
                "step_number": 2,
                "step_type": WorkflowStepType.ADMIN_REVIEW,
                "step_name": "管理员审核",
                "status": WorkflowStepStatus.PENDING,
                "required_actions": ["REVIEW_CODE", "APPROVE_CODE"]
            },
            {
                "step_number": 3,
                "step_type": WorkflowStepType.UNIT_TEST,
                "step_name": "单元测试",
                "status": WorkflowStepStatus.PENDING,
                "required_actions": ["RUN_TESTS", "VERIFY_RESULTS"]
            },
            {
                "step_number": 4,
                "step_type": WorkflowStepType.DEPLOYMENT,
                "step_name": "部署",
                "status": WorkflowStepStatus.PENDING,
                "required_actions": ["DEPLOY_CODE", "VERIFY_DEPLOYMENT"]
            },
            {
                "step_number": 5,
                "step_type": WorkflowStepType.COMPLETION,
                "step_name": "完成",
                "status": WorkflowStepStatus.PENDING,
                "required_actions": ["FINAL_VERIFICATION"]
            }
        ]
        
        for step_config in steps:
            step = WorkflowStep(
                session_id=workflow_session.id,
                step_number=step_config["step_number"],
                step_type=step_config["step_type"],
                step_name=step_config["step_name"],
                status=step_config["status"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(step)
            db.flush()  # 获取步骤ID
            
            # 为每个步骤创建操作
            for action_name in step_config["required_actions"]:
                action = StepAction(
                    step_id=step.id,
                    action_type=action_name,
                    action_name=action_name,
                    status=WorkflowStepStatus.COMPLETED if step_config["status"] == WorkflowStepStatus.COMPLETED else WorkflowStepStatus.PENDING,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(action)
        
        # 更新工作流程会话的当前步骤为下一步（代码审查）
        workflow_session.current_step = 2
        
        db.commit()
        print(f"成功为任务 {task_id} 创建工作流程会话和步骤")
        return True
        
    except Exception as e:
        print(f"创建工作流程会话时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """主函数"""
    # 获取最新任务ID
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        latest_task = db.query(Task).order_by(Task.id.desc()).first()
        if latest_task:
            print(f"最新任务: {latest_task.id} - {latest_task.title}")
            create_workflow_session_for_task(latest_task.id)
        else:
            print("没有找到任务")
    finally:
        db.close()

if __name__ == "__main__":
    main()