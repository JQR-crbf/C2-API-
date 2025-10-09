from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from database import get_db
from models import Task, User, TaskLog, Notification, TaskStatus, NotificationType, UserRole
from schemas import (
    TaskResponse, TaskUpdate, TaskListResponse, UserResponse, UserUpdate,
    AdminStats, MessageResponse, NotificationCreate
)
from routers.auth import get_current_user
from auth_utils import get_password_hash

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
            TaskStatus.SUBMITTED, TaskStatus.AI_GENERATING,
            TaskStatus.CODE_SUBMITTED, TaskStatus.UNDER_REVIEW
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
            priority=task.priority,
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
        priority=task.priority,
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
    
    # 验证拒绝操作必须有备注
    if task_update.status == TaskStatus.REJECTED:
        if not task_update.admin_comment or task_update.admin_comment.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="拒绝任务时必须提供拒绝理由"
            )
    
    # 更新任务信息
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        old_status = task.status
        
        # 处理拒绝逻辑：将状态回退到代码生成步骤
        if task_update.status == TaskStatus.REJECTED:
            task.status = TaskStatus.AI_GENERATING  # 回退到代码生成步骤
            log_message = f"管理员拒绝任务，状态从 {old_status.value} 回退到 {TaskStatus.AI_GENERATING.value}"
            notification_content = f"您的任务 '{task.title}' 被管理员拒绝，已回退到代码生成步骤。拒绝理由：{task_update.admin_comment}"
        else:
            task.status = task_update.status
            log_message = f"管理员将任务状态从 {old_status.value} 更改为 {task_update.status.value}"
            notification_content = f"您的任务 '{task.title}' 状态已更新为: {task_update.status.value}"
        
        # 创建状态变更日志
        task_log = TaskLog(
            task_id=task.id,
            action_type="admin_status_update",
            status=task.status.value,
            message=log_message
        )
        db.add(task_log)
        
        # 创建通知
        notification_title = "任务状态更新"
        
        if task_update.status == TaskStatus.APPROVED:
            notification_title = "任务审核通过"
            notification_content = f"恭喜！您的任务 '{task.title}' 已通过审核。"
        elif task_update.status == TaskStatus.REJECTED:
            notification_title = "任务审核未通过"
            # notification_content 已在上面设置
        
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
        priority=task.priority,
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

@router.delete("/tasks/{task_id}", response_model=MessageResponse, summary="删除任务（管理员）")
async def delete_task_by_admin(
    task_id: int,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """删除指定任务（管理员权限，可删除任何状态的任务）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 先删除相关的日志和通知
    db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
    db.query(Notification).filter(Notification.task_id == task_id).delete()
    
    # 记录删除操作（在删除任务之前）
    task_title = task.title
    task_user_id = task.user_id
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    # 创建删除通知给任务所有者（如果用户还存在）
    user_exists = db.query(User).filter(User.id == task_user_id).first()
    if user_exists:
        notification = Notification(
            user_id=task_user_id,
            title="任务已被删除",
            content=f"您的任务 '{task_title}' 已被管理员删除。",
            type=NotificationType.WARNING
        )
        db.add(notification)
        db.commit()
    
    return MessageResponse(message=f"任务 '{task_title}' 删除成功")

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

@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """更新用户信息（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查用户名是否已被其他用户使用
    if user_update.username and user_update.username != user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
    
    # 更新用户信息
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role
    if user_update.password:
        # 更新密码，需要进行哈希处理
        user.password_hash = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        full_name=user.username
    )

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

@router.post("/tasks/{task_id}/review", response_model=MessageResponse, summary="管理员审核任务")
async def review_task(
    task_id: int,
    action: str,  # "approve" 或 "reject"
    comment: Optional[str] = None,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """管理员审核任务（通过或拒绝）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 验证任务状态是否可以审核
    if task.status != TaskStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有处于审核状态的任务才能进行审核操作"
        )
    
    # 验证操作类型
    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="操作类型必须是 'approve' 或 'reject'"
        )
    
    # 验证拒绝操作必须有备注
    if action == "reject" and (not comment or comment.strip() == ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="拒绝任务时必须提供拒绝理由"
        )
    
    old_status = task.status
    
    if action == "approve":
        # 审核通过，进入下一步（部署完成）
        task.status = TaskStatus.DEPLOYED
        log_message = f"管理员审核通过，任务状态从 {old_status.value} 更改为 {TaskStatus.DEPLOYED.value}"
        notification_title = "任务审核通过"
        notification_content = f"恭喜！您的任务 '{task.title}' 已通过管理员审核，现已进入部署完成阶段。"
        if comment:
            task.admin_comment = comment
            notification_content += f" 管理员备注：{comment}"
    else:  # reject
        # 审核拒绝，回退到代码生成步骤
        task.status = TaskStatus.AI_GENERATING
        task.admin_comment = comment
        log_message = f"管理员审核拒绝，任务状态从 {old_status.value} 回退到 {TaskStatus.AI_GENERATING.value}"
        notification_title = "任务审核未通过"
        notification_content = f"您的任务 '{task.title}' 未通过管理员审核，已回退到代码生成步骤。拒绝理由：{comment}"
    
    # 创建状态变更日志
    task_log = TaskLog(
        task_id=task.id,
        action_type="admin_review",
        status=task.status.value,
        message=log_message
    )
    db.add(task_log)
    
    # 创建通知
    notification = Notification(
        user_id=task.user_id,
        task_id=task.id,
        title=notification_title,
        content=notification_content,
        type=NotificationType.INFO
    )
    db.add(notification)
    
    db.commit()
    
    action_text = "通过" if action == "approve" else "拒绝"
    return MessageResponse(message=f"任务审核{action_text}成功")