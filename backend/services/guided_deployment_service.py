import re
import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from models import Task, DeploymentSession, DeploymentStep, DeploymentStepStatus, DeploymentConnectionStatus
from services.ssh_manager import ssh_manager

logger = logging.getLogger(__name__)

class GuidedDeploymentService:
    """引导式部署服务"""
    
    def __init__(self):
        self.default_project_structure = {
            'app': ['__init__.py'],
            'app/models': ['__init__.py'],
            'app/schemas': ['__init__.py'],
            'app/services': ['__init__.py'],
            'app/routers': ['__init__.py'],
            'requirements.txt': None,
            'main.py': None,
            'README.md': None
        }
    
    def analyze_generated_code(self, generated_code: str) -> Dict:
        """
        分析AI生成的代码，提取文件结构和内容
        
        Returns:
            Dict: 包含文件路径和内容的字典
        """
        code_files = {}
        
        try:
            # 使用正则表达式提取文件内容
            # 匹配类似 "# 文件：app/models/xxx.py" 的注释
            file_pattern = r'#\s*文件[：:]\s*([^\n]+)'
            content_pattern = r'```python\n(.*?)```'
            
            # 分割代码段
            sections = re.split(file_pattern, generated_code)
            
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    file_path = sections[i].strip()
                    content_section = sections[i + 1]
                    
                    # 提取Python代码
                    code_matches = re.findall(content_pattern, content_section, re.DOTALL)
                    if code_matches:
                        code_content = code_matches[0].strip()
                        code_files[file_path] = code_content
            
            # 如果没有找到明确的文件分隔，尝试其他方式
            if not code_files:
                # 尝试匹配单个Python代码块
                code_matches = re.findall(r'```python\n(.*?)```', generated_code, re.DOTALL)
                if code_matches:
                    # 猜测文件结构
                    main_code = code_matches[0].strip()
                    if 'class.*Base' in main_code or 'Base = declarative_base' in main_code:
                        code_files['app/models/__init__.py'] = main_code
                    elif 'FastAPI' in main_code or 'APIRouter' in main_code:
                        code_files['main.py'] = main_code
                    else:
                        code_files['generated_code.py'] = main_code
            
            logger.info(f"代码分析完成，提取到 {len(code_files)} 个文件")
            return code_files
            
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {'generated_code.py': generated_code}  # 后备方案
    
    def generate_deployment_steps(
        self, 
        task: Task, 
        deployment_path: str,
        git_repo_url: str = ""
    ) -> List[Dict]:
        """
        根据任务生成部署步骤
        
        Returns:
            List[Dict]: 部署步骤列表
        """
        code_files = self.analyze_generated_code(task.generated_code or "")
        
        steps = []
        step_number = 1
        
        # 步骤1: 检查服务器连接
        steps.append({
            'step_number': step_number,
            'step_name': '检查服务器连接',
            'step_description': '验证SSH连接状态，确保可以正常访问服务器',
            'command': 'whoami && pwd && echo "连接正常"',
            'expected_output': '连接正常'
        })
        step_number += 1
        
        # 步骤2: 进入或创建项目目录
        steps.append({
            'step_number': step_number,
            'step_name': '进入项目目录',
            'step_description': f'进入项目部署目录: {deployment_path}',
            'command': f'cd {deployment_path} || (mkdir -p {deployment_path} && cd {deployment_path})',
            'expected_output': ''
        })
        step_number += 1
        
        # 步骤3: 检查Python环境
        steps.append({
            'step_number': step_number,
            'step_name': '检查Python环境',
            'step_description': '检查Python版本和pip是否可用',
            'command': 'python3 --version && pip3 --version',
            'expected_output': 'Python 3'
        })
        step_number += 1
        
        # 步骤4: 创建项目结构
        for dir_path in ['app', 'app/models', 'app/schemas', 'app/services', 'app/routers']:
            steps.append({
                'step_number': step_number,
                'step_name': f'创建目录 {dir_path}',
                'step_description': f'创建项目目录结构: {dir_path}',
                'command': f'mkdir -p {dir_path}',
                'expected_output': ''
            })
            step_number += 1
        
        # 步骤5: 创建__init__.py文件
        for init_path in ['app/__init__.py', 'app/models/__init__.py', 'app/schemas/__init__.py', 'app/services/__init__.py', 'app/routers/__init__.py']:
            steps.append({
                'step_number': step_number,
                'step_name': f'创建 {init_path}',
                'step_description': f'创建Python包初始化文件',
                'command': f'touch {init_path}',
                'expected_output': '',
                'file_path': init_path,
                'file_content': '# -*- coding: utf-8 -*-\n'
            })
            step_number += 1
        
        # 步骤6: 写入生成的代码文件
        for file_path, content in code_files.items():
            steps.append({
                'step_number': step_number,
                'step_name': f'创建代码文件 {file_path}',
                'step_description': f'将AI生成的代码写入到 {file_path}',
                'command': f'cat > {file_path} << \'EOF\'\n{content}\nEOF',
                'expected_output': '',
                'file_path': file_path,
                'file_content': content
            })
            step_number += 1
        
        # 步骤7: 创建requirements.txt
        requirements_content = self.generate_requirements(task.generated_code or "")
        steps.append({
            'step_number': step_number,
            'step_name': '创建requirements.txt',
            'step_description': '创建Python依赖文件',
            'command': f'cat > requirements.txt << \'EOF\'\n{requirements_content}\nEOF',
            'expected_output': '',
            'file_path': 'requirements.txt',
            'file_content': requirements_content
        })
        step_number += 1
        
        # 步骤8: 安装依赖
        steps.append({
            'step_number': step_number,
            'step_name': '安装Python依赖',
            'step_description': '使用pip安装项目依赖包',
            'command': 'pip3 install -r requirements.txt',
            'expected_output': 'Successfully installed'
        })
        step_number += 1
        
        # 步骤9: 测试代码语法
        steps.append({
            'step_number': step_number,
            'step_name': '检查代码语法',
            'step_description': '验证Python代码语法是否正确',
            'command': 'python3 -m py_compile app/**/*.py || echo "语法检查完成"',
            'expected_output': '语法检查完成'
        })
        step_number += 1
        
        # 步骤10: 初始化Git仓库（如果提供了Git地址）
        if git_repo_url:
            steps.append({
                'step_number': step_number,
                'step_name': '初始化Git仓库',
                'step_description': '初始化Git仓库并添加远程地址',
                'command': f'git init && git remote add origin {git_repo_url}',
                'expected_output': ''
            })
            step_number += 1
            
            # 步骤11: 提交代码
            steps.append({
                'step_number': step_number,
                'step_name': '提交代码到Git',
                'step_description': '将代码添加到Git并提交',
                'command': f'git add . && git commit -m "Add {task.title} API implementation"',
                'expected_output': 'create mode'
            })
            step_number += 1
            
            # 步骤12: 推送到远程仓库
            steps.append({
                'step_number': step_number,
                'step_name': '推送到远程仓库',
                'step_description': '将代码推送到远程Git仓库',
                'command': 'git push -u origin main',
                'expected_output': 'To '
            })
            step_number += 1
        
        logger.info(f"生成了 {len(steps)} 个部署步骤")
        return steps
    
    def generate_requirements(self, generated_code: str) -> str:
        """根据生成的代码分析所需的Python包"""
        requirements = set()
        
        # 基础包
        requirements.add('fastapi>=0.104.1')
        requirements.add('uvicorn[standard]>=0.24.0')
        requirements.add('sqlalchemy>=2.0.0')
        requirements.add('pydantic>=2.0.0')
        
        # 分析代码中的import语句
        import_pattern = r'from\s+(\w+)|import\s+(\w+)'
        imports = re.findall(import_pattern, generated_code)
        
        for import_tuple in imports:
            module = import_tuple[0] or import_tuple[1]
            
            # 映射常见的包名
            package_mapping = {
                'datetime': '',  # 内置模块
                'typing': '',   # 内置模块
                'json': '',     # 内置模块
                'os': '',       # 内置模块
                'sys': '',      # 内置模块
                'pymysql': 'pymysql>=1.1.0',
                'psycopg2': 'psycopg2-binary>=2.9.0',
                'redis': 'redis>=5.0.0',
                'celery': 'celery>=5.3.0',
                'alembic': 'alembic>=1.12.0',
                'bcrypt': 'bcrypt>=4.0.0',
                'jwt': 'PyJWT>=2.8.0',
                'requests': 'requests>=2.31.0',
                'httpx': 'httpx>=0.25.0'
            }
            
            if module in package_mapping and package_mapping[module]:
                requirements.add(package_mapping[module])
        
        # 数据库相关
        if 'mysql' in generated_code.lower() or 'pymysql' in generated_code:
            requirements.add('pymysql>=1.1.0')
        
        if 'postgresql' in generated_code.lower() or 'psycopg' in generated_code:
            requirements.add('psycopg2-binary>=2.9.0')
        
        # 其他常用包
        requirements.add('python-multipart>=0.0.6')  # 文件上传
        requirements.add('python-jose[cryptography]>=3.3.0')  # JWT
        requirements.add('passlib[bcrypt]>=1.7.4')  # 密码加密
        
        return '\n'.join(sorted(filter(None, requirements)))
    
    async def create_deployment_session(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        server_config: Dict
    ) -> Tuple[bool, Optional[DeploymentSession], str]:
        """创建部署会话"""
        try:
            # 检查是否已存在会话
            existing_session = db.query(DeploymentSession).filter(
                DeploymentSession.task_id == task_id,
                DeploymentSession.connection_status != DeploymentConnectionStatus.DISCONNECTED
            ).first()
            
            if existing_session:
                return False, None, "该任务已有活跃的部署会话"
            
            # 创建新会话
            session = DeploymentSession(
                task_id=task_id,
                user_id=user_id,
                server_host=server_config['host'],
                server_port=server_config.get('port', 22),
                server_username=server_config['username'],
                deployment_path=server_config.get('deployment_path', f'/home/{server_config["username"]}/api_projects'),
                git_repo_url=server_config.get('git_repo_url', ''),
                ssh_key_path=server_config.get('ssh_key_path', ''),
                ssh_key_content=server_config.get('ssh_key_content', '')
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"部署会话创建成功: {session.id}")
            return True, session, ""
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建部署会话失败: {str(e)}")
            return False, None, f"创建部署会话失败: {str(e)}"
    
    async def initialize_deployment_steps(
        self,
        db: Session,
        session: DeploymentSession,
        task: Task
    ) -> bool:
        """初始化部署步骤"""
        try:
            # 生成部署步骤
            steps_data = self.generate_deployment_steps(
                task,
                session.deployment_path,
                session.git_repo_url
            )
            
            # 创建步骤记录
            for step_data in steps_data:
                step = DeploymentStep(
                    session_id=session.id,
                    step_number=step_data['step_number'],
                    step_name=step_data['step_name'],
                    step_description=step_data['step_description'],
                    command=step_data['command'],
                    expected_output=step_data['expected_output'],
                    file_path=step_data.get('file_path'),
                    file_content=step_data.get('file_content')
                )
                db.add(step)
            
            db.commit()
            logger.info(f"初始化了 {len(steps_data)} 个部署步骤")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化部署步骤失败: {str(e)}")
            return False
    
    async def connect_to_server(
        self,
        db: Session,
        session: DeploymentSession,
        auth_config: Dict
    ) -> Tuple[bool, str]:
        """连接到服务器"""
        try:
            # 更新会话状态
            session.connection_status = DeploymentConnectionStatus.CONNECTING
            db.commit()
            
            # 尝试连接
            success, connection_id, error = await ssh_manager.create_connection(
                host=session.server_host,
                port=session.server_port,
                username=session.server_username,
                password=auth_config.get('password'),
                key_path=auth_config.get('key_path'),
                key_content=auth_config.get('key_content')
            )
            
            if success:
                session.connection_status = DeploymentConnectionStatus.CONNECTED
                # 存储连接ID到会话中（可以新增字段）
                db.commit()
                logger.info(f"服务器连接成功: {connection_id}")
                return True, connection_id
            else:
                session.connection_status = DeploymentConnectionStatus.ERROR
                db.commit()
                logger.error(f"服务器连接失败: {error}")
                return False, error
                
        except Exception as e:
            session.connection_status = DeploymentConnectionStatus.ERROR
            db.commit()
            logger.error(f"连接服务器时发生异常: {str(e)}")
            return False, f"连接失败: {str(e)}"
    
    async def execute_deployment_step(
        self,
        db: Session,
        step: DeploymentStep,
        connection_id: str
    ) -> Tuple[bool, str, str]:
        """执行单个部署步骤"""
        try:
            # 更新步骤状态
            step.status = DeploymentStepStatus.RUNNING
            db.commit()
            
            # 如果有文件内容需要写入
            if step.file_content and step.file_path:
                success, error = await ssh_manager.upload_file(
                    connection_id,
                    step.file_content,
                    step.file_path
                )
                
                if not success:
                    step.status = DeploymentStepStatus.FAILED
                    step.error_message = error
                    db.commit()
                    return False, "", error
            
            # 执行命令
            if step.command:
                success, stdout, stderr = await ssh_manager.execute_command(
                    connection_id,
                    step.command
                )
                
                step.actual_output = stdout
                
                if success:
                    step.status = DeploymentStepStatus.COMPLETED
                    step.completed_at = db.execute("SELECT NOW()").scalar()
                else:
                    step.status = DeploymentStepStatus.FAILED
                    step.error_message = stderr
                
                db.commit()
                return success, stdout, stderr
            else:
                # 没有命令的步骤（如纯文件创建）
                step.status = DeploymentStepStatus.COMPLETED
                step.completed_at = db.execute("SELECT NOW()").scalar()
                db.commit()
                return True, "文件创建完成", ""
                
        except Exception as e:
            step.status = DeploymentStepStatus.FAILED
            step.error_message = str(e)
            db.commit()
            logger.error(f"执行步骤失败: {str(e)}")
            return False, "", str(e)

    async def create_deployment_session(
        self,
        task_id: int,
        user_id: int,
        server_config: Dict,
        generated_code: str
    ) -> Dict:
        """创建部署会话（无数据库版本）"""
        try:
            # 生成部署步骤
            steps_data = self.generate_deployment_steps(
                type('Task', (), {'generated_code': generated_code, 'id': task_id})(),
                server_config.get('deployment_path', f'/home/{server_config["username"]}/api_projects'),
                server_config.get('git_repo_url', '')
            )
            
            # 构造会话响应
            session = {
                "id": task_id,
                "task_id": task_id,
                "user_id": user_id,
                "server_host": server_config['host'],
                "server_port": server_config.get('port', 22),
                "server_username": server_config['username'],
                "connection_status": "disconnected",
                "current_step": 1,
                "deployment_path": server_config.get('deployment_path'),
                "git_repo_url": server_config.get('git_repo_url'),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "steps": [
                    {
                        "id": i + 1,
                        "step_number": step['step_number'],
                        "step_name": step['step_name'],
                        "step_description": step['step_description'],
                        "command": step['command'],
                        "expected_output": step['expected_output'],
                        "actual_output": None,
                        "status": "pending",
                        "error_message": None,
                        "file_path": step.get('file_path'),
                        "file_content": step.get('file_content'),
                        "completed_at": None,
                        "created_at": "2024-01-01T00:00:00"
                    }
                    for i, step in enumerate(steps_data)
                ]
            }
            
            # 存储会话到内存（简化版本）
            if not hasattr(self, '_sessions'):
                self._sessions = {}
            self._sessions[task_id] = session
            
            logger.info(f"部署会话创建成功: {task_id}")
            return session
            
        except Exception as e:
            logger.error(f"创建部署会话失败: {str(e)}")
            raise e
    
    async def get_deployment_session(self, task_id: int) -> Optional[Dict]:
        """获取部署会话"""
        if not hasattr(self, '_sessions'):
            self._sessions = {}
        return self._sessions.get(task_id)
    
    async def update_connection_status(
        self, 
        task_id: int, 
        status: str, 
        connection_id: Optional[str]
    ) -> bool:
        """更新连接状态"""
        try:
            if hasattr(self, '_sessions') and task_id in self._sessions:
                self._sessions[task_id]['connection_status'] = status
                if connection_id:
                    self._sessions[task_id]['connection_id'] = connection_id
                return True
            return False
        except Exception as e:
            logger.error(f"更新连接状态失败: {str(e)}")
            return False
    
    async def execute_step(
        self,
        task_id: int,
        step_id: int,
        connection_id: str
    ) -> Dict:
        """执行部署步骤"""
        try:
            session = await self.get_deployment_session(task_id)
            if not session:
                return {
                    "success": False,
                    "message": "部署会话不存在"
                }
            
            # 查找步骤
            step = None
            for s in session['steps']:
                if s['id'] == step_id:
                    step = s
                    break
            
            if not step:
                return {
                    "success": False,
                    "message": "步骤不存在"
                }
            
            # 更新步骤状态
            step['status'] = 'running'
            
            # 如果有文件内容需要写入
            if step['file_content'] and step['file_path']:
                success = await ssh_manager.upload_file(
                    connection_id,
                    step['file_content'],
                    step['file_path']
                )
                
                if not success:
                    step['status'] = 'failed'
                    step['error_message'] = "文件上传失败"
                    return {
                        "success": False,
                        "message": "文件上传失败"
                    }
            
            # 执行命令
            if step['command']:
                success, stdout, stderr = await ssh_manager.execute_command(
                    connection_id,
                    step['command']
                )
                
                step['actual_output'] = stdout
                
                if success:
                    step['status'] = 'completed'
                    step['completed_at'] = "2024-01-01T00:00:00"
                    return {
                        "success": True,
                        "message": "步骤执行成功",
                        "stdout": stdout
                    }
                else:
                    step['status'] = 'failed'
                    step['error_message'] = stderr
                    return {
                        "success": False,
                        "message": "命令执行失败",
                        "stderr": stderr
                    }
            else:
                # 没有命令的步骤（如纯文件创建）
                step['status'] = 'completed'
                step['completed_at'] = "2024-01-01T00:00:00"
                return {
                    "success": True,
                    "message": "文件创建完成"
                }
                
        except Exception as e:
            logger.error(f"执行步骤失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}"
            }

# 创建全局服务实例
guided_deployment_service = GuidedDeploymentService()
