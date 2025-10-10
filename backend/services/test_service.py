import os
import docker
import tempfile
import shutil
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from models import Task, TaskLog, TaskStatus
import logging
import time
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEnvironmentService:
    """测试环境部署服务"""
    
    def __init__(self):
        """初始化测试服务"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except Exception as e:
            logger.error(f"Docker客户端初始化失败：{str(e)}")
            self.docker_client = None
    
    async def deploy_to_test_environment(
        self, 
        task: Task, 
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """部署到测试环境
        
        Args:
            task: 任务对象
            db: 数据库会话
            
        Returns:
            Tuple[success, test_url, error_message]
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.TESTING
            self._add_task_log(task.id, TaskStatus.TESTING, "开始部署测试环境", db)
            db.commit()
            
            # 检查Docker是否可用
            if not self.docker_client:
                error_msg = "Docker服务不可用"
                self._add_task_log(task.id, task.status, error_msg, db)
                db.commit()
                return False, None, error_msg
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix=f"task_{task.id}_")
            
            try:
                # 准备测试代码
                self._prepare_test_code(task, temp_dir)
                
                # 构建Docker镜像
                image_name = f"test-task-{task.id}"
                success = self._build_docker_image(temp_dir, image_name, task.id, db)
                
                if not success:
                    return False, None, "Docker镜像构建失败"
                
                # 运行容器
                container_port = 8000 + task.id  # 避免端口冲突
                container = self._run_container(image_name, container_port, task.id, db)
                
                if not container:
                    return False, None, "容器启动失败"
                
                # 等待服务启动
                test_url = f"http://localhost:{container_port}"
                if self._wait_for_service(test_url, task.id, db):
                    # 更新任务状态
                    task.status = TaskStatus.TEST_COMPLETED
                    task.test_url = test_url
                    
                    self._add_task_log(
                        task.id, 
                        TaskStatus.TEST_COMPLETED, 
                        f"测试环境部署成功，访问地址：{test_url}", 
                        db
                    )
                    db.commit()
                    
                    logger.info(f"任务 {task.id} 测试环境部署成功：{test_url}")
                    return True, test_url, None
                else:
                    error_msg = "服务启动超时"
                    self._add_task_log(task.id, task.status, error_msg, db)
                    db.commit()
                    return False, None, error_msg
                    
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            error_msg = f"测试环境部署异常：{str(e)}"
            logger.error(error_msg)
            self._add_task_log(task.id, task.status, error_msg, db)
            db.commit()
            return False, None, error_msg
    
    def _prepare_test_code(self, task: Task, temp_dir: str):
        """准备测试代码"""
        # 创建main.py文件
        main_py_content = f"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="测试API - 任务{task.id}",
    description="{task.title}",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 生成的代码
{task.generated_code or '# 暂无生成代码'}

@app.get("/")
async def root():
    return {{
        "message": "测试API运行中",
        "task_id": {task.id},
        "task_title": "{task.title}"
    }}

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        
        with open(os.path.join(temp_dir, "main.py"), "w", encoding="utf-8") as f:
            f.write(main_py_content)
        
        # 创建requirements.txt
        requirements_content = """
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
"""
        
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write(requirements_content)
        
        # 创建Dockerfile
        dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["python", "main.py"]
"""
        
        with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile_content)
    
    def _build_docker_image(self, temp_dir: str, image_name: str, task_id: int, db: Session) -> bool:
        """构建Docker镜像"""
        try:
            self._add_task_log(task_id, TaskStatus.TESTING, "开始构建Docker镜像", db)
            db.commit()
            
            # 构建镜像
            image, logs = self.docker_client.images.build(
                path=temp_dir,
                tag=image_name,
                rm=True
            )
            
            self._add_task_log(task_id, TaskStatus.TESTING, "Docker镜像构建完成", db)
            db.commit()
            
            logger.info(f"任务 {task_id} Docker镜像构建成功：{image_name}")
            return True
            
        except Exception as e:
            error_msg = f"Docker镜像构建失败：{str(e)}"
            logger.error(error_msg)
            self._add_task_log(task_id, TaskStatus.TESTING, error_msg, db)
            db.commit()
            return False
    
    def _run_container(self, image_name: str, port: int, task_id: int, db: Session):
        """运行Docker容器"""
        try:
            self._add_task_log(task_id, TaskStatus.TESTING, f"启动容器，端口：{port}", db)
            db.commit()
            
            # 停止可能存在的同名容器
            container_name = f"test-task-{task_id}"
            try:
                existing_container = self.docker_client.containers.get(container_name)
                existing_container.stop()
                existing_container.remove()
            except docker.errors.NotFound:
                pass
            
            # 运行新容器
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                ports={'8000/tcp': port},
                detach=True,
                remove=True
            )
            
            self._add_task_log(task_id, TaskStatus.TESTING, "容器启动成功", db)
            db.commit()
            
            logger.info(f"任务 {task_id} 容器启动成功：{container.id}")
            return container
            
        except Exception as e:
            error_msg = f"容器启动失败：{str(e)}"
            logger.error(error_msg)
            self._add_task_log(task_id, TaskStatus.TESTING, error_msg, db)
            db.commit()
            return None
    
    def _wait_for_service(self, test_url: str, task_id: int, db: Session, timeout: int = 60) -> bool:
        """等待服务启动"""
        self._add_task_log(task_id, TaskStatus.TESTING, "等待服务启动", db)
        db.commit()
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{test_url}/health", timeout=5)
                if response.status_code == 200:
                    self._add_task_log(task_id, TaskStatus.TESTING, "服务健康检查通过", db)
                    db.commit()
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        return False
    
    def cleanup_test_environment(self, task_id: int):
        """清理测试环境"""
        try:
            if self.docker_client:
                container_name = f"test-task-{task_id}"
                image_name = f"test-task-{task_id}"
                
                # 停止并删除容器
                try:
                    container = self.docker_client.containers.get(container_name)
                    container.stop()
                    container.remove()
                    logger.info(f"任务 {task_id} 容器已清理")
                except docker.errors.NotFound:
                    pass
                
                # 删除镜像
                try:
                    self.docker_client.images.remove(image_name)
                    logger.info(f"任务 {task_id} 镜像已清理")
                except docker.errors.ImageNotFound:
                    pass
                    
        except Exception as e:
            logger.error(f"清理测试环境失败：{str(e)}")
    
    def _add_task_log(self, task_id: int, status: TaskStatus, message: str, db: Session):
        """添加任务日志"""
        task_log = TaskLog(
            task_id=task_id,
            action_type="test_execution",
            status=status.value,
            message=message
        )
        db.add(task_log)

# 创建全局测试服务实例
test_service = TestEnvironmentService()