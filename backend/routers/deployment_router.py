from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import logging

from database import get_db
from models import User, Task
from schemas import MessageResponse, ServerConnectionConfig
from routers.auth import get_current_user
from services.ssh_manager import ssh_manager
from services.guided_deployment_service import GuidedDeploymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["部署管理"])

# 请求模型
class ServerAuthConfig(BaseModel):
    password: Optional[str] = None
    key_path: Optional[str] = None
    key_content: Optional[str] = None

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

# 初始化服务
deployment_service = GuidedDeploymentService()

# 注意：session相关路由已移至tasks.py，避免重复定义

# GET session路由也已移至tasks.py

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