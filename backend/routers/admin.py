from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from database import get_db
from models import Task, User, TaskLog, Notification, TaskStatus, NotificationType, UserRole
from schemas import (
    TaskResponse, TaskUpdate, TaskListResponse, UserResponse,
    AdminStats, MessageResponse, NotificationCreate
)
from routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["管理员"])

# 管理员权限验证装饰器
async def verify_admin(current_user: User = Depends(get_current_user)):
    """验证管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@router.get("/stats", response_model=AdminStats, summary="获取系统统计数据")
async def get_admin_stats(
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """获取系统统计数据"""
    # 统计用户数量
    total_users = db.query(User).count()
    
    # 统计任务数量
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(
        Task.status.in_([TaskStatus.DEPLOYED, TaskStatus.APPROVED])
    ).count()
    pending_tasks = db.query(Task).filter(
        Task.status.in_([
            TaskStatus.SUBMITTED, TaskStatus.CODE_PULLING, 
            TaskStatus.BRANCH_CREATED, TaskStatus.AI_GENERATING,
            TaskStatus.TEST_READY, TaskStatus.TESTING,
            TaskStatus.TEST_COMPLETED, TaskStatus.CODE_PUSHED,
            TaskStatus.UNDER_REVIEW
        ])
    ).count()
    
    # 计算成功率
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return AdminStats(
        total_users=total_users,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        success_rate=round(success_rate, 2)
    )

@router.get("/tasks", response_model=TaskListResponse, summary="获取所有任务列表")
async def get_all_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """获取所有任务列表（管理员）"""
    query = db.query(Task).join(User)
    
    if status:
        query = query.filter(Task.status == status)
    
    if user_id:
        query = query.filter(Task.user_id == user_id)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    tasks = query.order_by(desc(Task.created_at)).offset((page - 1) * size).limit(size).all()
    
    task_responses = []
    for task in tasks:
        task_responses.append(TaskResponse(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            input_params=task.input_params,
            output_params=task.output_params,
            status=task.status,
            branch_name=task.branch_name,
            generated_code=task.generated_code,
            test_cases=task.test_cases,
            test_result_image=task.test_result_image,
            test_url=task.test_url,
            admin_comment=task.admin_comment,
            created_at=task.created_at,
            updated_at=task.updated_at,
            user=task.user
        ))
    
    return TaskListResponse(
        tasks=task_responses,
        total=total,
        page=page,
        size=size
    )

@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="获取任务详情")
async def get_task_by_admin(
    task_id: int,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """获取指定任务的详细信息（管理员）"""
    task = db.query(Task).join(User).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        input_params=task.input_params,
        output_params=task.output_params,
        status=task.status,
        branch_name=task.branch_name,
        generated_code=task.generated_code,
        test_cases=task.test_cases,
        test_result_image=task.test_result_image,
        test_url=task.test_url,
        admin_comment=task.admin_comment,
        created_at=task.created_at,
        updated_at=task.updated_at,
        user=task.user
    )

@router.put("/tasks/{task_id}", response_model=TaskResponse, summary="更新任务状态")
async def update_task_status(
    task_id: int,
    task_update: TaskUpdate,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """更新任务状态（管理员）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新任务信息
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        old_status = task.status
        task.status = task_update.status
        
        # 创建状态变更日志
        task_log = TaskLog(
            task_id=task.id,
            status=task_update.status.value,
            message=f"管理员将任务状态从 {old_status.value} 更改为 {task_update.status.value}"
        )
        db.add(task_log)
        
        # 创建通知
        notification_title = "任务状态更新"
        notification_content = f"您的任务 '{task.title}' 状态已更新为: {task_update.status.value}"
        
        if task_update.status == TaskStatus.APPROVED:
            notification_title = "任务审核通过"
            notification_content = f"恭喜！您的任务 '{task.title}' 已通过审核。"
        elif task_update.status == TaskStatus.REJECTED:
            notification_title = "任务审核未通过"
            notification_content = f"很抱歉，您的任务 '{task.title}' 未通过审核。"
        
        notification = Notification(
            user_id=task.user_id,
            task_id=task.id,
            title=notification_title,
            content=notification_content,
            type=NotificationType.INFO
        )
        db.add(notification)
    
    if task_update.admin_comment is not None:
        task.admin_comment = task_update.admin_comment
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        input_params=task.input_params,
        output_params=task.output_params,
        status=task.status,
        branch_name=task.branch_name,
        generated_code=task.generated_code,
        test_cases=task.test_cases,
        test_result_image=task.test_result_image,
        test_url=task.test_url,
        admin_comment=task.admin_comment,
        created_at=task.created_at,
        updated_at=task.updated_at,
        user=task.user
    )

@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_all_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（管理员）"""
    users = db.query(User).order_by(desc(User.created_at)).offset((page - 1) * size).limit(size).all()
    
    return [UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    ) for user in users]

@router.put("/users/{user_id}/status", response_model=MessageResponse, summary="更新用户状态")
async def update_user_status(
    user_id: int,
    is_active: bool,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """更新用户状态（启用/禁用）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.role == UserRole.ADMIN and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用管理员账户"
        )
    
    user.is_active = is_active
    db.commit()
    
    status_text = "启用" if is_active else "禁用"
    return MessageResponse(message=f"用户 {user.username} 已{status_text}")

@router.post("/notifications", response_model=MessageResponse, summary="发送系统通知")
async def send_system_notification(
    notification_data: NotificationCreate,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """发送系统通知（管理员）"""
    # 验证用户是否存在
    user = db.query(User).filter(User.id == notification_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 创建通知
    notification = Notification(
        user_id=notification_data.user_id,
        task_id=notification_data.task_id,
        title=notification_data.title,
        content=notification_data.content,
        type=notification_data.type
    )
    
    db.add(notification)
    db.commit()
    
    return MessageResponse(message="通知发送成功")