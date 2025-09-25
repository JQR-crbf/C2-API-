from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

from database import get_db
from models import WorkflowSession, WorkflowStep, StepAction, User
from services.workflow_engine import workflow_engine
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Pydantic模型
class CreateWorkflowRequest(BaseModel):
    task_id: int
    requirements: Dict[str, Any]
    project_name: str
    project_description: Optional[str] = None
    project_path: Optional[str] = None
    git_repo_url: Optional[str] = None
    branch_name: Optional[str] = None

class ExecuteStepRequest(BaseModel):
    user_input: Optional[Dict[str, Any]] = None

class WorkflowStatusResponse(BaseModel):
    session_id: int
    status: str
    current_step: int
    total_steps: int
    progress_percentage: int
    created_at: str
    updated_at: str
    steps: List[Dict[str, Any]]

class WorkflowStepResponse(BaseModel):
    step_id: int
    step_number: int
    step_name: str
    step_type: str
    status: str
    description: Optional[str] = None
    estimated_duration: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    actions: List[Dict[str, Any]]

@router.post("/create", response_model=Dict[str, Any])
async def create_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的工作流程会话
    """
    try:
        success, session_id, error_msg = await workflow_engine.create_workflow_session(
            task_id=request.task_id,
            user_id=current_user.id,
            requirements=request.requirements,
            project_name=request.project_name,
            project_description=request.project_description,
            project_path=request.project_path,
            git_repo_url=request.git_repo_url,
            branch_name=request.branch_name
        )
        
        if success:
            return {
                "success": True,
                "session_id": session_id,
                "message": "工作流程创建成功"
            }
        else:
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        logger.error(f"创建工作流程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建工作流程失败: {str(e)}")

@router.get("/status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取工作流程状态
    """
    try:
        status_data = await workflow_engine.get_workflow_status(session_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此工作流程")
        
        return WorkflowStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流程状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/execute/{session_id}/{step_number}", response_model=Dict[str, Any])
async def execute_workflow_step(
    session_id: int,
    step_number: int,
    request: ExecuteStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    执行工作流程步骤
    """
    try:
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此工作流程")
        
        success, error_msg = await workflow_engine.execute_step(
            session_id=session_id,
            step_number=step_number,
            user_input=request.user_input
        )
        
        if success:
            return {
                "success": True,
                "message": f"步骤 {step_number} 执行成功"
            }
        else:
            return {
                "success": False,
                "error": error_msg
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流程步骤失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行步骤失败: {str(e)}")

@router.get("/step/{session_id}/{step_number}", response_model=WorkflowStepResponse)
async def get_workflow_step(
    session_id: int,
    step_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定工作流程步骤的详细信息
    """
    try:
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此工作流程")
        
        # 获取步骤信息
        step = db.query(WorkflowStep).filter(
            WorkflowStep.session_id == session_id,
            WorkflowStep.step_number == step_number
        ).first()
        
        if not step:
            raise HTTPException(status_code=404, detail=f"步骤 {step_number} 不存在")
        
        # 获取步骤的操作
        actions = db.query(StepAction).filter(
            StepAction.step_id == step.id
        ).all()
        
        actions_data = []
        for action in actions:
            actions_data.append({
                "action_id": action.id,
                "action_name": action.action_name,
                "action_type": action.action_type.value,
                "status": action.status.value,
                "description": action.description,
                "command": action.command,
                "output": action.output,
                "error_message": action.error_message,
                "started_at": action.started_at.isoformat() if action.started_at else None,
                "completed_at": action.completed_at.isoformat() if action.completed_at else None,
                "duration_seconds": action.duration_seconds
            })
        
        return WorkflowStepResponse(
            step_id=step.id,
            step_number=step.step_number,
            step_name=step.step_name,
            step_type=step.step_type.value,
            status=step.status.value,
            description=step.description,
            estimated_duration=step.estimated_duration,
            started_at=step.started_at.isoformat() if step.started_at else None,
            completed_at=step.completed_at.isoformat() if step.completed_at else None,
            duration_seconds=step.duration_seconds,
            error_message=step.error_message,
            actions=actions_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流程步骤失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取步骤失败: {str(e)}")

@router.post("/pause/{session_id}", response_model=Dict[str, Any])
async def pause_workflow(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    暂停工作流程
    """
    try:
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此工作流程")
        
        success, error_msg = await workflow_engine.pause_workflow(session_id)
        
        if success:
            return {
                "success": True,
                "message": "工作流程已暂停"
            }
        else:
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停工作流程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"暂停工作流程失败: {str(e)}")

@router.post("/resume/{session_id}", response_model=Dict[str, Any])
async def resume_workflow(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    恢复工作流程
    """
    try:
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此工作流程")
        
        success, error_msg = await workflow_engine.resume_workflow(session_id)
        
        if success:
            return {
                "success": True,
                "message": "工作流程已恢复"
            }
        else:
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复工作流程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复工作流程失败: {str(e)}")

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_user_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的所有工作流程会话
    """
    try:
        sessions = db.query(WorkflowSession).filter(
            WorkflowSession.user_id == current_user.id
        ).order_by(WorkflowSession.created_at.desc()).all()
        
        result = []
        for session in sessions:
            result.append({
                "session_id": session.id,
                "task_id": session.task_id,
                "project_name": session.project_name,
                "status": session.status.value,
                "current_step": session.current_step,
                "total_steps": session.total_steps,
                "progress_percentage": session.progress_percentage,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"获取用户工作流程列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

@router.delete("/delete/{session_id}", response_model=Dict[str, Any])
async def delete_workflow(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除工作流程会话
    """
    try:
        # 检查用户权限
        session = db.query(WorkflowSession).filter(
            WorkflowSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="工作流程会话不存在")
        
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此工作流程")
        
        # 删除相关的步骤和操作（由于外键约束，会级联删除）
        db.delete(session)
        db.commit()
        
        return {
            "success": True,
            "message": "工作流程已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除工作流程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除工作流程失败: {str(e)}")