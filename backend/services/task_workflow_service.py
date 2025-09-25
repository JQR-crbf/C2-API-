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
                'reason': '任务已完成所有步骤',
                'current_step': current_step
            }
        
        # 检查当前步骤是否已完成必要操作
        if not self.is_step_completed(task, current_step):
            return {
                'can_advance': False,
                'reason': f'当前步骤 "{current_step["name"]}" 尚未完成必要操作',
                'required_actions': current_step['required_actions'],
                'current_step': current_step,
                'next_step': next_step
            }
        
        # 检查下一步骤的前置条件
        prerequisites_check = self.validate_step_prerequisites(task, next_step)
        if not prerequisites_check['all_met']:
            unmet_conditions = [p['description'] for p in prerequisites_check['unmet_prerequisites']]
            return {
                'can_advance': False,
                'reason': f'下一步骤的前置条件未满足: {"; ".join(unmet_conditions)}',
                'unmet_prerequisites': prerequisites_check['unmet_prerequisites'],
                'current_step': current_step,
                'next_step': next_step
            }
        
        # 检查用户权限
        if not self.has_permission_for_step(user, next_step):
            return {
                'can_advance': False,
                'reason': '您没有权限执行此步骤',
                'current_step': current_step,
                'next_step': next_step
            }
        
        return {
            'can_advance': True,
            'next_step': next_step,
            'current_step': current_step,
            'prerequisites_met': prerequisites_check['prerequisites']
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
        
        try:
            if status == TaskStatus.CODE_PULLING:
                # 检查是否已拉取代码和相关文件是否存在
                return (self.check_action_completed(task, 'pull_code') and 
                       self._validate_code_pull_completion(task))
            
            elif status == TaskStatus.BRANCH_CREATED:
                # 检查是否已创建分支并验证分支名称格式
                return (task.branch_name is not None and 
                       task.branch_name.strip() != '' and
                       self._validate_branch_name(task.branch_name) and
                       self.check_action_completed(task, 'create_branch'))
            
            elif status == TaskStatus.AI_GENERATING:
                # 检查是否已生成代码并验证代码质量
                return (task.generated_code is not None and 
                       task.generated_code.strip() != '' and
                       self._validate_generated_code(task) and
                       self.check_action_completed(task, 'generate_code'))
            
            elif status == TaskStatus.TESTING:
                # 检查是否已运行测试并验证测试结果
                return (self.check_action_completed(task, 'run_tests') and
                       self._validate_test_results(task))
            
            elif status == TaskStatus.TEST_COMPLETED:
                # 检查是否已确认测试结果并验证测试覆盖率
                return (self.check_action_completed(task, 'confirm_tests') and
                       self._validate_test_coverage(task))
            
            elif status == TaskStatus.CODE_PUSHED:
                # 检查是否已推送代码并验证远程仓库状态
                return (self.check_action_completed(task, 'push_code') and
                       self._validate_code_push_completion(task))
            
            elif status == TaskStatus.UNDER_REVIEW:
                # 检查是否已进入审查状态
                return self.check_action_completed(task, 'start_review')
            
            elif status == TaskStatus.APPROVED:
                # 检查是否已通过审查
                return self.check_action_completed(task, 'admin_approve')
            
            elif status == TaskStatus.DEPLOYED:
                # 检查是否已部署
                return (self.check_action_completed(task, 'deploy') and
                       self._validate_deployment_status(task))
        
        except Exception as e:
            logger.error(f"检查步骤完成状态时发生错误: {str(e)}")
            return False
        
        return False
    
    def check_action_completed(self, task: Task, action: str) -> bool:
        """检查特定操作是否已完成"""
        try:
            # 查询任务日志中是否有相应的操作记录
            log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains(f'action:{action}:completed')
            ).first()
            
            if log:
                logger.debug(f"任务 {task.id} 操作 {action} 已完成，时间: {log.created_at}")
                return True
            
            # 检查是否有失败记录
            failed_log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains(f'action:{action}:failed')
            ).first()
            
            if failed_log:
                logger.warning(f"任务 {task.id} 操作 {action} 曾经失败: {failed_log.message}")
            
            return False
        except Exception as e:
            logger.error(f"检查操作完成状态时发生错误: {str(e)}")
            return False
    
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
    
    def _validate_code_pull_completion(self, task: Task) -> bool:
        """验证代码拉取是否完成"""
        try:
            # 检查是否有基础代码文件
            if hasattr(task, 'base_code_path') and task.base_code_path:
                return True
            # 检查是否有相关的代码拉取日志
            return self.check_action_completed(task, 'code_files_downloaded')
        except Exception as e:
            logger.error(f"验证代码拉取完成状态失败: {str(e)}")
            return False
    
    def _validate_branch_name(self, branch_name: str) -> bool:
        """验证分支名称格式"""
        try:
            # 检查分支名称是否符合规范（例如：feature/task-{id}）
            import re
            pattern = r'^(feature|bugfix|hotfix)/[a-zA-Z0-9_-]+$'
            return bool(re.match(pattern, branch_name))
        except Exception as e:
            logger.error(f"验证分支名称失败: {str(e)}")
            return True  # 如果验证失败，默认通过
    
    def _validate_generated_code(self, task: Task) -> bool:
        """验证生成的代码质量"""
        try:
            if not task.generated_code:
                return False
            
            # 基本的代码质量检查
            code = task.generated_code.strip()
            
            # 检查代码长度（至少应该有一些实质内容）
            if len(code) < 50:
                return False
            
            # 检查是否包含基本的Python结构
            basic_patterns = ['def ', 'class ', 'import ', 'from ']
            has_basic_structure = any(pattern in code for pattern in basic_patterns)
            
            return has_basic_structure
        except Exception as e:
            logger.error(f"验证生成代码质量失败: {str(e)}")
            return True  # 如果验证失败，默认通过
    
    def _validate_test_results(self, task: Task) -> bool:
        """验证测试结果"""
        try:
            # 检查是否有测试通过的记录
            test_passed_log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains('tests_passed')
            ).first()
            
            return test_passed_log is not None
        except Exception as e:
            logger.error(f"验证测试结果失败: {str(e)}")
            return False
    
    def _validate_test_coverage(self, task: Task) -> bool:
        """验证测试覆盖率"""
        try:
            # 检查是否有测试覆盖率记录
            coverage_log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains('coverage')
            ).first()
            
            if coverage_log:
                # 可以进一步解析覆盖率数据
                return True
            
            # 如果没有覆盖率记录，检查是否至少有测试完成记录
            return self.check_action_completed(task, 'tests_confirmed')
        except Exception as e:
            logger.error(f"验证测试覆盖率失败: {str(e)}")
            return True  # 如果验证失败，默认通过
    
    def _validate_code_push_completion(self, task: Task) -> bool:
        """验证代码推送完成状态"""
        try:
            # 检查是否有推送成功的记录
            push_success_log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains('push_successful')
            ).first()
            
            return push_success_log is not None
        except Exception as e:
            logger.error(f"验证代码推送完成状态失败: {str(e)}")
            return False
    
    def _validate_deployment_status(self, task: Task) -> bool:
        """验证部署状态"""
        try:
            # 检查是否有部署成功的记录
            deploy_success_log = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains('deployment_successful')
            ).first()
            
            return deploy_success_log is not None
        except Exception as e:
            logger.error(f"验证部署状态失败: {str(e)}")
            return False
    
    def validate_step_prerequisites(self, task: Task, target_step: Dict) -> Dict[str, any]:
        """验证步骤前置条件"""
        try:
            status = target_step['status']
            prerequisites = []
            
            # 定义每个步骤的前置条件
            if status == TaskStatus.BRANCH_CREATED:
                prerequisites.append({
                    'condition': 'code_pulled',
                    'description': '需要先完成代码拉取',
                    'met': self.check_action_completed(task, 'pull_code')
                })
            
            elif status == TaskStatus.AI_GENERATING:
                prerequisites.extend([
                    {
                        'condition': 'branch_created',
                        'description': '需要先创建开发分支',
                        'met': task.branch_name is not None
                    },
                    {
                        'condition': 'requirements_clear',
                        'description': '需求描述应该清晰完整',
                        'met': task.description and len(task.description.strip()) > 20
                    }
                ])
            
            elif status == TaskStatus.TESTING:
                prerequisites.append({
                    'condition': 'code_generated',
                    'description': '需要先完成代码生成',
                    'met': task.generated_code is not None
                })
            
            elif status == TaskStatus.CODE_PUSHED:
                prerequisites.append({
                    'condition': 'tests_passed',
                    'description': '需要先通过所有测试',
                    'met': self._validate_test_results(task)
                })
            
            # 检查所有前置条件是否满足
            unmet_prerequisites = [p for p in prerequisites if not p['met']]
            
            return {
                'all_met': len(unmet_prerequisites) == 0,
                'prerequisites': prerequisites,
                'unmet_prerequisites': unmet_prerequisites
            }
        
        except Exception as e:
            logger.error(f"验证步骤前置条件失败: {str(e)}")
            return {
                 'all_met': True,
                 'prerequisites': [],
                 'unmet_prerequisites': []
             }
    
    def rollback_to_previous_step(self, task: Task, user: User, reason: str = None) -> Dict[str, any]:
        """回滚到上一个步骤"""
        try:
            current_index = self.get_current_step_index(task)
            
            if current_index <= 0:
                return {
                    'success': False,
                    'message': '已经是第一个步骤，无法回滚'
                }
            
            # 检查用户权限（只有管理员可以回滚）
            if user.role.value != 'admin':
                return {
                    'success': False,
                    'message': '只有管理员可以执行回滚操作'
                }
            
            previous_step = self.WORKFLOW_STEPS[current_index - 1]
            old_status = task.status
            
            # 更新任务状态
            task.status = previous_step['status']
            task.updated_at = datetime.utcnow()
            
            # 记录回滚日志
            rollback_reason = reason or '管理员手动回滚'
            log_message = f"任务状态从 {old_status.value} 回滚到 {previous_step['status'].value}，原因: {rollback_reason}"
            
            task_log = TaskLog(
                task_id=task.id,
                status=previous_step['status'].value,
                message=log_message
            )
            self.db.add(task_log)
            self.db.commit()
            
            logger.info(f"任务 {task.id} 已回滚到步骤: {previous_step['name']}")
            
            return {
                'success': True,
                'message': f"已回滚到步骤: {previous_step['name']}",
                'new_status': previous_step['status'].value,
                'step_info': previous_step
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"回滚任务状态失败: {str(e)}")
            return {
                'success': False,
                'message': f"回滚失败: {str(e)}"
            }
    
    def batch_update_task_status(self, task_ids: List[int], target_status: TaskStatus, user: User) -> Dict[str, any]:
        """批量更新任务状态"""
        try:
            if user.role.value != 'admin':
                return {
                    'success': False,
                    'message': '只有管理员可以执行批量状态更新'
                }
            
            updated_tasks = []
            failed_tasks = []
            
            for task_id in task_ids:
                task = self.db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    failed_tasks.append({'task_id': task_id, 'reason': '任务不存在'})
                    continue
                
                old_status = task.status
                task.status = target_status
                task.updated_at = datetime.utcnow()
                
                # 记录状态变更日志
                log_message = f"管理员批量更新：任务状态从 {old_status.value} 更新为 {target_status.value}"
                task_log = TaskLog(
                    task_id=task.id,
                    status=target_status.value,
                    message=log_message
                )
                self.db.add(task_log)
                updated_tasks.append(task_id)
            
            self.db.commit()
            
            return {
                'success': True,
                'message': f"成功更新 {len(updated_tasks)} 个任务状态",
                'updated_tasks': updated_tasks,
                'failed_tasks': failed_tasks
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量更新任务状态失败: {str(e)}")
            return {
                'success': False,
                'message': f"批量更新失败: {str(e)}"
            }
    
    def get_workflow_health_check(self, task: Task) -> Dict[str, any]:
        """获取工作流程健康检查报告"""
        try:
            current_step = self.get_current_step(task)
            health_issues = []
            warnings = []
            
            # 检查任务是否卡在某个步骤太久
            if task.updated_at:
                time_since_update = datetime.utcnow() - task.updated_at
                if time_since_update.total_seconds() > 86400:  # 超过24小时
                    health_issues.append({
                        'type': 'stuck_step',
                        'message': f'任务在步骤 "{current_step["name"]}" 停留超过24小时',
                        'severity': 'high'
                    })
                elif time_since_update.total_seconds() > 3600:  # 超过1小时
                    warnings.append({
                        'type': 'slow_progress',
                        'message': f'任务在步骤 "{current_step["name"]}" 停留超过1小时',
                        'severity': 'medium'
                    })
            
            # 检查是否有失败的操作记录
            failed_actions = self.db.query(TaskLog).filter(
                TaskLog.task_id == task.id,
                TaskLog.message.contains(':failed')
            ).all()
            
            if failed_actions:
                health_issues.append({
                    'type': 'failed_actions',
                    'message': f'发现 {len(failed_actions)} 个失败的操作记录',
                    'severity': 'medium',
                    'details': [log.message for log in failed_actions[-3:]]  # 最近3个失败记录
                })
            
            # 检查步骤完成状态
            step_completion_status = self.is_step_completed(task, current_step)
            if not step_completion_status and not current_step['auto']:
                warnings.append({
                    'type': 'incomplete_step',
                    'message': f'当前步骤 "{current_step["name"]}" 尚未完成',
                    'severity': 'low'
                })
            
            # 计算健康分数
            health_score = 100
            health_score -= len(health_issues) * 20
            health_score -= len(warnings) * 5
            health_score = max(0, health_score)
            
            return {
                'health_score': health_score,
                'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
                'current_step': current_step,
                'health_issues': health_issues,
                'warnings': warnings,
                'last_update': task.updated_at.isoformat() if task.updated_at else None,
                'total_logs': self.db.query(TaskLog).filter(TaskLog.task_id == task.id).count()
            }
        
        except Exception as e:
            logger.error(f"获取工作流程健康检查失败: {str(e)}")
            return {
                'health_score': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def get_step_execution_statistics(self, step_status: TaskStatus = None) -> Dict[str, any]:
        """获取步骤执行统计信息"""
        try:
            # 基础查询
            query = self.db.query(Task)
            if step_status:
                query = query.filter(Task.status == step_status)
            
            tasks = query.all()
            
            # 统计各步骤的任务数量
            step_counts = {}
            for step in self.WORKFLOW_STEPS:
                count = len([t for t in tasks if t.status == step['status']])
                step_counts[step['status'].value] = {
                    'count': count,
                    'step_name': step['name'],
                    'percentage': (count / len(tasks) * 100) if tasks else 0
                }
            
            # 计算平均完成时间（基于日志记录）
            completion_times = {}
            for step in self.WORKFLOW_STEPS:
                step_tasks = [t for t in tasks if t.status == step['status']]
                if step_tasks:
                    avg_time = sum([
                        (t.updated_at - t.created_at).total_seconds() 
                        for t in step_tasks if t.updated_at and t.created_at
                    ]) / len(step_tasks)
                    completion_times[step['status'].value] = {
                        'average_seconds': avg_time,
                        'average_hours': avg_time / 3600
                    }
            
            return {
                'total_tasks': len(tasks),
                'step_distribution': step_counts,
                'completion_times': completion_times,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"获取步骤执行统计失败: {str(e)}")
            return {
                'error': str(e)
            }