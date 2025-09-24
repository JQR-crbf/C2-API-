from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from database import get_db
from models import Task, User, TaskLog, Notification, TaskStatus, NotificationType
from schemas import (
    TaskCreate, TaskResponse, TaskUpdate, TaskListResponse,
    TaskLogResponse, MessageResponse
)
from routers.auth import get_current_user
from services.ai_service import ai_service
from services.task_processor import task_processor
from services.task_workflow_service import TaskWorkflowService
import zipfile
import io
import os
import asyncio

router = APIRouter(prefix="/tasks", tags=["任务管理"])

@router.post("/", response_model=TaskResponse, summary="创建新任务")
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新任务"""
    # 构建技术栈信息
    tech_stack = {
        "language": task_data.language,
        "framework": task_data.framework,
        "database": task_data.database,
        "features": task_data.features
    }
    
    new_task = Task(
        user_id=current_user.id,
        title=task_data.name,  # 使用name作为title
        description=task_data.description,
        input_params=tech_stack,  # 将技术栈信息存储在input_params中
        output_params=None,
        status=TaskStatus.SUBMITTED
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # 创建任务日志
    task_log = TaskLog(
        task_id=new_task.id,
        status=TaskStatus.SUBMITTED.value,
        message="任务已提交，等待处理"
    )
    db.add(task_log)
    
    # 创建通知
    notification = Notification(
        user_id=current_user.id,
        task_id=new_task.id,
        title="任务创建成功",
        content=f"您的任务 '{new_task.title}' 已成功创建，正在等待处理。",
        type=NotificationType.SUCCESS
    )
    db.add(notification)
    
    db.commit()
    
    # 自动触发AI代码生成（异步执行，不阻塞响应）
    asyncio.create_task(trigger_ai_generation(new_task.id))
    
    # 返回任务信息
    return TaskResponse(
        id=new_task.id,
        user_id=new_task.user_id,
        title=new_task.title,
        description=new_task.description,
        input_params=new_task.input_params,
        output_params=new_task.output_params,
        status=new_task.status,
        branch_name=new_task.branch_name,
        generated_code=new_task.generated_code,
        test_cases=new_task.test_cases,
        test_result_image=new_task.test_result_image,
        test_url=new_task.test_url,
        admin_comment=new_task.admin_comment,
        created_at=new_task.created_at,
        updated_at=new_task.updated_at,
        user=current_user
    )

@router.get("/", response_model=TaskListResponse, summary="获取任务列表")
async def get_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的任务列表"""
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    
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
            user=current_user
        ))
    
    return TaskListResponse(
        tasks=task_responses,
        total=total,
        page=page,
        size=size
    )

@router.get("/{task_id}", response_model=TaskResponse, summary="获取任务详情")
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定任务的详细信息"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
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
        user=current_user
    )

