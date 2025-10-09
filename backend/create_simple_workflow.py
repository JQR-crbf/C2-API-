#!/usr/bin/env python3
"""
创建简化的工作流程会话
解决数据库字段限制问题
"""

from sqlalchemy.orm import sessionmaker
from database import engine
from models import Task, WorkflowSession, WorkflowStep, StepAction, TaskStatus, WorkflowStepStatus, WorkflowStepType, ActionType
from datetime import datetime
import json

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_simple_workflow_session(task_id: int):
    """为指定任务创建简化的工作流程会话"""
    db = SessionLocal()
    
    try:
        # 查找任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务 {task_id} 不存在")
            return False
        
        print(f"找到任务: {task.title} (状态: {task.status})")
        
        # 检查是否已有工作流程会话
        existing_session = db.query(WorkflowSession).filter(
            WorkflowSession.task_id == task_id
        ).first()
        
        if existing_session:
            print(f"任务 {task_id} 已有工作流程会话 (ID: {existing_session.id})")
            return True
        
        # 创建工作流程会话
        workflow_session = WorkflowSession(
            task_id=task_id,
            user_id=task.user_id,
            session_name=f"任务{task_id}工作流程",
            status="IN_PROGRESS",
            current_step=2,  # 当前在第2步（管理员审核）
            total_steps=3,   # 简化为3步
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(workflow_session)
        db.flush()  # 获取会话ID
        
        print(f"创建工作流程会话 {workflow_session.id}")
        
        # 创建简化的工作流程步骤（只创建3步）
        steps = [
            {
                "step_number": 1,
                "step_type": WorkflowStepType.CODE_COMMIT,
                "step_name": "代码提交",
                "status": WorkflowStepStatus.COMPLETED,  # 已完成
            },
            {
                "step_number": 2,
                "step_type": WorkflowStepType.ADMIN_REVIEW,
                "step_name": "管理员审核",
                "status": WorkflowStepStatus.PENDING,    # 当前步骤
            },
            {
                "step_number": 3,
                "step_type": WorkflowStepType.COMPLETION,
                "step_name": "完成",
                "status": WorkflowStepStatus.PENDING,
            }
        ]
        
        for step_config in steps:
            step = WorkflowStep(
                session_id=workflow_session.id,
                step_number=step_config["step_number"],
                step_type=step_config["step_type"],
                step_name=step_config["step_name"],
                status=step_config["status"]
            )
            
            db.add(step)
            db.flush()  # 获取step.id
            
            # 为每个步骤创建一个简单的操作
            action = StepAction(
                step_id=step.id,
                action_type=ActionType.USER_INPUT,  # 使用简短的枚举值
                action_name=step_config["step_name"],
                status=step_config["status"]
            )
            db.add(action)
        
        # 提交所有更改
        db.commit()
        
        print(f"✅ 成功为任务 {task_id} 创建工作流程会话")
        print(f"   - 会话ID: {workflow_session.id}")
        print(f"   - 当前步骤: {workflow_session.current_step}")
        print(f"   - 总步骤数: {workflow_session.total_steps}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建工作流程会话失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # 为任务14创建工作流程会话
    task_id = 14
    success = create_simple_workflow_session(task_id)
    
    if success:
        print(f"\n🎉 任务 {task_id} 的工作流程会话创建成功！")
        print("现在可以测试提交代码按钮了。")
    else:
        print(f"\n❌ 任务 {task_id} 的工作流程会话创建失败。")