import asyncio
import paramiko
import io
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class SSHManager:
    """SSH连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, Dict] = {}
        self.connection_timeout = 3600  # 1小时超时
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._lock = threading.Lock()
    
    def _generate_connection_id(self, host: str, port: int, username: str) -> str:
        """生成连接ID"""
        return f"{username}@{host}:{port}"
    
    def _create_connection_sync(
        self, 
        host: str, 
        port: int, 
        username: str, 
        password: str = None, 
        key_path: str = None,
        key_content: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        同步创建SSH连接
        
        Returns:
            Tuple[success, connection_id, error_message]
        """
        connection_id = self._generate_connection_id(host, port, username)
        
        try:
            # 创建SSH客户端
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': 30,
                'banner_timeout': 30
            }
            
            # 认证方式
            if password:
                connect_kwargs['password'] = password
            elif key_path:
                connect_kwargs['key_filename'] = key_path
            elif key_content:
                # 从字符串创建私钥
                key_file = io.StringIO(key_content)
                try:
                    private_key = paramiko.RSAKey.from_private_key(key_file)
                    connect_kwargs['pkey'] = private_key
                except paramiko.ssh_exception.PasswordRequiredException:
                    return False, "", "私钥需要密码，请提供密码"
                except Exception as e:
                    return False, "", f"私钥格式错误: {str(e)}"
            else:
                return False, "", "请提供密码或SSH密钥"
            
            # 建立连接
            ssh_client.connect(**connect_kwargs)
            
            # 测试连接
            stdin, stdout, stderr = ssh_client.exec_command('echo "Connection test"')
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                ssh_client.close()
                return False, "", f"连接测试失败: {error}"
            
            # 存储连接信息
            with self._lock:
                self.connections[connection_id] = {
                    'client': ssh_client,
                    'host': host,
                    'port': port,
                    'username': username,
                    'created_at': datetime.now(),
                    'last_used': datetime.now()
                }
            
            logger.info(f"SSH连接创建成功: {connection_id}")
            return True, connection_id, None
            
        except paramiko.AuthenticationException:
            return False, "", "认证失败，请检查用户名、密码或密钥"
        except paramiko.SSHException as e:
            return False, "", f"SSH连接错误: {str(e)}"
        except Exception as e:
            return False, "", f"连接失败: {str(e)}"
    
    async def create_connection(
        self, 
        host: str, 
        port: int, 
        username: str, 
        password: str = None, 
        key_path: str = None,
        key_content: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        异步创建SSH连接
        
        Returns:
            Tuple[success, connection_id, error_message]
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_connection_sync,
            host, port, username, password, key_path, key_content
        )
    
    async def execute_command(
        self, 
        connection_id: str, 
        command: str,
        timeout: int = 30
    ) -> Tuple[bool, str, str]:
        """
        执行命令
        
        Returns:
            Tuple[success, stdout, stderr]
        """
        if connection_id not in self.connections:
            return False, "", "连接不存在"
        
        try:
            connection = self.connections[connection_id]
            ssh_client = connection['client']
            
            # 更新最后使用时间
            connection['last_used'] = datetime.now()
            
            # 执行命令
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            
            # 读取输出
            stdout_content = stdout.read().decode('utf-8', errors='ignore')
            stderr_content = stderr.read().decode('utf-8', errors='ignore')
            
            # 获取退出码
            exit_status = stdout.channel.recv_exit_status()
            
            logger.info(f"命令执行完成 [{connection_id}]: {command} (退出码: {exit_status})")
            
            return exit_status == 0, stdout_content, stderr_content
            
        except Exception as e:
            logger.error(f"命令执行失败 [{connection_id}]: {str(e)}")
            return False, "", f"命令执行失败: {str(e)}"
    
    async def upload_file(
        self, 
        connection_id: str, 
        file_content: str, 
        remote_path: str
    ) -> Tuple[bool, str]:
        """
        上传文件
        
        Returns:
            Tuple[success, error_message]
        """
        if connection_id not in self.connections:
            return False, "连接不存在"
        
        try:
            connection = self.connections[connection_id]
            ssh_client = connection['client']
            
            # 更新最后使用时间
            connection['last_used'] = datetime.now()
            
            # 创建SFTP客户端
            sftp = ssh_client.open_sftp()
            
            # 确保目录存在
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            if remote_dir:
                try:
                    sftp.makedirs(remote_dir)
                except Exception:
                    pass  # 目录可能已存在
            
            # 写入文件
            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(file_content)
            
            sftp.close()
            logger.info(f"文件上传成功 [{connection_id}]: {remote_path}")
            return True, ""
            
        except Exception as e:
            logger.error(f"文件上传失败 [{connection_id}]: {str(e)}")
            return False, f"文件上传失败: {str(e)}"
    
    async def download_file(
        self, 
        connection_id: str, 
        remote_path: str
    ) -> Tuple[bool, str, str]:
        """
        下载文件
        
        Returns:
            Tuple[success, file_content, error_message]
        """
        if connection_id not in self.connections:
            return False, "", "连接不存在"
        
        try:
            connection = self.connections[connection_id]
            ssh_client = connection['client']
            
            # 更新最后使用时间
            connection['last_used'] = datetime.now()
            
            # 创建SFTP客户端
            sftp = ssh_client.open_sftp()
            
            # 读取文件
            with sftp.file(remote_path, 'r') as remote_file:
                content = remote_file.read()
            
            sftp.close()
            logger.info(f"文件下载成功 [{connection_id}]: {remote_path}")
            return True, content, ""
            
        except Exception as e:
            logger.error(f"文件下载失败 [{connection_id}]: {str(e)}")
            return False, "", f"文件下载失败: {str(e)}"
    
    def check_connection(self, connection_id: str) -> bool:
        """检查连接是否有效"""
        if connection_id not in self.connections:
            return False
        
        try:
            connection = self.connections[connection_id]
            ssh_client = connection['client']
            
            # 简单的连接测试
            transport = ssh_client.get_transport()
            return transport is not None and transport.is_active()
            
        except Exception:
            return False
    
    def close_connection(self, connection_id: str) -> bool:
        """关闭连接"""
        if connection_id not in self.connections:
            return False
        
        try:
            connection = self.connections[connection_id]
            ssh_client = connection['client']
            ssh_client.close()
            
            del self.connections[connection_id]
            logger.info(f"SSH连接已关闭: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"关闭连接失败: {str(e)}")
            return False
    
    def cleanup_expired_connections(self):
        """清理过期的连接"""
        now = datetime.now()
        expired_connections = []
        
        for connection_id, connection in self.connections.items():
            if (now - connection['last_used']).total_seconds() > self.connection_timeout:
                expired_connections.append(connection_id)
        
        for connection_id in expired_connections:
            self.close_connection(connection_id)
        
        if expired_connections:
            logger.info(f"清理了 {len(expired_connections)} 个过期连接")
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """获取连接信息"""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        return {
            'connection_id': connection_id,
            'host': connection['host'],
            'port': connection['port'],
            'username': connection['username'],
            'created_at': connection['created_at'],
            'last_used': connection['last_used'],
            'is_active': self.check_connection(connection_id)
        }
    
    def list_connections(self) -> List[Dict]:
        """列出所有连接"""
        return [self.get_connection_info(conn_id) for conn_id in self.connections.keys()]

# 创建全局SSH管理器实例
ssh_manager = SSHManager()
