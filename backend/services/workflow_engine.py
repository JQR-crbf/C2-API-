#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流程引擎服务
管理15步完整开发流程的执行
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import SessionLocal
from models import (
    WorkflowSession, WorkflowStep, StepAction, Task,
    WorkflowStepType, WorkflowStepStatus, ActionType,
    DeploymentConnectionStatus
)
from services.ssh_manager import ssh_manager
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """工作流程引擎 - 管理完整的15步开发流程"""
    
    def __init__(self):
        self.active_sessions: Dict[int, Dict] = {}  # session_id -> session_info
        
        # 定义15步工作流程模板
        self.workflow_template = [
            {
                "step_number": 1,
                "step_type": WorkflowStepType.DEMAND_ANALYSIS,
                "step_name": "需求分析",
                "step_description": "分析用户需求，生成详细的API规格说明",
                "requires_user_input": True,
                "estimated_duration": 300,  # 5分钟
                "actions": [
                    {"action_type": ActionType.USER_INPUT, "action_name": "收集需求信息"},
                    {"action_type": ActionType.AI_GENERATE, "action_name": "生成API规格"}
                ]
            },
            {
                "step_number": 2,
                "step_type": WorkflowStepType.SERVER_CONNECTION,
                "step_name": "服务器连接",
                "step_description": "建立与目标服务器的SSH连接",
                "requires_user_input": True,
                "estimated_duration": 180,  # 3分钟
                "actions": [
                    {"action_type": ActionType.USER_INPUT, "action_name": "输入服务器信息"},
                    {"action_type": ActionType.SYSTEM_AUTO, "action_name": "建立SSH连接"}
                ]
            },
            {
                "step_number": 3,
                "step_type": WorkflowStepType.CODE_PULL,
                "step_name": "代码拉取",
                "step_description": "从Git仓库拉取最新代码",
                "requires_user_input": False,
                "estimated_duration": 120,  # 2分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "Git拉取代码"}
                ]
            },
            {
                "step_number": 4,
                "step_type": WorkflowStepType.BRANCH_CREATE,
                "step_name": "分支创建",
                "step_description": "创建新的开发分支",
                "requires_user_input": False,
                "estimated_duration": 60,  # 1分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "创建Git分支"}
                ]
            },
            {
                "step_number": 5,
                "step_type": WorkflowStepType.AI_CODE_GENERATION,
                "step_name": "AI代码生成",
                "step_description": "使用AI生成API代码",
                "requires_user_input": False,
                "estimated_duration": 600,  # 10分钟
                "actions": [
                    {"action_type": ActionType.AI_GENERATE, "action_name": "生成API代码"},
                    {"action_type": ActionType.AI_GENERATE, "action_name": "生成测试代码"}
                ]
            },
            {
                "step_number": 6,
                "step_type": WorkflowStepType.CODE_INTEGRATION,
                "step_name": "代码集成",
                "step_description": "将生成的代码集成到项目中",
                "requires_user_input": False,
                "estimated_duration": 300,  # 5分钟
                "actions": [
                    {"action_type": ActionType.FILE_OPERATION, "action_name": "写入代码文件"},
                    {"action_type": ActionType.FILE_OPERATION, "action_name": "更新配置文件"}
                ]
            },
            {
                "step_number": 7,
                "step_type": WorkflowStepType.SYNTAX_CHECK,
                "step_name": "语法检查",
                "step_description": "检查代码语法错误",
                "requires_user_input": False,
                "estimated_duration": 120,  # 2分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "运行语法检查"}
                ]
            },
            {
                "step_number": 8,
                "step_type": WorkflowStepType.UNIT_TEST,
                "step_name": "单元测试",
                "step_description": "运行单元测试",
                "requires_user_input": False,
                "estimated_duration": 300,  # 5分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "运行单元测试"}
                ]
            },
            {
                "step_number": 9,
                "step_type": WorkflowStepType.API_TEST,
                "step_name": "API测试",
                "step_description": "测试API接口功能",
                "requires_user_input": False,
                "estimated_duration": 240,  # 4分钟
                "actions": [
                    {"action_type": ActionType.API_CALL, "action_name": "测试API端点"}
                ]
            },
            {
                "step_number": 10,
                "step_type": WorkflowStepType.PERFORMANCE_TEST,
                "step_name": "性能测试",
                "step_description": "测试API性能指标",
                "requires_user_input": False,
                "estimated_duration": 360,  # 6分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "运行性能测试"}
                ]
            },
            {
                "step_number": 11,
                "step_type": WorkflowStepType.CODE_COMMIT,
                "step_name": "代码提交",
                "step_description": "提交代码到本地仓库",
                "requires_user_input": False,
                "estimated_duration": 60,  # 1分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "Git提交代码"}
                ]
            },
            {
                "step_number": 12,
                "step_type": WorkflowStepType.CODE_PUSH,
                "step_name": "代码推送",
                "step_description": "推送代码到远程仓库",
                "requires_user_input": False,
                "estimated_duration": 120,  # 2分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "Git推送代码"}
                ]
            },
            {
                "step_number": 13,
                "step_type": WorkflowStepType.DEPLOYMENT,
                "step_name": "部署",
                "step_description": "部署应用到生产环境",
                "requires_user_input": False,
                "estimated_duration": 480,  # 8分钟
                "actions": [
                    {"action_type": ActionType.COMMAND_EXEC, "action_name": "部署应用"}
                ]
            },
            {
                "step_number": 14,
                "step_type": WorkflowStepType.ADMIN_REVIEW,
                "step_name": "管理员审核",
                "step_description": "等待管理员审核和批准",
                "requires_user_input": True,
                "estimated_duration": 1800,  # 30分钟
                "actions": [
                    {"action_type": ActionType.NOTIFICATION, "action_name": "通知管理员审核"},
                    {"action_type": ActionType.USER_INPUT, "action_name": "管理员审核决定"}
                ]
            },
            {
                "step_number": 15,
                "step_type": WorkflowStepType.COMPLETION,
                "step_name": "完成",
                "step_description": "工作流程完成，生成报告",
                "requires_user_input": False,
                "estimated_duration": 60,  # 1分钟
                "actions": [
                    {"action_type": ActionType.NOTIFICATION, "action_name": "发送完成通知"},
                    {"action_type": ActionType.SYSTEM_AUTO, "action_name": "生成完成报告"}
                ]
            }
        ]
    
    async def create_workflow_session(
        self, 
        task_id: int, 
        user_id: int, 
        requirements: Dict[str, Any]
    ) -> Tuple[bool, Optional[int], str]:
        """
        创建工作流程会话
        
        Returns:
            Tuple[success, session_id, error_message]
        """
        db = SessionLocal()
        try:
            # 检查是否已有活跃的会话
            existing_session = db.query(WorkflowSession).filter(
                and_(
                    WorkflowSession.task_id == task_id,
                    WorkflowSession.status.in_([
                        WorkflowStepStatus.PENDING,
                        WorkflowStepStatus.IN_PROGRESS,
                        WorkflowStepStatus.REQUIRES_INPUT
                    ])
                )
            ).first()
            
            if existing_session:
                return False, None, "该任务已有活跃的工作流程会话"
            
            # 创建新会话
            session = WorkflowSession(
                task_id=task_id,
                user_id=user_id,
                session_name=f"Task-{task_id}-Workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                requirements=requirements,
                status=WorkflowStepStatus.PENDING
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # 创建工作流程步骤
            await self._create_workflow_steps(db, session.id)
            
            # 添加到活跃会话
            self.active_sessions[session.id] = {
                'session': session,
                'current_step': 1,
                'ssh_connection_id': None,
                'created_at': datetime.now()
            }
            
            logger.info(f"工作流程会话创建成功: {session.id}")
            return True, session.id, ""
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建工作流程会话失败: {str(e)}")
            return False, None, f"创建会话失败: {str(e)}"
        finally:
            db.close()
    
    async def _create_workflow_steps(self, db: Session, session_id: int):
        """创建工作流程步骤"""
        for step_template in self.workflow_template:
            step = WorkflowStep(
                session_id=session_id,
                step_number=step_template["step_number"],
                step_type=step_template["step_type"],
                step_name=step_template["step_name"],
                step_description=step_template["step_description"],
                requires_user_input=step_template["requires_user_input"],
                status=WorkflowStepStatus.PENDING if step_template["step_number"] == 1 else WorkflowStepStatus.BLOCKED
            )
            
            db.add(step)
            db.commit()
            db.refresh(step)
            
            # 创建步骤操作
            for action_template in step_template["actions"]:
                action = StepAction(
                    step_id=step.id,
                    action_type=action_template["action_type"],
                    action_name=action_template["action_name"],
                    action_description=action_template.get("action_description", ""),
                    status=WorkflowStepStatus.PENDING
                )
                db.add(action)
            
            db.commit()
    
    async def get_workflow_status(
        self, 
        session_id: int
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        获取工作流程状态
        
        Returns:
            Tuple[success, status_info, error_message]
        """
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.id == session_id
            ).first()
            
            if not session:
                return False, None, "工作流程会话不存在"
            
            # 获取所有步骤
            steps = db.query(WorkflowStep).filter(
                WorkflowStep.session_id == session_id
            ).order_by(WorkflowStep.step_number).all()
            
            # 计算进度
            completed_steps = len([s for s in steps if s.status == WorkflowStepStatus.COMPLETED])
            progress_percentage = int((completed_steps / len(steps)) * 100)
            
            # 获取当前步骤
            current_step = next(
                (s for s in steps if s.status in [
                    WorkflowStepStatus.IN_PROGRESS, 
                    WorkflowStepStatus.REQUIRES_INPUT
                ]), 
                None
            )
            
            status_info = {
                'session_id': session.id,
                'session_name': session.session_name,
                'status': session.status,
                'current_step': current_step.step_number if current_step else session.current_step,
                'total_steps': session.total_steps,
                'progress_percentage': progress_percentage,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'steps': [
                    {
                        'step_number': step.step_number,
                        'step_name': step.step_name,
                        'step_type': step.step_type,
                        'status': step.status,
                        'requires_user_input': step.requires_user_input,
                        'started_at': step.started_at,
                        'completed_at': step.completed_at,
                        'error_message': step.error_message
                    } for step in steps
                ]
            }
            
            return True, status_info, ""
            
        except Exception as e:
            logger.error(f"获取工作流程状态失败: {str(e)}")
            return False, None, f"获取状态失败: {str(e)}"
        finally:
            db.close()

    async def execute_step(
        self, 
        session_id: int, 
        step_number: int, 
        user_input: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        执行工作流程步骤
        
        Returns:
            Tuple[success, error_message]
        """
        db = SessionLocal()
        try:
            # 获取会话和步骤
            session = db.query(WorkflowSession).filter(
                WorkflowSession.id == session_id
            ).first()
            
            if not session:
                return False, "工作流程会话不存在"
            
            step = db.query(WorkflowStep).filter(
                and_(
                    WorkflowStep.session_id == session_id,
                    WorkflowStep.step_number == step_number
                )
            ).first()
            
            if not step:
                return False, f"步骤 {step_number} 不存在"
            
            if step.status not in [WorkflowStepStatus.PENDING, WorkflowStepStatus.REQUIRES_INPUT]:
                return False, f"步骤 {step_number} 当前状态不允许执行"
            
            # 更新步骤状态
            step.status = WorkflowStepStatus.IN_PROGRESS
            step.started_at = datetime.now()
            if user_input:
                step.user_input_data = user_input
            
            db.commit()
            
            # 执行步骤操作
            success = await self._execute_step_actions(db, step, user_input)
            
            if success:
                step.status = WorkflowStepStatus.COMPLETED
                step.completed_at = datetime.now()
                step.duration_seconds = int((step.completed_at - step.started_at).total_seconds())
                
                # 更新会话进度
                session.current_step = step_number + 1
                session.progress_percentage = int((step_number / session.total_steps) * 100)
                
                # 激活下一步骤
                if step_number < session.total_steps:
                    next_step = db.query(WorkflowStep).filter(
                        and_(
                            WorkflowStep.session_id == session_id,
                            WorkflowStep.step_number == step_number + 1
                        )
                    ).first()
                    
                    if next_step:
                        next_step.status = WorkflowStepStatus.PENDING
                else:
                    # 工作流程完成
                    session.status = WorkflowStepStatus.COMPLETED
                    session.completed_at = datetime.now()
                
                db.commit()
                logger.info(f"步骤 {step_number} 执行成功")
                return True, ""
            else:
                step.status = WorkflowStepStatus.FAILED
                step.retry_count += 1
                db.commit()
                logger.error(f"步骤 {step_number} 执行失败")
                return False, step.error_message or "步骤执行失败"
                
        except Exception as e:
            db.rollback()
            logger.error(f"执行步骤失败: {str(e)}")
            return False, f"执行步骤失败: {str(e)}"
        finally:
            db.close()
    
    async def _execute_step_actions(
        self, 
        db: Session, 
        step: WorkflowStep, 
        user_input: Optional[Dict[str, Any]] = None
    ) -> bool:
        """执行步骤中的所有操作"""
        try:
            actions = db.query(StepAction).filter(
                StepAction.step_id == step.id
            ).all()
            
            for action in actions:
                action.status = WorkflowStepStatus.IN_PROGRESS
                action.started_at = datetime.now()
                db.commit()
                
                success = await self._execute_action(db, step, action, user_input)
                
                if success:
                    action.status = WorkflowStepStatus.COMPLETED
                    action.completed_at = datetime.now()
                    action.duration_seconds = int((action.completed_at - action.started_at).total_seconds())
                else:
                    action.status = WorkflowStepStatus.FAILED
                    step.error_message = action.error_message
                    db.commit()
                    return False
                
                db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"执行步骤操作失败: {str(e)}")
            step.error_message = f"执行操作失败: {str(e)}"
            return False
    
    async def _execute_action(
        self, 
        db: Session, 
        step: WorkflowStep, 
        action: StepAction, 
        user_input: Optional[Dict[str, Any]] = None
    ) -> bool:
        """执行单个操作"""
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.id == step.session_id
            ).first()
            
            if action.action_type == ActionType.USER_INPUT:
                # 用户输入操作
                if user_input:
                    action.output = json.dumps(user_input, ensure_ascii=False)
                    return True
                else:
                    action.error_message = "需要用户输入"
                    return False
            
            elif action.action_type == ActionType.SYSTEM_AUTO:
                # 系统自动操作
                if step.step_type == WorkflowStepType.SERVER_CONNECTION:
                    return await self._handle_server_connection(db, session, action, user_input)
                else:
                    action.output = "系统自动操作完成"
                    return True
            
            elif action.action_type == ActionType.AI_GENERATE:
                # AI生成操作
                return await self._handle_ai_generation(db, session, step, action)
            
            elif action.action_type == ActionType.COMMAND_EXEC:
                # 命令执行操作
                return await self._handle_command_execution(db, session, action)
            
            elif action.action_type == ActionType.FILE_OPERATION:
                # 文件操作
                return await self._handle_file_operation(db, session, action)
            
            elif action.action_type == ActionType.API_CALL:
                # API调用操作
                return await self._handle_api_call(db, session, action)
            
            elif action.action_type == ActionType.NOTIFICATION:
                # 通知操作
                return await self._handle_notification(db, session, action)
            
            else:
                action.error_message = f"未知的操作类型: {action.action_type}"
                return False
                
        except Exception as e:
            logger.error(f"执行操作失败: {str(e)}")
            action.error_message = f"操作执行失败: {str(e)}"
            return False
    
    async def _handle_server_connection(
        self, 
        db: Session, 
        session: WorkflowSession, 
        action: StepAction, 
        user_input: Optional[Dict[str, Any]] = None
    ) -> bool:
        """处理服务器连接"""
        try:
            if not user_input or 'server_info' not in user_input:
                action.error_message = "缺少服务器连接信息"
                return False
            
            server_info = user_input['server_info']
            host = server_info.get('host')
            port = server_info.get('port', 22)
            username = server_info.get('username')
            password = server_info.get('password')
            key_content = server_info.get('key_content')
            
            if not all([host, username]):
                action.error_message = "服务器主机和用户名不能为空"
                return False
            
            # 创建SSH连接
            success, connection_id, error_msg = await ssh_manager.create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                key_content=key_content
            )
            
            if success:
                # 更新会话信息
                session.server_host = host
                session.server_port = port
                session.server_username = username
                session.connection_status = DeploymentConnectionStatus.CONNECTED
                
                # 保存连接ID到活跃会话
                if session.id in self.active_sessions:
                    self.active_sessions[session.id]['ssh_connection_id'] = connection_id
                
                action.output = f"SSH连接建立成功: {connection_id}"
                db.commit()
                return True
            else:
                session.connection_status = DeploymentConnectionStatus.ERROR
                action.error_message = error_msg
                db.commit()
                return False
                
        except Exception as e:
            logger.error(f"处理服务器连接失败: {str(e)}")
            action.error_message = f"服务器连接失败: {str(e)}"
            return False
    
    async def _handle_ai_generation(
        self, 
        db: Session, 
        session: WorkflowSession, 
        step: WorkflowStep, 
        action: StepAction
    ) -> bool:
        """处理AI生成操作"""
        try:
            if step.step_type == WorkflowStepType.DEMAND_ANALYSIS:
                # 生成API规格
                requirements = session.requirements or {}
                prompt = f"根据以下需求生成详细的API规格说明：\n{json.dumps(requirements, ensure_ascii=False, indent=2)}"
                
                # 这里应该调用AI服务生成API规格
                # 暂时使用模拟数据
                api_spec = {
                    "api_name": requirements.get('api_name', 'Generated API'),
                    "description": requirements.get('description', 'AI生成的API'),
                    "endpoints": [
                        {
                            "method": "GET",
                            "path": "/api/example",
                            "description": "示例端点"
                        }
                    ]
                }
                
                session.api_specification = api_spec
                action.output = json.dumps(api_spec, ensure_ascii=False, indent=2)
                db.commit()
                return True
            
            elif step.step_type == WorkflowStepType.AI_CODE_GENERATION:
                # 生成代码
                api_spec = session.api_specification or {}
                
                # 这里应该调用AI服务生成代码
                # 暂时使用模拟数据
                generated_code = f"# AI生成的代码\n# API: {api_spec.get('api_name', 'Unknown')}\n\ndef example_function():\n    return 'Hello, World!'"
                
                action.output = generated_code
                return True
            
            else:
                action.error_message = f"不支持的AI生成类型: {step.step_type}"
                return False
                
        except Exception as e:
            logger.error(f"AI生成操作失败: {str(e)}")
            action.error_message = f"AI生成失败: {str(e)}"
            return False
    
    async def _handle_command_execution(
        self, 
        db: Session, 
        session: WorkflowSession, 
        action: StepAction
    ) -> bool:
        """处理命令执行操作"""
        try:
            # 获取SSH连接
            connection_id = None
            if session.id in self.active_sessions:
                connection_id = self.active_sessions[session.id].get('ssh_connection_id')
            
            if not connection_id:
                action.error_message = "没有可用的SSH连接"
                return False
            
            # 根据操作名称确定要执行的命令
            command = self._get_command_for_action(action.action_name, session)
            
            if not command:
                action.error_message = f"无法确定操作 '{action.action_name}' 对应的命令"
                return False
            
            # 执行命令
            success, stdout, stderr = await ssh_manager.execute_command(
                connection_id=connection_id,
                command=command,
                timeout=300  # 5分钟超时
            )
            
            action.command = command
            action.output = stdout
            
            if success:
                return True
            else:
                action.error_message = stderr or "命令执行失败"
                return False
                
        except Exception as e:
            logger.error(f"命令执行失败: {str(e)}")
            action.error_message = f"命令执行失败: {str(e)}"
            return False
    
    def _get_command_for_action(self, action_name: str, session: WorkflowSession) -> Optional[str]:
        """根据操作名称获取对应的命令"""
        command_map = {
            "Git拉取代码": f"cd {session.project_path or '/tmp'} && git pull origin main",
            "创建Git分支": f"cd {session.project_path or '/tmp'} && git checkout -b {session.branch_name or 'feature-branch'}",
            "运行语法检查": f"cd {session.project_path or '/tmp'} && python -m py_compile *.py",
            "运行单元测试": f"cd {session.project_path or '/tmp'} && python -m pytest tests/",
            "运行性能测试": f"cd {session.project_path or '/tmp'} && python -m pytest tests/ --benchmark-only",
            "Git提交代码": f"cd {session.project_path or '/tmp'} && git add . && git commit -m 'AI generated code'",
            "Git推送代码": f"cd {session.project_path or '/tmp'} && git push origin {session.branch_name or 'feature-branch'}",
            "部署应用": f"cd {session.project_path or '/tmp'} && docker-compose up -d"
        }
        
        return command_map.get(action_name)
    
    async def _handle_file_operation(
        self, 
        db: Session, 
        session: WorkflowSession, 
        action: StepAction
    ) -> bool:
        """处理文件操作"""
        try:
            # 获取SSH连接
            connection_id = None
            if session.id in self.active_sessions:
                connection_id = self.active_sessions[session.id].get('ssh_connection_id')
            
            if not connection_id:
                action.error_message = "没有可用的SSH连接"
                return False
            
            # 这里应该根据具体需求实现文件操作
            # 暂时返回成功
            action.output = "文件操作完成"
            return True
            
        except Exception as e:
            logger.error(f"文件操作失败: {str(e)}")
            action.error_message = f"文件操作失败: {str(e)}"
            return False
    
    async def _handle_api_call(
        self, 
        db: Session, 
        session: WorkflowSession, 
        action: StepAction
    ) -> bool:
        """处理API调用操作"""
        try:
            # 这里应该实现API测试逻辑
            # 暂时返回成功
            action.output = "API测试完成"
            return True
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            action.error_message = f"API调用失败: {str(e)}"
            return False
    
    async def _handle_notification(
        self, 
        db: Session, 
        session: WorkflowSession, 
        action: StepAction
    ) -> bool:
        """处理通知操作"""
        try:
            # 这里应该实现通知逻辑
            # 暂时返回成功
            action.output = "通知已发送"
            return True
            
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
            action.error_message = f"发送通知失败: {str(e)}"
            return False
    
    async def pause_workflow(self, session_id: int) -> Tuple[bool, str]:
        """暂停工作流程"""
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.id == session_id
            ).first()
            
            if not session:
                return False, "工作流程会话不存在"
            
            session.status = WorkflowStepStatus.BLOCKED
            db.commit()
            
            logger.info(f"工作流程已暂停: {session_id}")
            return True, ""
            
        except Exception as e:
            db.rollback()
            logger.error(f"暂停工作流程失败: {str(e)}")
            return False, f"暂停失败: {str(e)}"
        finally:
            db.close()
    
    async def resume_workflow(self, session_id: int) -> Tuple[bool, str]:
        """恢复工作流程"""
        db = SessionLocal()
        try:
            session = db.query(WorkflowSession).filter(
                WorkflowSession.id == session_id
            ).first()
            
            if not session:
                return False, "工作流程会话不存在"
            
            session.status = WorkflowStepStatus.IN_PROGRESS
            db.commit()
            
            logger.info(f"工作流程已恢复: {session_id}")
            return True, ""
            
        except Exception as e:
            db.rollback()
            logger.error(f"恢复工作流程失败: {str(e)}")
            return False, f"恢复失败: {str(e)}"
        finally:
            db.close()

# 创建全局工作流程引擎实例
workflow_engine = WorkflowEngine()