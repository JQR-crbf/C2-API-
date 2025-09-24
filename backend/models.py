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
    CODE_PUSHED = "code_pushed"       # 代码已推送
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
    generated_code = Column(Text)  # AI生成的代码
    test_cases = Column(Text)  # 测试用例
    test_result_image = Column(String(255))  # 测试结果截图路径
    test_url = Column(String(255))  # 测试环境URL
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