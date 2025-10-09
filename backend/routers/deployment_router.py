from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import logging

from database import get_db
from models import User, Task
from schemas import MessageResponse
from routers.auth import get_current_user
from services.ssh_manager import ssh_manager
from services.guided_deployment_service import GuidedDeploymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["部署管理"])
guided_router = APIRouter(prefix="/guided-deployment", tags=["引导部署"])

# 请求模型
class ServerAuthConfig(BaseModel):
    password: Optional[str] = None
    key_path: Optional[str] = None
    key_content: Optional[str] = None

class ServerConnectionConfig(BaseModel):
    password: Optional[str] = Field(None, description="SSH密码")
    key_path: Optional[str] = Field(None, description="私钥文件路径")
    key_content: Optional[str] = Field(None, description="私钥内容")

class DeploymentSessionCreate(BaseModel):
    server_host: str = Field(..., description="服务器地址")
    server_port: int = Field(22, description="SSH端口")
    server_username: str = Field(..., description="用户名")
    deployment_path: str = Field(..., description="部署路径")
    git_repo_url: Optional[str] = Field(None, description="Git仓库地址")

class StepExecuteRequest(BaseModel):
    step_id: int = Field(..., description="步骤ID")
    connection_id: str = Field(..., description="连接ID")

# 响应模型
class DeploymentStepResponse(BaseModel):
    id: int
    step_number: int
    step_name: str
    step_description: str
    command: Optional[str]
    expected_output: Optional[str]
    actual_output: Optional[str]
    status: str
    error_message: Optional[str]
    file_path: Optional[str]
    file_content: Optional[str]
    completed_at: Optional[str]
    created_at: str

class DeploymentSessionResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    server_host: str
    server_port: int
    server_username: str
    connection_status: str
    current_step: int
    deployment_path: Optional[str]
    git_repo_url: Optional[str]
    created_at: str
    updated_at: str
    steps: List[DeploymentStepResponse]

class ConnectResponse(BaseModel):
    success: bool
    message: str
    connection_id: Optional[str] = None

class ExecuteResponse(BaseModel):
    success: bool
    message: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class GenerateStepsRequest(BaseModel):
    project_name: str = Field(..., description="项目名称")
    project_description: str = Field(..., description="项目描述")
    deployment_path: str = Field(..., description="部署路径")
    git_repo_url: Optional[str] = Field(None, description="Git仓库地址")
    code_files: List[Dict] = Field(..., description="代码文件列表")

class DeploymentStep(BaseModel):
    id: int
    step_number: int
    step_name: str
    step_description: str
    command: Optional[str]
    expected_output: Optional[str]
    is_manual: bool = False
    file_path: Optional[str] = None
    file_content: Optional[str] = None

class GenerateStepsResponse(BaseModel):
    success: bool
    message: str
    steps: List[DeploymentStep]

# 初始化服务
deployment_service = GuidedDeploymentService()

