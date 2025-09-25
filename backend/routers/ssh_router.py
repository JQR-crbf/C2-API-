from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import logging

from database import get_db
from models import User
from schemas import MessageResponse
from routers.auth import get_current_user
from services.ssh_manager import ssh_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ssh", tags=["SSH连接管理"])

# 请求模型
class SSHConnectionRequest(BaseModel):
    host: str = Field(..., description="服务器主机地址")
    port: int = Field(22, description="SSH端口")
    username: str = Field(..., description="用户名")
    password: Optional[str] = Field(None, description="密码")
    key_path: Optional[str] = Field(None, description="私钥文件路径")
    key_content: Optional[str] = Field(None, description="私钥文件内容")

class CommandExecuteRequest(BaseModel):
    connection_id: str = Field(..., description="连接ID")
    command: str = Field(..., description="要执行的命令")
    timeout: int = Field(30, description="超时时间（秒）")

class FileUploadRequest(BaseModel):
    connection_id: str = Field(..., description="连接ID")
    file_content: str = Field(..., description="文件内容")
    remote_path: str = Field(..., description="远程文件路径")

class FileDownloadRequest(BaseModel):
    connection_id: str = Field(..., description="连接ID")
    remote_path: str = Field(..., description="远程文件路径")

# 响应模型
class SSHConnectionResponse(BaseModel):
    success: bool
    connection_id: Optional[str] = None
    error_message: Optional[str] = None

class CommandExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str

class FileOperationResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None

class ConnectionInfoResponse(BaseModel):
    connection_id: str
    host: str
    port: int
    username: str
    created_at: str
    last_used: str
    is_active: bool

@router.post(
    "/connect",
    response_model=SSHConnectionResponse,
    summary="创建SSH连接",
    description="创建到远程服务器的SSH连接"
)
async def create_ssh_connection(
    request: SSHConnectionRequest,
    current_user: User = Depends(get_current_user)
):
    """创建SSH连接"""
    try:
        success, connection_id, error_message = await ssh_manager.create_connection(
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            key_path=request.key_path,
            key_content=request.key_content
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 创建SSH连接成功: {connection_id}")
            return SSHConnectionResponse(
                success=True,
                connection_id=connection_id
            )
        else:
            logger.warning(f"用户 {current_user.username} 创建SSH连接失败: {error_message}")
            return SSHConnectionResponse(
                success=False,
                error_message=error_message
            )
            
    except Exception as e:
        logger.error(f"创建SSH连接时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建SSH连接失败: {str(e)}"
        )

@router.post(
    "/execute",
    response_model=CommandExecuteResponse,
    summary="执行远程命令",
    description="在SSH连接上执行命令"
)
async def execute_command(
    request: CommandExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """执行远程命令"""
    try:
        success, stdout, stderr = await ssh_manager.execute_command(
            connection_id=request.connection_id,
            command=request.command,
            timeout=request.timeout
        )
        
        logger.info(f"用户 {current_user.username} 执行命令: {request.command} (成功: {success})")
        
        return CommandExecuteResponse(
            success=success,
            stdout=stdout,
            stderr=stderr
        )
        
    except Exception as e:
        logger.error(f"执行命令时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行命令失败: {str(e)}"
        )

@router.post(
    "/upload",
    response_model=FileOperationResponse,
    summary="上传文件",
    description="上传文件到远程服务器"
)
async def upload_file(
    request: FileUploadRequest,
    current_user: User = Depends(get_current_user)
):
    """上传文件到远程服务器"""
    try:
        success, error_message = await ssh_manager.upload_file(
            connection_id=request.connection_id,
            file_content=request.file_content,
            remote_path=request.remote_path
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 上传文件成功: {request.remote_path}")
            return FileOperationResponse(success=True)
        else:
            logger.warning(f"用户 {current_user.username} 上传文件失败: {error_message}")
            return FileOperationResponse(
                success=False,
                error_message=error_message
            )
            
    except Exception as e:
        logger.error(f"上传文件时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文件失败: {str(e)}"
        )

@router.post(
    "/download",
    response_model=FileOperationResponse,
    summary="下载文件",
    description="从远程服务器下载文件"
)
async def download_file(
    request: FileDownloadRequest,
    current_user: User = Depends(get_current_user)
):
    """从远程服务器下载文件"""
    try:
        success, content, error_message = await ssh_manager.download_file(
            connection_id=request.connection_id,
            remote_path=request.remote_path
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 下载文件成功: {request.remote_path}")
            return FileOperationResponse(
                success=True,
                content=content
            )
        else:
            logger.warning(f"用户 {current_user.username} 下载文件失败: {error_message}")
            return FileOperationResponse(
                success=False,
                error_message=error_message
            )
            
    except Exception as e:
        logger.error(f"下载文件时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载文件失败: {str(e)}"
        )

@router.get(
    "/connections",
    response_model=List[ConnectionInfoResponse],
    summary="获取连接列表",
    description="获取当前所有SSH连接的信息"
)
async def list_connections(
    current_user: User = Depends(get_current_user)
):
    """获取所有SSH连接信息"""
    try:
        connections = ssh_manager.list_connections()
        
        result = []
        for conn in connections:
            if conn:  # 确保连接信息不为空
                result.append(ConnectionInfoResponse(
                    connection_id=conn['connection_id'],
                    host=conn['host'],
                    port=conn['port'],
                    username=conn['username'],
                    created_at=conn['created_at'].isoformat(),
                    last_used=conn['last_used'].isoformat(),
                    is_active=conn['is_active']
                ))
        
        logger.info(f"用户 {current_user.username} 查询连接列表，共 {len(result)} 个连接")
        return result
        
    except Exception as e:
        logger.error(f"获取连接列表时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取连接列表失败: {str(e)}"
        )

@router.get(
    "/connection/{connection_id}/status",
    response_model=Dict[str, bool],
    summary="检查连接状态",
    description="检查指定SSH连接是否有效"
)
async def check_connection_status(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """检查SSH连接状态"""
    try:
        is_active = ssh_manager.check_connection(connection_id)
        
        logger.info(f"用户 {current_user.username} 检查连接状态: {connection_id} (活跃: {is_active})")
        
        return {"is_active": is_active}
        
    except Exception as e:
        logger.error(f"检查连接状态时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查连接状态失败: {str(e)}"
        )

@router.delete(
    "/connection/{connection_id}",
    response_model=MessageResponse,
    summary="关闭SSH连接",
    description="关闭指定的SSH连接"
)
async def close_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """关闭SSH连接"""
    try:
        success = ssh_manager.close_connection(connection_id)
        
        if success:
            logger.info(f"用户 {current_user.username} 关闭连接成功: {connection_id}")
            return MessageResponse(message="连接已成功关闭")
        else:
            logger.warning(f"用户 {current_user.username} 关闭连接失败: {connection_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="连接不存在或已关闭"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关闭连接时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关闭连接失败: {str(e)}"
        )

@router.post(
    "/cleanup",
    response_model=MessageResponse,
    summary="清理过期连接",
    description="清理所有过期的SSH连接"
)
async def cleanup_expired_connections(
    current_user: User = Depends(get_current_user)
):
    """清理过期的SSH连接"""
    try:
        # 只有管理员可以执行清理操作
        if current_user.role.value != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以执行此操作"
            )
        
        ssh_manager.cleanup_expired_connections()
        
        logger.info(f"管理员 {current_user.username} 执行了连接清理操作")
        
        return MessageResponse(message="过期连接清理完成")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理过期连接时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理过期连接失败: {str(e)}"
        )