@router.get("/{task_id}/logs", response_model=List[TaskLogResponse], summary="获取任务日志")
async def get_task_logs(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定任务的日志记录"""
    # 验证任务是否属于当前用户
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    logs = db.query(TaskLog).filter(
        TaskLog.task_id == task_id
    ).order_by(TaskLog.created_at).all()
    
    return [TaskLogResponse(
        id=log.id,
        task_id=log.task_id,
        status=log.status,
        message=log.message,
        created_at=log.created_at
    ) for log in logs]

@router.get("/{task_id}/workflow", summary="获取任务工作流程信息")
async def get_task_workflow(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务工作流程信息"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if current_user.role.value != 'admin' and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    workflow_service = TaskWorkflowService(db)
    progress_info = workflow_service.get_task_progress_info(task)
    
    return {
        "task_id": task_id,
        "current_status": task.status.value,
        "workflow": progress_info
    }

@router.post("/{task_id}/advance", summary="推进任务到下一步骤")
async def advance_task_step(
    task_id: int,
    action_data: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """推进任务到下一步骤"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if current_user.role.value != 'admin' and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    workflow_service = TaskWorkflowService(db)
    result = workflow_service.advance_to_next_step(task, current_user, action_data)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result

@router.post("/{task_id}/actions/{action}/complete", summary="标记某个操作为已完成")
async def mark_action_completed(
    task_id: int,
    action: str,
    message: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记某个操作为已完成"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    if current_user.role.value != 'admin' and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    workflow_service = TaskWorkflowService(db)
    success = workflow_service.mark_action_completed(task, action, message)
    
    if not success:
        raise HTTPException(status_code=500, detail="标记操作完成失败")
    
    return {"message": f"操作 {action} 已标记为完成"}

@router.delete("/{task_id}", response_model=MessageResponse, summary="删除任务")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定任务（仅允许删除未开始处理的任务）"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 只允许删除已提交但未开始处理的任务
    if task.status != TaskStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能删除尚未开始处理的任务"
        )
    
    # 删除相关的日志和通知
    db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
    db.query(Notification).filter(Notification.task_id == task_id).delete()
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    return MessageResponse(message="任务删除成功")

@router.get("/{task_id}/download", summary="下载任务生成的代码")
async def download_task_code(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载指定任务生成的代码文件"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if not task.generated_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该任务尚未生成代码"
        )
    
    # 创建内存中的ZIP文件
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 添加主要的API代码文件
        zip_file.writestr("main.py", task.generated_code)
        
        # 添加测试用例文件（如果存在）
        if task.test_cases:
            zip_file.writestr("test_cases.py", task.test_cases)
        
        # 添加README文件
        readme_content = f"""# {task.title}

## 描述
{task.description}

## 技术栈
{task.input_params if task.input_params else '未指定'}

## 使用说明
1. 安装依赖：pip install fastapi uvicorn
2. 运行服务：uvicorn main:app --reload
3. 访问文档：http://localhost:8000/docs

## 生成时间
{task.created_at}

## 任务状态
{task.status.value}
"""
        zip_file.writestr("README.md", readme_content)
        
        # 添加requirements.txt文件
        requirements_content = """fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
sqlalchemy>=1.4.0
python-multipart>=0.0.5
"""
        zip_file.writestr("requirements.txt", requirements_content)
    
    zip_buffer.seek(0)
    
    # 生成文件名
    filename = f"{task.title.replace(' ', '_').replace('/', '_')}_code.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/{task_id}/regenerate", response_model=MessageResponse, summary="重新生成代码")
async def regenerate_task_code(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新生成任务代码"""
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查权限：只有任务创建者或管理员可以重新生成
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作此任务"
        )
    
    # 检查任务状态：只有特定状态的任务才能重新生成
    allowed_statuses = [TaskStatus.SUBMITTED, TaskStatus.AI_GENERATING, TaskStatus.TEST_READY, TaskStatus.TESTING]
    if task.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为 {task.status.value}，无法重新生成代码"
        )
    
    try:
        # 重置任务状态
        task.status = TaskStatus.SUBMITTED
        task.generated_code = None
        task.test_cases = None
        
        # 添加重新生成日志
        task_log = TaskLog(
            task_id=task_id,
            status=TaskStatus.SUBMITTED.value,
            message=f"用户 {current_user.username} 触发重新生成代码"
        )
        db.add(task_log)
        db.commit()
        
        # 异步触发AI代码生成
        asyncio.create_task(trigger_ai_generation(task_id))
        
        return MessageResponse(message="已触发重新生成代码，请稍后查看结果")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成代码失败: {str(e)}"
        )


async def trigger_ai_generation(task_id: int):
    """异步触发AI代码生成"""
    # 创建新的数据库会话，避免跨线程使用同一个Session
    db = next(get_db())
    try:
        # 获取任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # 调用AI服务生成代码
        success, generated_code, test_cases, error_message = await ai_service.generate_code(task, db)
        
        if success:
            print(f"任务 {task_id} AI代码生成成功")
        else:
            print(f"任务 {task_id} AI代码生成失败: {error_message}")
            
    except Exception as e:
        print(f"触发AI代码生成异常: {str(e)}")
        # 记录错误日志
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task_log = TaskLog(
                    task_id=task_id,
                    status=TaskStatus.SUBMITTED.value,
                    message=f"AI代码生成触发失败: {str(e)}"
                )
                db.add(task_log)
                db.commit()
        except:
            pass  # 避免二次异常
    finally:
        # 确保关闭数据库连接
        db.close()