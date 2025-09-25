from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class TaskStatus(str, enum.Enum):
    SUBMITTED = "submitted"           # 已提交
    CODE_PULLING = "code_pulling"     # 拉取代码中
    BRANCH_CREATED = "branch_created" # 分支已创建
    AI_GENERATING = "ai_generating"   # AI生成代码中
    TEST_READY = "test_ready"         # 测试环境准备就绪
    TESTING = "testing"               # 测试中
    TEST_COMPLETED = "test_completed" # 测试完成
    DEPLOYMENT_READY = "deployment_ready"         # 准备部署
    DEPLOYMENT_IN_PROGRESS = "deployment_in_progress"  # 部署中
    DEPLOYMENT_COMPLETED = "deployment_completed"      # 部署完成
    CODE_PUSHED = "code_pushed"       # 代码已推送
    GIT_PUSHED = "git_pushed"         # 已推送到Git
    UNDER_REVIEW = "under_review"     # 管理员审核中
    APPROVED = "approved"             # 审核通过
    DEPLOYED = "deployed"             # 已部署
    REJECTED = "rejected"             # 审核拒绝

class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)  # 用户全名
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    input_params = Column(JSON)  # 输入参数定义
    output_params = Column(JSON)  # 输出参数定义
    status = Column(Enum(TaskStatus), default=TaskStatus.SUBMITTED)
    branch_name = Column(String(100))  # Git分支名
    git_branch = Column(String(100))  # Git功能分支名
    git_commit_hash = Column(String(50))  # Git提交哈希
    generated_code = Column(Text)  # AI生成的代码
    test_cases = Column(Text)  # 测试用例
    test_result_image = Column(String(255))  # 测试结果截图路径
    test_url = Column(String(255))  # 测试环境URL
    test_status = Column(String(50))  # 测试状态: pending, running, passed, failed
    test_results = Column(Text)  # 测试结果详情（JSON格式）
    admin_comment = Column(Text)  # 管理员审核意见
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task")
    notifications = relationship("Notification", back_populates="task")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="notifications")
    task = relationship("Task", back_populates="notifications")

class TaskLog(Base):
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="logs")

