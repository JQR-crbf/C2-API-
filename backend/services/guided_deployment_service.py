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
    
    def analyze_generated_code(self, generated_code: str) -> Dict[str, str]:
        """
        分析生成的代码，提取文件路径和内容
        根据API开发指南的标准结构分析代码
        
        Args:
            generated_code: AI生成的代码字符串
            
        Returns:
            Dict[str, str]: 文件路径到内容的映射
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
            
            # 如果没有找到明确的文件分隔，尝试根据API开发指南结构分析
            if not code_files:
                code_files = self._analyze_code_structure(generated_code)
            
            logger.info(f"代码分析完成，提取到 {len(code_files)} 个文件")
            return code_files
            
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {'generated_code.py': generated_code}  # 后备方案
    
    def _analyze_code_structure(self, generated_code: str) -> Dict[str, str]:
        """
        根据API开发指南的标准结构分析代码
        """
        code_files = {}
        
        # 尝试匹配单个Python代码块
        code_matches = re.findall(r'```python\n(.*?)```', generated_code, re.DOTALL)
        if code_matches:
            main_code = code_matches[0].strip()
            
            # 1. 数据模型文件 (app/models/)
            if "class" in main_code and "Base" in main_code and "__tablename__" in main_code:
                # 检测到数据模型
                model_name = self._extract_class_name(main_code, "Base")
                if model_name:
                    code_files[f"app/models/{model_name.lower()}.py"] = self._extract_model_code(main_code)
            
            # 2. 数据模式文件 (app/schemas/)
            elif "BaseModel" in main_code and "Field" in main_code:
                # 检测到Pydantic模式
                schema_name = self._extract_class_name(main_code, "BaseModel")
                if schema_name:
                    code_files[f"app/schemas/{schema_name.lower()}.py"] = self._extract_schema_code(main_code)
            
            # 3. 服务层文件 (app/services/)
            elif "Service" in main_code and "def" in main_code:
                # 检测到服务类
                service_name = self._extract_class_name(main_code, "Service")
                if service_name:
                    code_files[f"app/services/{service_name.lower()}.py"] = self._extract_service_code(main_code)
            
            # 4. 路由层文件 (app/api/v1/)
            elif "APIRouter" in main_code and "@router" in main_code:
                # 检测到路由定义
                router_name = self._extract_router_name(main_code)
                if router_name:
                    code_files[f"app/api/v1/{router_name.lower()}.py"] = self._extract_router_code(main_code)
            
            # 5. 如果无法识别具体类型，默认为主文件
            else:
                code_files["app/main.py"] = main_code
        else:
            # 没有代码块，直接使用原始代码
            code_files["generated_code.py"] = generated_code
        
        return code_files
    
    def _extract_class_name(self, code: str, base_class: str) -> str:
        """
        从代码中提取类名
        """
        pattern = rf'class\s+(\w+).*{base_class}'
        match = re.search(pattern, code)
        return match.group(1) if match else "unknown"
    
    def _extract_router_name(self, code: str) -> str:
        """
        从路由代码中提取路由名称
        """
        # 尝试从注释或路径中提取名称
        pattern = r'prefix="/([^"]+)"'
        match = re.search(pattern, code)
        if match:
            return match.group(1).replace('-', '_')
        return "api"
    
    def _extract_model_code(self, code: str) -> str:
        """
        提取模型相关代码
        """
        # 这里可以进行更复杂的代码提取和清理
        return code
    
    def _extract_schema_code(self, code: str) -> str:
        """
        提取模式相关代码
        """
        return code
    
    def _extract_service_code(self, code: str) -> str:
        """
        提取服务相关代码
        """
        return code
    
    def _extract_router_code(self, code: str) -> str:
        """
        提取路由相关代码
        """
        return code
    
    def generate_deployment_steps(
        self, 
        task: Task, 
        deployment_path: str = "/opt/api/ai_interface_project",
        git_repo_url: str = ""
    ) -> List[Dict]:
        """
        根据任务生成部署步骤 - 严格按照用户提供的37步详细指南
        
        Returns:
            List[Dict]: 部署步骤列表
        """
        steps = []
        
        # 步骤1: 进入项目目录
        steps.append({
            'step_number': 1,
            'step_name': '进入项目目录',
            'command': f'cd {deployment_path}'
        })
        
        # 步骤2: 切换到主分支
        steps.append({
            'step_number': 2,
            'step_name': '切换到主分支',
            'command': 'git switch main'
        })
        
        # 步骤3: 获取最新的代码
        steps.append({
            'step_number': 3,
            'step_name': '获取最新的代码',
            'command': 'git pull origin main'
        })
        
        # 步骤4: 创建新的分支
        steps.append({
            'step_number': 4,
            'step_name': '创建新的分支',
            'command': 'git switch -c feature/your-new-api'
        })
        
        # 步骤5: 打开文件写入
        steps.append({
            'step_number': 5,
            'step_name': '打开文件写入',
            'command': 'nano app/models/your_model.py'
        })
        
        # 步骤6: 写入代码
        steps.append({
            'step_number': 6,
            'step_name': '写入代码（这个是直接复制粘贴之前AI写的内容）',
            'command': '写入代码（这个是直接复制粘贴之前AI写的内容）'
        })
        
        # 步骤7: 保存代码
        steps.append({
            'step_number': 7,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤8: 退出文件编辑
        steps.append({
            'step_number': 8,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤9: 打开文件写入
        steps.append({
            'step_number': 9,
            'step_name': '打开文件写入',
            'command': 'nano app/schemas/your_schema.py'
        })
        
        # 步骤10: 写入代码
        steps.append({
            'step_number': 10,
            'step_name': '写入代码（这个是直接复制粘贴之前AI写的内容）',
            'command': '写入代码（这个是直接复制粘贴之前AI写的内容）'
        })
        
        # 步骤11: 保存代码
        steps.append({
            'step_number': 11,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤12: 退出文件编辑
        steps.append({
            'step_number': 12,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤13: 打开文件写入
        steps.append({
            'step_number': 13,
            'step_name': '打开文件写入',
            'command': 'nano app/services/your_service.py'
        })
        
        # 步骤14: 写入代码
        steps.append({
            'step_number': 14,
            'step_name': '写入代码（这个是直接复制粘贴之前AI写的内容）',
            'command': '写入代码（这个是直接复制粘贴之前AI写的内容）'
        })
        
        # 步骤15: 保存代码
        steps.append({
            'step_number': 15,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤16: 退出文件编辑
        steps.append({
            'step_number': 16,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤17: 打开文件写入
        steps.append({
            'step_number': 17,
            'step_name': '打开文件写入',
            'command': 'nano app/api/v1/your_api.py'
        })
        
        # 步骤18: 写入代码
        steps.append({
            'step_number': 18,
            'step_name': '写入代码（这个是直接复制粘贴之前AI写的内容）',
            'command': '写入代码（这个是直接复制粘贴之前AI写的内容）'
        })
        
        # 步骤19: 保存代码
        steps.append({
            'step_number': 19,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤20: 退出文件编辑
        steps.append({
            'step_number': 20,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤21: 打开文件写入（写入到最后）
        steps.append({
            'step_number': 21,
            'step_name': '打开文件写入（写入到最后）',
            'command': 'nano app/api/v1/__init__.py'
        })
        
        # 步骤22: 保存代码
        steps.append({
            'step_number': 22,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤23: 退出文件编辑
        steps.append({
            'step_number': 23,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤24: 退出文件编辑（键盘快捷键 ctrl+）
        steps.append({
            'step_number': 24,
            'step_name': '退出文件编辑（键盘快捷键 ctrl+）',
            'command': '退出文件编辑（键盘快捷键 ctrl+）'
        })
        
        # 步骤25: 打开文件写入（写入到最后）
        steps.append({
            'step_number': 25,
            'step_name': '打开文件写入（写入到最后）',
            'command': 'nano app/main.py'
        })
        
        # 步骤26: 写入代码
        steps.append({
            'step_number': 26,
            'step_name': '写入代码（这个是直接复制粘贴之前AI写的内容）',
            'command': '写入代码（这个是直接复制粘贴之前AI写的内容）'
        })
        
        # 步骤27: 保存代码
        steps.append({
            'step_number': 27,
            'step_name': '保存代码 按下 Ctrl + O（英文O），然后按 Enter 键确认',
            'command': 'Ctrl + O（英文O），然后按 Enter 键确认'
        })
        
        # 步骤28: 退出文件编辑
        steps.append({
            'step_number': 28,
            'step_name': '退出文件编辑 按下 Ctrl + X 返回到命令行',
            'command': 'Ctrl + X 返回到命令行'
        })
        
        # 步骤29: 进入到根目录
        steps.append({
            'step_number': 29,
            'step_name': '进入到根目录',
            'command': f'cd {deployment_path}'
        })
        
        # 步骤30: 创建虚拟环境
        steps.append({
            'step_number': 30,
            'step_name': '创建虚拟环境',
            'command': 'python3 -m venv venv'
        })
        
        # 步骤31: 激活虚拟环境
        steps.append({
            'step_number': 31,
            'step_name': '激活虚拟环境',
            'command': 'source venv/bin/activate'
        })
        
        # 步骤32: 启动服务
        steps.append({
            'step_number': 32,
            'step_name': '启动服务',
            'command': 'uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
        })
        
        # 步骤33: 是否报错
        steps.append({
            'step_number': 33,
            'step_name': '是否报错（是，把报错信息发给ai，根据ai的提示进行修改；否，点击下一步）',
            'command': '是否报错（是，把报错信息发给ai，根据ai的提示进行修改；否，点击下一步）'
        })
        
        # 步骤34: 代码打包
        steps.append({
            'step_number': 34,
            'step_name': '代码打包',
            'command': 'git add .'
        })
        
        # 步骤35: 代码备注
        steps.append({
            'step_number': 35,
            'step_name': '代码备注',
            'command': 'git commit -m "本次修改的内容，可用中文描述"'
        })
        
        # 步骤36: 代码推送
        steps.append({
            'step_number': 36,
            'step_name': '代码推送',
            'command': 'git push -u origin feature/your-new-api'
        })
        
        # 步骤37: 部署完成
        steps.append({
            'step_number': 37,
            'step_name': '部署完成',
            'command': '部署完成'
        })
        
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
                ssh_key_path=server_config.get('ssh_key_path', '')
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

    async def mark_step_completed(
        self,
        db: Session,
        task_id: int,
        step_number: int,
        user_id: int
    ) -> Tuple[bool, str]:
        """标记部署步骤为已完成"""
        try:
            # 查找对应的部署会话
            session = db.query(DeploymentSession).filter(
                DeploymentSession.task_id == task_id,
                DeploymentSession.user_id == user_id
            ).first()
            
            # 如果没有部署会话，创建一个临时会话用于记录步骤状态
            if not session:
                # 创建临时部署会话
                from models import Task
                task = db.query(Task).filter(Task.id == task_id).first()
                session = DeploymentSession(
                    task_id=task_id,
                    user_id=user_id,
                    server_host="localhost",  # 临时值
                    server_port=22,
                    server_username="temp",  # 临时值
                    deployment_path="/tmp",  # 临时值
                    connection_status=DeploymentConnectionStatus.DISCONNECTED
                )
                db.add(session)
                db.flush()  # 获取session.id
                
                # 为新会话生成步骤
                if task:
                    steps_data = self.generate_deployment_steps(task)
                    # 创建步骤记录
                    for step_data in steps_data:
                        step = DeploymentStep(
                            session_id=session.id,
                            step_number=step_data['step_number'],
                            step_name=step_data['step_name'],
                            step_description=step_data.get('step_description', ''),
                            command=step_data.get('command', ''),
                            expected_output=step_data.get('expected_output', ''),
                            status=DeploymentStepStatus.PENDING
                        )
                        db.add(step)
                    db.flush()  # 确保步骤也被添加到数据库
                    logger.info(f"为任务 {task_id} 创建了 {len(steps_data)} 个部署步骤")
            
            # 查找对应的步骤
            step = db.query(DeploymentStep).filter(
                DeploymentStep.session_id == session.id,
                DeploymentStep.step_number == step_number
            ).first()
            
            if not step:
                return False, f"未找到步骤 {step_number}"
            
            # 更新步骤状态
            step.status = DeploymentStepStatus.COMPLETED
            step.completed_at = db.execute("SELECT NOW()").scalar()
            
            db.commit()
            logger.info(f"步骤 {step_number} 已标记为完成")
            return True, "步骤已标记为完成"
            
        except Exception as e:
            db.rollback()
            logger.error(f"标记步骤完成失败: {str(e)}")
            return False, f"标记步骤完成失败: {str(e)}"
    
    async def get_steps_status(
        self,
        db: Session,
        task_id: int,
        user_id: int
    ) -> Tuple[bool, List[Dict], str]:
        """获取任务的所有部署步骤状态"""
        try:
            # 查找对应的部署会话
            session = db.query(DeploymentSession).filter(
                DeploymentSession.task_id == task_id,
                DeploymentSession.user_id == user_id
            ).first()
            
            if not session:
                return False, [], "未找到对应的部署会话"
            
            # 查找所有步骤
            steps = db.query(DeploymentStep).filter(
                DeploymentStep.session_id == session.id
            ).order_by(DeploymentStep.step_number).all()
            
            # 构造步骤状态列表
            steps_status = []
            for step in steps:
                steps_status.append({
                    "step_number": step.step_number,
                    "step_name": step.step_name,
                    "step_description": step.step_description,
                    "status": step.status.value if step.status else "pending",
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "created_at": step.created_at.isoformat() if step.created_at else None,
                    "error_message": step.error_message,
                    "command": step.command,
                    "expected_output": step.expected_output,
                    "actual_output": step.actual_output
                })
            
            logger.info(f"获取到 {len(steps_status)} 个步骤状态")
            return True, steps_status, ""
            
        except Exception as e:
            logger.error(f"获取步骤状态失败: {str(e)}")
            return False, [], f"获取步骤状态失败: {str(e)}"

# 创建全局服务实例
guided_deployment_service = GuidedDeploymentService()