@router.post("/{task_id}/deployment/session")
async def create_deployment_session(
    task_id: int,
    session_data: DeploymentSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建部署会话
    """
    try:
        # 验证任务是否存在且属于当前用户
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 创建部署会话和步骤
        session = await deployment_service.create_deployment_session(
            task_id=task_id,
            user_id=current_user.id,
            server_config={
                "host": session_data.server_host,
                "port": session_data.server_port,
                "username": session_data.server_username,
                "deployment_path": session_data.deployment_path,
                "git_repo_url": session_data.git_repo_url
            },
            generated_code=task.generated_code or ""
        )
        
        return {
            "success": True,
            "message": "部署会话创建成功",
            "data": session
        }
        
    except Exception as e:
        logger.error(f"创建部署会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建部署会话失败: {str(e)}"
        )

@router.get("/{task_id}/deployment/session")
async def get_deployment_session(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取部署会话信息
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 获取部署会话
        session = await deployment_service.get_deployment_session(task_id)
        
        if not session:
            return {
                "success": False,
                "message": "部署会话不存在",
                "data": None
            }
        
        return {
            "success": True,
            "message": "获取部署会话成功",
            "data": session
        }
        
    except Exception as e:
        logger.error(f"获取部署会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取部署会话失败: {str(e)}"
        )

@router.post("/{task_id}/deployment/connect")
async def connect_to_server(
    task_id: int,
    connection_config: ServerConnectionConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    连接到服务器
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 验证认证信息
        if not connection_config.password and not connection_config.key_content and not connection_config.key_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供密码或SSH密钥"
            )
        
        # 准备连接参数
        ssh_config = {
            "host": connection_config.host,
            "port": connection_config.port,
            "username": connection_config.username
        }
        
        # 添加认证信息
        if connection_config.password:
            ssh_config["password"] = connection_config.password
        elif connection_config.key_content:
            ssh_config["key_content"] = connection_config.key_content
        elif connection_config.key_path:
            ssh_config["key_path"] = connection_config.key_path
        
        # 创建SSH连接
        success, connection_id, error_message = await ssh_manager.create_connection(
            **ssh_config
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message or "SSH连接失败"
            )
        
        # 更新会话状态
        await deployment_service.update_connection_status(
            task_id, "connected", connection_id
        )
        
        return {
            "success": True,
            "message": "服务器连接成功",
            "connection_id": connection_id
        }
        
    except Exception as e:
        logger.error(f"连接服务器失败: {str(e)}")
        # 更新会话状态为错误
        try:
            await deployment_service.update_connection_status(
                task_id, "error", None
            )
        except:
            pass
        
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "connection_id": None
        }

@router.post("/{task_id}/deployment/step/execute")
async def execute_deployment_step(
    task_id: int,
    execute_request: StepExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行部署步骤
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 执行部署步骤
        result = await deployment_service.execute_step(
            task_id=task_id,
            step_id=execute_request.step_id,
            connection_id=execute_request.connection_id
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr")
        }
        
    except Exception as e:
        logger.error(f"执行部署步骤失败: {str(e)}")
        return {
            "success": False,
            "message": f"执行失败: {str(e)}",
            "stdout": None,
            "stderr": str(e)
        }

@router.delete("/{task_id}/deployment/disconnect")
async def disconnect_from_server(
    task_id: int,
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    断开服务器连接
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 关闭SSH连接
        await ssh_manager.close_connection(connection_id)
        
        # 更新会话状态
        await deployment_service.update_connection_status(
            task_id, "disconnected", None
        )
        
        return {
            "success": True,
            "message": "连接已断开"
        }
        
    except Exception as e:
        logger.error(f"断开连接失败: {str(e)}")
        return {
            "success": False,
            "message": f"断开连接失败: {str(e)}"
        }

@router.post("/{task_id}/deployment/steps/{step_number}/complete")
async def mark_step_completed(
    task_id: int,
    step_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记部署步骤为已完成
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 标记步骤完成
        success, message = await deployment_service.mark_step_completed(
            db=db,
            task_id=task_id,
            step_number=step_number,
            user_id=current_user.id
        )
        
        if success:
            return {
                "success": True,
                "message": message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
    except Exception as e:
        logger.error(f"标记步骤完成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记步骤完成失败: {str(e)}"
        )

@router.get("/{task_id}/deployment/steps/status")
async def get_steps_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取部署步骤完成状态
    """
    try:
        # 验证任务权限
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        # 获取步骤状态
        success, steps_status, message = await deployment_service.get_steps_status(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        
        if success:
            return {
                "success": True,
                "message": "获取步骤状态成功",
                "steps": steps_status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
    except Exception as e:
        logger.error(f"获取步骤状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取步骤状态失败: {str(e)}"
        )

# 引导部署API端点
@guided_router.post("/generate-steps", response_model=GenerateStepsResponse)
async def generate_deployment_steps(
    request: GenerateStepsRequest,
    current_user: User = Depends(get_current_user)
):
    """生成部署步骤"""
    try:
        logger.info(f"用户 {current_user.id} 请求生成部署步骤")
        
        # 创建一个模拟的Task对象用于生成步骤
        class MockTask:
            def __init__(self, title, generated_code):
                self.id = 1
                self.title = title
                self.generated_code = generated_code
        
        # 从code_files中提取生成的代码
        generated_code = ""
        if request.code_files:
            for file_info in request.code_files:
                if 'content' in file_info:
                    generated_code += f"# 文件：{file_info.get('path', 'unknown.py')}\n"
                    generated_code += f"```python\n{file_info['content']}\n```\n\n"
        
        mock_task = MockTask(request.project_name, generated_code)
        
        # 调用服务生成步骤
        steps = deployment_service.generate_deployment_steps(
            task=mock_task,
            deployment_path=request.deployment_path,
            git_repo_url=request.git_repo_url or ""
        )
        
        # 转换为响应格式
        step_responses = []
        for i, step in enumerate(steps):
            step_responses.append(DeploymentStep(
                id=i + 1,
                step_number=i + 1,
                step_name=step.get('step_name', ''),
                step_description=step.get('step_description', ''),
                command=step.get('command'),
                expected_output=step.get('expected_output'),
                is_manual=step.get('is_manual', False),
                file_path=step.get('file_path'),
                file_content=step.get('file_content')
            ))
        
        return GenerateStepsResponse(
            success=True,
            message=f"成功生成 {len(step_responses)} 个部署步骤",
            steps=step_responses
        )
        
    except Exception as e:
        logger.error(f"生成部署步骤失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成部署步骤失败: {str(e)}"
        )