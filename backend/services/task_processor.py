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
        return db.query(Task).filter(
            Task.status.in_([
                TaskStatus.SUBMITTED,
                TaskStatus.CODE_PULLING,
                TaskStatus.BRANCH_CREATED,
                TaskStatus.TEST_READY
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
            if task.status == TaskStatus.SUBMITTED:
                await self._handle_submitted_task(task, db)
            elif task.status == TaskStatus.CODE_PULLING:
                await self._handle_code_pulling_task(task, db)
            elif task.status == TaskStatus.BRANCH_CREATED:
                await self._handle_branch_created_task(task, db)
            elif task.status == TaskStatus.TEST_READY:
                await self._handle_test_ready_task(task, db)
            
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
        # 模拟代码拉取过程
        task.status = TaskStatus.CODE_PULLING
        self._add_task_log(task.id, TaskStatus.CODE_PULLING, "开始拉取代码仓库", db)
        db.commit()
        
        # 模拟拉取延时
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
    
    async def _handle_code_pulling_task(self, task: Task, db: Session):
        """处理代码拉取中的任务"""
        # 这个状态通常很快转换，这里直接跳到下一步
        await self._handle_submitted_task(task, db)
    
    async def _handle_branch_created_task(self, task: Task, db: Session):
        """处理分支已创建的任务"""
        # 调用AI服务生成代码
        success, generated_code, test_cases, error = await ai_service.generate_code(task, db)
        
        if success:
            logger.info(f"任务 {task.id} AI代码生成成功")
            # 发送成功通知
            self._create_notification(
                task.user_id,
                task.id,
                "代码生成完成",
                f"您的任务 '{task.title}' 的代码已生成完成，正在准备测试环境。",
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
    
    async def _handle_test_ready_task(self, task: Task, db: Session):
        """处理测试准备就绪的任务"""
        # 部署到测试环境
        success, test_url, error = await test_service.deploy_to_test_environment(task, db)
        
        if success:
            logger.info(f"任务 {task.id} 测试环境部署成功：{test_url}")
            
            # 更新任务状态为代码已推送（准备管理员审核）
            task.status = TaskStatus.CODE_PUSHED
            self._add_task_log(
                task.id, 
                TaskStatus.CODE_PUSHED, 
                "代码已推送，等待管理员审核", 
                db
            )
            
            # 发送成功通知
            self._create_notification(
                task.user_id,
                task.id,
                "测试环境部署成功",
                f"您的任务 '{task.title}' 已部署到测试环境，访问地址：{test_url}。现在等待管理员审核。",
                NotificationType.SUCCESS,
                db
            )
        else:
            logger.error(f"任务 {task.id} 测试环境部署失败：{error}")
            # 发送失败通知
            self._create_notification(
                task.user_id,
                task.id,
                "测试环境部署失败",
                f"您的任务 '{task.title}' 的测试环境部署失败：{error}",
                NotificationType.ERROR,
                db
            )
        
        db.commit()
    
    def _add_task_log(self, task_id: int, status: TaskStatus, message: str, db: Session):
        """添加任务日志"""
        task_log = TaskLog(
            task_id=task_id,
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