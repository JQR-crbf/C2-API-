import asyncio
import logging
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Task, TaskStatus, TaskLog, Notification, NotificationType
from services.ai_service import ai_service
from services.test_service import test_service
from typing import List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskProcessor:
    """任务处理器 - 负责处理任务队列中的任务"""
    
    def __init__(self):
        self.is_running = False
        self.processing_tasks = set()  # 正在处理的任务ID集合
    
    async def start_processing(self):
        """启动任务处理循环"""
        if self.is_running:
            logger.warning("任务处理器已在运行中")
            return
        
        self.is_running = True
        logger.info("任务处理器启动")
        
        while self.is_running:
            try:
                await self._process_pending_tasks()
                await asyncio.sleep(5)  # 每5秒检查一次
            except Exception as e:
                logger.error(f"任务处理循环异常：{str(e)}")
                await asyncio.sleep(10)  # 异常时等待更长时间
    
    def stop_processing(self):
        """停止任务处理"""
        self.is_running = False
        logger.info("任务处理器停止")
    
    async def _process_pending_tasks(self):
        """处理待处理的任务"""
        db = SessionLocal()
        try:
            # 查找需要处理的任务
            pending_tasks = self._get_pending_tasks(db)
            
            for task in pending_tasks:
                if task.id not in self.processing_tasks:
                    # 异步处理任务
                    asyncio.create_task(self._process_single_task(task.id))
                    
        except Exception as e:
            logger.error(f"获取待处理任务失败：{str(e)}")
        finally:
            db.close()
    
    def _get_pending_tasks(self, db: Session) -> List[Task]:
        """获取待处理的任务列表"""
        # 注释掉自动处理SUBMITTED状态的任务，改为手动聊天生成代码
        return db.query(Task).filter(
            Task.status.in_([
                # TaskStatus.SUBMITTED,  # 不再自动处理已提交的任务
                TaskStatus.AI_GENERATING
            ])
        ).order_by(Task.created_at).limit(5).all()  # 限制并发处理数量
    
    async def _process_single_task(self, task_id: int):
        """处理单个任务"""
        if task_id in self.processing_tasks:
            return
        
        self.processing_tasks.add(task_id)
        db = SessionLocal()
        
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"任务 {task_id} 不存在")
                return
            
            logger.info(f"开始处理任务 {task_id}: {task.title}")
            
            # 根据任务状态执行相应的处理步骤
            # 注释掉自动处理SUBMITTED状态，改为手动聊天生成代码
            # if task.status == TaskStatus.SUBMITTED:
            #     await self._handle_submitted_task(task, db)
            if task.status == TaskStatus.AI_GENERATING:
                await self._handle_ai_generating_task(task, db)
            
        except Exception as e:
            logger.error(f"处理任务 {task_id} 时发生异常：{str(e)}")
            # 记录错误日志
            if 'task' in locals():
                self._add_task_log(
                    task.id, 
                    task.status, 
                    f"任务处理异常：{str(e)}", 
                    db
                )
                db.commit()
        finally:
            self.processing_tasks.discard(task_id)
            db.close()
    
    async def _handle_submitted_task(self, task: Task, db: Session):
        """处理已提交的任务"""
        # 直接进入AI代码生成阶段
        task.status = TaskStatus.AI_GENERATING
        self._add_task_log(task.id, TaskStatus.AI_GENERATING, "开始AI代码生成", db)
        db.commit()
        
        # 模拟AI生成延时
        await asyncio.sleep(2)
        
        # 模拟创建分支
        task.status = TaskStatus.BRANCH_CREATED
        task.branch_name = f"feature/task-{task.id}-{task.title.replace(' ', '-').lower()}"
        self._add_task_log(
            task.id, 
            TaskStatus.BRANCH_CREATED, 
            f"创建分支：{task.branch_name}", 
            db
        )
        db.commit()
        
        # 发送通知
        self._create_notification(
            task.user_id,
            task.id,
            "任务处理中",
            f"您的任务 '{task.title}' 已开始处理，分支 {task.branch_name} 已创建。",
            NotificationType.INFO,
            db
        )
        db.commit()
    
    async def _handle_ai_generating_task(self, task: Task, db: Session):
        """处理AI代码生成任务"""
        # 调用AI服务生成代码
        success, generated_code, test_cases, error = await ai_service.generate_code(task, db)
        
        if success:
            logger.info(f"任务 {task.id} AI代码生成成功")
            # 更新任务状态为代码已提交
            task.status = TaskStatus.CODE_SUBMITTED
            self._add_task_log(task.id, TaskStatus.CODE_SUBMITTED, "AI代码生成完成，代码已提交", db)
            
            # 发送成功通知
            self._create_notification(
                task.user_id,
                task.id,
                "代码生成完成",
                f"您的任务 '{task.title}' 的代码已生成完成，等待管理员审核。",
                NotificationType.SUCCESS,
                db
            )
        else:
            logger.error(f"任务 {task.id} AI代码生成失败：{error}")
            # 发送失败通知
            self._create_notification(
                task.user_id,
                task.id,
                "代码生成失败",
                f"您的任务 '{task.title}' 的代码生成失败：{error}",
                NotificationType.ERROR,
                db
            )
        
        db.commit()
    
    # 旧的处理方法已被简化的工作流程替代
    # 新的工作流程只需要处理 SUBMITTED -> AI_GENERATING -> CODE_SUBMITTED -> APPROVED -> COMPLETED
    
    def _add_task_log(self, task_id: int, status: TaskStatus, message: str, db: Session):
        """添加任务日志"""
        task_log = TaskLog(
            task_id=task_id,
            action_type="task_processing",
            status=status.value,
            message=message
        )
        db.add(task_log)
        
        # 获取任务信息以发送实时更新
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            # 发送任务状态更新通知
            asyncio.create_task(self._send_realtime_notification(
                task.user_id,
                "task_status_update",
                {
                    "task_id": task_id,
                    "status": status.value,
                    "message": message,
                    "title": task.title
                }
            ))
    
    def _create_notification(
        self, 
        user_id: int, 
        task_id: int, 
        title: str, 
        content: str, 
        notification_type: NotificationType,
        db: Session
    ):
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            task_id=task_id,
            title=title,
            content=content,
            type=notification_type
        )
        db.add(notification)
        
        # 发送实时通知
        asyncio.create_task(self._send_realtime_notification(
            user_id, 
            "notification", 
            {
                "id": notification.id,
                "title": title,
                "content": content,
                "type": notification_type.value,
                "task_id": task_id
            }
        ))
    
    async def _send_realtime_notification(self, user_id: int, notification_type: str, data: dict):
        """发送实时通知"""
        try:
            # 动态导入以避免循环导入
            from main import send_realtime_notification
            await send_realtime_notification(user_id, notification_type, data)
        except Exception as e:
            logger.error(f"发送实时通知失败: {e}")

# 创建全局任务处理器实例
task_processor = TaskProcessor()

# 启动任务处理器的函数
async def start_task_processor():
    """启动任务处理器"""
    await task_processor.start_processing()

def stop_task_processor():
    """停止任务处理器"""
    task_processor.stop_processing()