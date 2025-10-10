from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import UserRole, TaskStatus, NotificationType, TaskPriority

# 用户相关模式
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)  # 限制密码最大长度，避免bcrypt 72字节限制
    full_name: Optional[str] = None  # 兼容前端发送的full_name字段

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=6, max_length=50)

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserResponse

# 任务相关模式
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    input_params: Optional[Dict[str, Any]] = None
    output_params: Optional[Dict[str, Any]] = None

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    language: Optional[str] = "python"
    framework: Optional[str] = "fastapi"
    database: Optional[str] = "mysql"
    features: Optional[List[str]] = []
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    admin_comment: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    status: TaskStatus
    priority: TaskPriority
    branch_name: Optional[str] = None
    generated_code: Optional[str] = None
    test_cases: Optional[str] = None
    test_result_image: Optional[str] = None
    test_url: Optional[str] = None
    admin_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: UserResponse
    
    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    size: int

# 任务日志相关模式
class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    user_id: Optional[int] = None
    action_type: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    user_name: Optional[str] = None  # 操作用户名称
    
    class Config:
        from_attributes = True

# 通知相关模式
class NotificationBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    type: NotificationType = NotificationType.INFO

class NotificationCreate(NotificationBase):
    user_id: int
    task_id: Optional[int] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    task_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI代码生成相关模式
class CodeGenerationRequest(BaseModel):
    task_id: int
    requirements: Dict[str, Any]

class CodeGenerationResponse(BaseModel):
    success: bool
    generated_code: Optional[str] = None
    test_cases: Optional[str] = None
    error: Optional[str] = None

# 测试环境相关模式
class TestDeploymentRequest(BaseModel):
    task_id: int
    generated_code: str

class TestDeploymentResponse(BaseModel):
    success: bool
    test_url: Optional[str] = None
    swagger_url: Optional[str] = None
    error: Optional[str] = None

# 管理员统计数据模式
class AdminStats(BaseModel):
    total_users: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    success_rate: float

# 通用响应模式
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# 引导部署相关模式
class ServerConfig(BaseModel):
    host: str = Field(..., description="服务器IP地址或域名")
    port: int = Field(22, description="SSH端口号")
    username: str = Field(..., description="服务器用户名")
    deployment_path: str = Field(..., description="项目部署路径")
    git_repo_url: Optional[str] = Field(None, description="Git仓库地址")

class ServerAuthConfig(BaseModel):
    password: Optional[str] = Field(None, description="SSH密码")
    key_path: Optional[str] = Field(None, description="SSH私钥文件路径")
    key_content: Optional[str] = Field(None, description="SSH私钥内容")

class DeploymentSessionCreate(BaseModel):
    task_id: int
    server_config: ServerConfig
    auth_config: ServerAuthConfig

class DeploymentStepResponse(BaseModel):
    id: int
    step_number: int
    step_name: str
    step_description: str
    command: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeploymentSessionResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    server_host: str
    server_port: int
    server_username: str
    connection_status: str
    current_step: int
    deployment_path: Optional[str] = None
    git_repo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    steps: List[DeploymentStepResponse] = []
    
    class Config:
        from_attributes = True

class DeploymentConnectionResponse(BaseModel):
    success: bool
    connection_id: Optional[str] = None
    message: str

class DeploymentStepExecuteRequest(BaseModel):
    step_id: int
    connection_id: str

class DeploymentStepExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    next_step_id: Optional[int] = None

class ServerConnectionInfo(BaseModel):
    connection_id: str
    host: str
    port: int
    username: str
    created_at: datetime
    last_used: datetime
    is_active: bool