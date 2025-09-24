from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from database import get_db
from models import Notification, User
from schemas import NotificationResponse, MessageResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["通知管理"])

@router.get("/", response_model=List[NotificationResponse], summary="获取用户通知列表")
async def get_notifications(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    unread_only: bool = Query(False, description="仅显示未读通知"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的通知列表"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(desc(Notification.created_at)).offset((page - 1) * size).limit(size).all()
    
    return [NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        task_id=notification.task_id,
        title=notification.title,
        content=notification.content,
        type=notification.type,
        is_read=notification.is_read,
        created_at=notification.created_at
    ) for notification in notifications]

@router.get("/unread-count", summary="获取未读通知数量")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的未读通知数量"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}

@router.put("/{notification_id}/read", response_model=MessageResponse, summary="标记通知为已读")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记指定通知为已读"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    notification.is_read = True
    db.commit()
    
    return MessageResponse(message="通知已标记为已读")

@router.put("/mark-all-read", response_model=MessageResponse, summary="标记所有通知为已读")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记当前用户的所有通知为已读"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return MessageResponse(message="所有通知已标记为已读")

@router.delete("/{notification_id}", response_model=MessageResponse, summary="删除通知")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    db.delete(notification)
    db.commit()
    
    return MessageResponse(message="通知删除成功")

@router.delete("/clear-read", response_model=MessageResponse, summary="清除已读通知")
async def clear_read_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清除当前用户的所有已读通知"""
    deleted_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == True
    ).delete()
    
    db.commit()
    
    return MessageResponse(message=f"已清除 {deleted_count} 条已读通知")