from sqlalchemy.orm import Session
from models import Task, TaskStatus, TaskLog, User
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskWorkflowService:
    """任务工作流程控制服务"""
    
    # 定义任务步骤的顺序和依赖关系
    WORKFLOW_STEPS = [
        {
            'status': TaskStatus.SUBMITTED,
            'name': '任务提交',
            'description': '任务已提交到系统',
            'auto': True,  # 自动完成
            'required_actions': []
        },
        {
            'status': TaskStatus.CODE_PULLING,
            'name': '代码拉取',
            'description': '从代码仓库拉取基础代码',
            'auto': False,  # 需要手动触发
            'required_actions': ['pull_code']
        },
        {
            'status': TaskStatus.BRANCH_CREATED,
            'name': '分支创建',
            'description': '为此任务创建专用开发分支',
            'auto': False,
            'required_actions': ['create_branch']
        },
        {
            'status': TaskStatus.AI_GENERATING,
            'name': 'AI代码生成',
            'description': 'AI正在根据需求生成代码',
            'auto': False,
            'required_actions': ['generate_code']
        },
        {
            'status': TaskStatus.TEST_READY,
            'name': '测试准备',
            'description': '代码生成完成，准备进行测试',
            'auto': True,  # AI生成完成后自动进入
            'required_actions': []
        },
        {
            'status': TaskStatus.TESTING,
            'name': '代码测试',
            'description': '正在执行自动化测试',
            'auto': False,
            'required_actions': ['run_tests']
        },
        {
            'status': TaskStatus.TEST_COMPLETED,
            'name': '测试完成',
            'description': '所有测试已通过',
            'auto': False,
            'required_actions': ['confirm_tests']
        },
        {
            'status': TaskStatus.CODE_PUSHED,
            'name': '代码推送',
            'description': '代码已推送到仓库',
            'auto': False,
            'required_actions': ['push_code']
        },
        {
            'status': TaskStatus.UNDER_REVIEW,
            'name': '代码审查',
            'description': '代码正在接受人工审查',
            'auto': True,  # 推送后自动进入审查
            'required_actions': []
        },
        {
            'status': TaskStatus.APPROVED,
            'name': '审查通过',
            'description': '代码审查已通过',
            'auto': False,  # 管理员操作
            'required_actions': ['admin_approve']
        },
        {
            'status': TaskStatus.DEPLOYED,
            'name': '部署完成',
            'description': 'API已成功部署到生产环境',
            'auto': False,
            'required_actions': ['deploy']
        }
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_workflow_steps(self) -> List[Dict]:
        """获取工作流程步骤定义"""
        return self.WORKFLOW_STEPS
    
    def get_current_step_index(self, task: Task) -> int:
        """获取当前步骤在工作流中的索引"""
        for i, step in enumerate(self.WORKFLOW_STEPS):
            if step['status'] == task.status:
                return i
        return 0
    
    def get_next_step(self, task: Task) -> Optional[Dict]:
        """获取下一个步骤"""
        current_index = self.get_current_step_index(task)
        if current_index < len(self.WORKFLOW_STEPS) - 1:
            return self.WORKFLOW_STEPS[current_index + 1]
        return None
    
    def can_advance_to_next_step(self, task: Task, user: User) -> Dict[str, any]:
        """检查是否可以进入下一步骤"""
        current_step = self.get_current_step(task)
        next_step = self.get_next_step(task)
        
        if not next_step:
            return {
                'can_advance': False,
                'reason': '任务已完成所有步骤'
            }
        
        # 检查当前步骤是否已完成必要操作
        if not self.is_step_completed(task, current_step):
            return {
                'can_advance': False,
                'reason': f'当前步骤 "{current_step["name"]}" 尚未完成必要操作',
                'required_actions': current_step['required_actions']
            }
        
        # 检查用户权限
        if not self.has_permission_for_step(user, next_step):
            return {
                'can_advance': False,
                'reason': '您没有权限执行此步骤'
            }
        
        return {
            'can_advance': True,
            'next_step': next_step
        }
    
    def get_current_step(self, task: Task) -> Dict:
        """获取当前步骤信息"""
        current_index = self.get_current_step_index(task)
        return self.WORKFLOW_STEPS[current_index]
    
    def is_step_completed(self, task: Task, step: Dict) -> bool:
        """检查步骤是否已完成"""
        # 如果是自动步骤，认为已完成
        if step['auto']:
            return True
        
        # 根据步骤类型检查完成条件
        status = step['status']
        
        if status == TaskStatus.CODE_PULLING:
            # 检查是否已拉取代码（这里可以检查相关日志或标记）
            return self.check_action_completed(task, 'pull_code')
        
        elif status == TaskStatus.BRANCH_CREATED:
            # 检查是否已创建分支
            return task.branch_name is not None and task.branch_name.strip() != ''
        
        elif status == TaskStatus.AI_GENERATING:
            # 检查是否已生成代码
            return task.generated_code is not None and task.generated_code.strip() != ''
        
        elif status == TaskStatus.TESTING:
            # 检查是否已运行测试
            return self.check_action_completed(task, 'run_tests')
        
        elif status == TaskStatus.TEST_COMPLETED:
            # 检查是否已确认测试结果
            return self.check_action_completed(task, 'confirm_tests')
        
        elif status == TaskStatus.CODE_PUSHED:
            # 检查是否已推送代码
            return self.check_action_completed(task, 'push_code')
        
        return False
    
    def check_action_completed(self, task: Task, action: str) -> bool:
        """检查特定操作是否已完成"""
        # 查询任务日志中是否有相应的操作记录
        log = self.db.query(TaskLog).filter(
            TaskLog.task_id == task.id,
            TaskLog.message.contains(f'action:{action}:completed')
        ).first()
        return log is not None
    
    def has_permission_for_step(self, user: User, step: Dict) -> bool:
        """检查用户是否有权限执行某个步骤"""
        # 管理员可以执行所有步骤
        if user.role.value == 'admin':
            return True
        
        # 普通用户不能执行管理员专属步骤
        admin_only_steps = [TaskStatus.APPROVED, TaskStatus.DEPLOYED]
        if step['status'] in admin_only_steps:
            return False
        
        return True
    
    def advance_to_next_step(self, task: Task, user: User, action_data: Dict = None) -> Dict[str, any]:
        """推进到下一步骤"""
        # 检查是否可以推进
        check_result = self.can_advance_to_next_step(task, user)
        if not check_result['can_advance']:
            return {
                'success': False,
                'message': check_result['reason'],
                'required_actions': check_result.get('required_actions', [])
            }
        
        next_step = check_result['next_step']
        old_status = task.status
        
        # 更新任务状态
        task.status = next_step['status']
        task.updated_at = datetime.utcnow()
        
        # 记录状态变更日志
        log_message = f"任务状态从 {old_status.value} 推进到 {next_step['status'].value}"
        if action_data:
            log_message += f"，操作数据: {action_data}"
        
        task_log = TaskLog(
            task_id=task.id,
            status=next_step['status'].value,
            message=log_message
        )
        self.db.add(task_log)
        
        try:
            self.db.commit()
            logger.info(f"任务 {task.id} 状态已更新为 {next_step['status'].value}")
            
            return {
                'success': True,
                'message': f"已推进到步骤: {next_step['name']}",
                'new_status': next_step['status'].value,
                'step_info': next_step
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务状态失败: {str(e)}")
            return {
                'success': False,
                'message': f"状态更新失败: {str(e)}"
            }
    
    def mark_action_completed(self, task: Task, action: str, message: str = None) -> bool:
        """标记某个操作为已完成"""
        try:
            log_message = f"action:{action}:completed"
            if message:
                log_message += f" - {message}"
            
            task_log = TaskLog(
                task_id=task.id,
                status=task.status.value,
                message=log_message
            )
            self.db.add(task_log)
            self.db.commit()
            
            logger.info(f"任务 {task.id} 操作 {action} 已标记为完成")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"标记操作完成失败: {str(e)}")
            return False
    
    def get_task_progress_info(self, task: Task) -> Dict[str, any]:
        """获取任务的详细进度信息"""
        current_index = self.get_current_step_index(task)
        current_step = self.WORKFLOW_STEPS[current_index]
        
        # 计算已完成的步骤
        completed_steps = []
        pending_steps = []
        
        for i, step in enumerate(self.WORKFLOW_STEPS):
            step_info = {
                'index': i,
                'status': step['status'].value,
                'name': step['name'],
                'description': step['description'],
                'auto': step['auto'],
                'required_actions': step['required_actions']
            }
            
            if i < current_index:
                step_info['completed'] = True
                step_info['current'] = False
                completed_steps.append(step_info)
            elif i == current_index:
                step_info['completed'] = self.is_step_completed(task, step)
                step_info['current'] = True
                step_info['can_advance'] = step_info['completed']
                completed_steps.append(step_info)
            else:
                step_info['completed'] = False
                step_info['current'] = False
                pending_steps.append(step_info)
        
        return {
            'current_step_index': current_index,
            'current_step': current_step,
            'total_steps': len(self.WORKFLOW_STEPS),
            'progress_percentage': int((current_index / (len(self.WORKFLOW_STEPS) - 1)) * 100),
            'completed_steps': completed_steps,
            'pending_steps': pending_steps,
            'all_steps': completed_steps + pending_steps
        }