class DeploymentConnectionStatus(str, enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class DeploymentStepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStepType(str, enum.Enum):
    """工作流步骤类型"""
    DEMAND_ANALYSIS = "demand_analysis"           # 需求分析
    SERVER_CONNECTION = "server_connection"       # 服务器连接
    CODE_PULL = "code_pull"                      # 代码拉取
    BRANCH_CREATE = "branch_create"              # 分支创建
    AI_CODE_GENERATION = "ai_code_generation"    # AI代码生成
    CODE_INTEGRATION = "code_integration"        # 代码集成
    SYNTAX_CHECK = "syntax_check"                # 语法检查
    UNIT_TEST = "unit_test"                      # 单元测试
    API_TEST = "api_test"                        # API测试
    PERFORMANCE_TEST = "performance_test"        # 性能测试
    CODE_COMMIT = "code_commit"                  # 代码提交
    CODE_PUSH = "code_push"                      # 代码推送
    DEPLOYMENT = "deployment"                    # 部署
    ADMIN_REVIEW = "admin_review"                # 管理员审核
    COMPLETION = "completion"                    # 完成

class WorkflowStepStatus(str, enum.Enum):
    """工作流步骤状态"""
    PENDING = "pending"          # 等待中
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    SKIPPED = "skipped"          # 跳过
    BLOCKED = "blocked"          # 阻塞
    REQUIRES_INPUT = "requires_input"  # 需要用户输入

class ActionType(str, enum.Enum):
    """操作类型"""
    USER_INPUT = "user_input"        # 用户输入
    SYSTEM_AUTO = "system_auto"      # 系统自动
    AI_GENERATE = "ai_generate"      # AI生成
    COMMAND_EXEC = "command_exec"    # 命令执行
    FILE_OPERATION = "file_operation" # 文件操作
    API_CALL = "api_call"            # API调用
    VALIDATION = "validation"        # 验证
    NOTIFICATION = "notification"    # 通知

class DeploymentSession(Base):
    """部署会话表 - 记录用户的部署过程"""
    __tablename__ = "deployment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    server_host = Column(String(255), nullable=False)
    server_port = Column(Integer, default=22)
    server_username = Column(String(100), nullable=False)
    connection_status = Column(Enum(DeploymentConnectionStatus), default=DeploymentConnectionStatus.DISCONNECTED)
    current_step = Column(Integer, default=1)
    deployment_path = Column(String(500))  # 项目部署路径
    git_repo_url = Column(String(500))  # Git仓库地址
    ssh_key_path = Column(String(500))  # SSH密钥路径
    ssh_key_content = Column(Text)  # SSH密钥内容
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    task = relationship("Task")
    user = relationship("User")
    steps = relationship("DeploymentStep", back_populates="session")

class DeploymentStep(Base):
    """部署步骤表 - 记录每个步骤的执行情况"""
    __tablename__ = "deployment_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('deployment_sessions.id'), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200), nullable=False)
    step_description = Column(Text)  # 步骤描述
    command = Column(Text)  # 执行的命令
    expected_output = Column(Text)  # 期望的输出
    actual_output = Column(Text)  # 实际输出
    status = Column(Enum(DeploymentStepStatus), default=DeploymentStepStatus.PENDING)
    error_message = Column(Text)
    file_content = Column(Text)  # 需要写入的文件内容
    file_path = Column(String(500))  # 文件路径
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    session = relationship("DeploymentSession", back_populates="steps")

class WorkflowSession(Base):
    """工作流会话表 - 管理完整的15步开发流程"""
    __tablename__ = "workflow_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_name = Column(String(200), nullable=False)  # 会话名称
    current_step = Column(Integer, default=1)  # 当前步骤
    total_steps = Column(Integer, default=15)  # 总步骤数
    status = Column(Enum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING)
    
    # 服务器连接信息
    server_host = Column(String(255))
    server_port = Column(Integer, default=22)
    server_username = Column(String(100))
    server_password = Column(String(255))  # 加密存储
    ssh_key_path = Column(String(500))
    connection_status = Column(Enum(DeploymentConnectionStatus), default=DeploymentConnectionStatus.DISCONNECTED)
    
    # 项目信息
    project_path = Column(String(500))  # 项目路径
    git_repo_url = Column(String(500))  # Git仓库地址
    branch_name = Column(String(100))   # 分支名称
    
    # 需求信息
    requirements = Column(JSON)  # 需求详情
    api_specification = Column(JSON)  # API规格说明
    
    # 进度跟踪
    progress_percentage = Column(Integer, default=0)  # 进度百分比
    estimated_completion = Column(DateTime(timezone=True))  # 预计完成时间
    
    # 错误处理
    error_count = Column(Integer, default=0)  # 错误次数
    last_error = Column(Text)  # 最后一次错误信息
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    task = relationship("Task")
    user = relationship("User")
    steps = relationship("WorkflowStep", back_populates="session", cascade="all, delete-orphan")

class WorkflowStep(Base):
    """工作流步骤表 - 记录每个步骤的详细信息"""
    __tablename__ = "workflow_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('workflow_sessions.id'), nullable=False)
    step_number = Column(Integer, nullable=False)  # 步骤序号
    step_type = Column(Enum(WorkflowStepType), nullable=False)  # 步骤类型
    step_name = Column(String(200), nullable=False)  # 步骤名称
    step_description = Column(Text)  # 步骤描述
    status = Column(Enum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING)
    
    # 执行信息
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)  # 执行时长（秒）
    
    # 输入输出
    input_data = Column(JSON)  # 输入数据
    output_data = Column(JSON)  # 输出数据
    
    # 错误处理
    error_message = Column(Text)  # 错误信息
    retry_count = Column(Integer, default=0)  # 重试次数
    max_retries = Column(Integer, default=3)  # 最大重试次数
    
    # 依赖关系
    depends_on_steps = Column(JSON)  # 依赖的步骤ID列表
    
    # 用户交互
    requires_user_input = Column(Boolean, default=False)  # 是否需要用户输入
    user_input_prompt = Column(Text)  # 用户输入提示
    user_input_data = Column(JSON)  # 用户输入的数据
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    session = relationship("WorkflowSession", back_populates="steps")
    actions = relationship("StepAction", back_populates="step", cascade="all, delete-orphan")

class StepAction(Base):
    """步骤操作表 - 记录每个步骤中的具体操作"""
    __tablename__ = "step_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey('workflow_steps.id'), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)  # 操作类型
    action_name = Column(String(200), nullable=False)  # 操作名称
    action_description = Column(Text)  # 操作描述
    
    # 执行信息
    command = Column(Text)  # 执行的命令
    file_path = Column(String(500))  # 文件路径
    file_content = Column(Text)  # 文件内容
    api_endpoint = Column(String(500))  # API端点
    api_payload = Column(JSON)  # API载荷
    
    # 结果信息
    status = Column(Enum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING)
    output = Column(Text)  # 输出结果
    error_message = Column(Text)  # 错误信息
    
    # 验证信息
    expected_result = Column(Text)  # 期望结果
    validation_rules = Column(JSON)  # 验证规则
    is_validated = Column(Boolean, default=False)  # 是否已验证
    
    # 时间信息
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)  # 执行时长（秒）
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    step = relationship("WorkflowStep", back_populates="actions")