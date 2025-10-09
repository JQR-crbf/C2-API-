import asyncio
import os
import subprocess
import psutil
import threading
import time
from typing import Dict, Optional, Callable
from uuid import uuid4
import logging
import queue

logger = logging.getLogger(__name__)

class TerminalSession:
    """终端会话类，管理单个终端进程（Windows兼容版本）"""
    
    def __init__(self, session_id: str, user_id: int, shell: str = None):
        self.session_id = session_id
        self.user_id = user_id
        self.shell = shell or self._get_default_shell()
        self.process: Optional[subprocess.Popen] = None
        self.created_at = time.time()
        self.last_activity = time.time()
        self.is_active = False
        self.output_callback: Optional[Callable] = None
        self._read_thread: Optional[threading.Thread] = None
        self._stop_reading = False
        self._input_queue = queue.Queue()
        self._write_thread: Optional[threading.Thread] = None
        
    def _get_default_shell(self) -> str:
        """获取默认shell"""
        if os.name == 'nt':  # Windows
            return 'powershell.exe'
        else:  # Unix-like
            return os.environ.get('SHELL', '/bin/bash')
    
    def start(self, output_callback: Callable[[str], None]):
        """启动终端会话"""
        try:
            self.output_callback = output_callback
            
            # 启动进程
            if os.name == 'nt':  # Windows
                # Windows下使用PowerShell
                self.process = subprocess.Popen(
                    [self.shell, '-NoLogo', '-NoExit'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:  # Unix-like
                self.process = subprocess.Popen(
                    [self.shell],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0
                )
            
            self.is_active = True
            self.last_activity = time.time()
            
            # 启动读取和写入线程
            self._start_reading_thread()
            self._start_writing_thread()
            
            logger.info(f"Terminal session {self.session_id} started for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to start terminal session {self.session_id}: {e}")
            raise
    
    def _start_reading_thread(self):
        """启动读取输出的线程"""
        self._stop_reading = False
        self._read_thread = threading.Thread(target=self._read_output, daemon=True)
        self._read_thread.start()
    
    def _start_writing_thread(self):
        """启动写入输入的线程"""
        self._write_thread = threading.Thread(target=self._write_input, daemon=True)
        self._write_thread.start()
    
    def _read_output(self):
        """读取进程输出"""
        try:
            while not self._stop_reading and self.process and self.process.poll() is None:
                try:
                    # 读取输出
                    if self.process.stdout:
                        output = self.process.stdout.read(1024)
                        if output:
                            self.last_activity = time.time()
                            if self.output_callback:
                                self.output_callback(output)
                except Exception as e:
                    if not self._stop_reading:
                        logger.error(f"Error reading from process: {e}")
                    break
                    
                time.sleep(0.01)  # 避免CPU占用过高
                
        except Exception as e:
            logger.error(f"Terminal reading thread error: {e}")
        finally:
            self.is_active = False
    
    def _write_input(self):
        """写入输入的线程"""
        try:
            while not self._stop_reading and self.process and self.process.poll() is None:
                try:
                    # 从队列获取输入
                    data = self._input_queue.get(timeout=0.1)
                    if data and self.process.stdin:
                        self.process.stdin.write(data)
                        self.process.stdin.flush()
                        self.last_activity = time.time()
                except queue.Empty:
                    continue
                except Exception as e:
                    if not self._stop_reading:
                        logger.error(f"Error writing to process: {e}")
                    break
        except Exception as e:
            logger.error(f"Terminal writing thread error: {e}")
    
    def write(self, data: str):
        """向终端写入数据"""
        if self.pty_process and self.pty_process.isalive():
            try:
                self.pty_process.write(data.encode('utf-8'))
                self.last_activity = time.time()
            except Exception as e:
                logger.error(f"Error writing to terminal: {e}")
                raise
        else:
            raise Exception("Terminal process is not active")
    
    def resize(self, rows: int, cols: int):
        """调整终端大小"""
        if self.pty_process and self.pty_process.isalive():
            try:
                self.pty_process.setwinsize(rows, cols)
            except Exception as e:
                logger.error(f"Error resizing terminal: {e}")
    
    def terminate(self):
        """终止终端会话"""
        try:
            self._stop_reading = True
            
            if self.pty_process and self.pty_process.isalive():
                # 尝试优雅关闭
                try:
                    if os.name == 'nt':
                        # Windows下终止进程
                        self.pty_process.terminate()
                    else:
                        # Unix-like系统发送SIGTERM
                        self.pty_process.kill(signal.SIGTERM)
                    
                    # 等待进程结束
                    for _ in range(50):  # 最多等待5秒
                        if not self.pty_process.isalive():
                            break
                        time.sleep(0.1)
                    
                    # 如果还没结束，强制杀死
                    if self.pty_process.isalive():
                        if os.name == 'nt':
                            self.pty_process.kill()
                        else:
                            self.pty_process.kill(signal.SIGKILL)
                            
                except Exception as e:
                    logger.error(f"Error terminating PTY process: {e}")
            
            # 等待读取线程结束
            if self._read_thread and self._read_thread.is_alive():
                self._read_thread.join(timeout=2)
            
            self.is_active = False
            logger.info(f"Terminal session {self.session_id} terminated")
            
        except Exception as e:
            logger.error(f"Error during terminal termination: {e}")
    
    def is_alive(self) -> bool:
        """检查终端是否还活着"""
        return self.pty_process and self.pty_process.isalive() and self.is_active
    
    def get_age(self) -> float:
        """获取会话年龄（秒）"""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """获取空闲时间（秒）"""
        return time.time() - self.last_activity


class TerminalManager:
    """终端管理器，管理所有终端会话"""
    
    def __init__(self, max_sessions: int = 50, session_timeout: int = 3600):
        self.sessions: Dict[str, TerminalSession] = {}
        self.user_sessions: Dict[int, set] = {}  # 用户ID -> 会话ID集合
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout  # 会话超时时间（秒）
        self._cleanup_thread = None
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_loop():
            while True:
                try:
                    self.cleanup_expired_sessions()
                    time.sleep(60)  # 每分钟检查一次
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def create_session(self, user_id: int, shell: str = None) -> str:
        """创建新的终端会话"""
        # 检查会话数量限制
        if len(self.sessions) >= self.max_sessions:
            # 清理过期会话
            self.cleanup_expired_sessions()
            
            # 如果还是超过限制，拒绝创建
            if len(self.sessions) >= self.max_sessions:
                raise Exception("Maximum number of terminal sessions reached")
        
        # 检查用户会话数量（每个用户最多5个会话）
        user_session_count = len(self.user_sessions.get(user_id, set()))
        if user_session_count >= 5:
            raise Exception("Maximum number of sessions per user reached")
        
        # 创建新会话
        session_id = str(uuid4())
        session = TerminalSession(session_id, user_id, shell)
        
        self.sessions[session_id] = session
        
        # 更新用户会话映射
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"Created terminal session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """获取终端会话"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """移除终端会话"""
        session = self.sessions.get(session_id)
        if session:
            # 终止会话
            session.terminate()
            
            # 从映射中移除
            del self.sessions[session_id]
            
            # 从用户会话映射中移除
            user_sessions = self.user_sessions.get(session.user_id, set())
            user_sessions.discard(session_id)
            if not user_sessions:
                del self.user_sessions[session.user_id]
            
            logger.info(f"Removed terminal session {session_id}")
    
    def cleanup_expired_sessions(self):
        """清理过期的会话"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            # 检查会话是否过期或已死亡
            if (not session.is_alive() or 
                session.get_idle_time() > self.session_timeout or
                session.get_age() > self.session_timeout * 2):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired terminal sessions")
    
    def get_user_sessions(self, user_id: int) -> list:
        """获取用户的所有会话"""
        user_session_ids = self.user_sessions.get(user_id, set())
        return [self.sessions[sid] for sid in user_session_ids if sid in self.sessions]
    
    def get_session_stats(self) -> dict:
        """获取会话统计信息"""
        active_sessions = sum(1 for s in self.sessions.values() if s.is_alive())
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_sessions,
            'inactive_sessions': len(self.sessions) - active_sessions,
            'users_with_sessions': len(self.user_sessions),
            'max_sessions': self.max_sessions
        }
    
    def shutdown(self):
        """关闭所有会话"""
        logger.info("Shutting down terminal manager...")
        
        # 终止所有会话
        for session_id in list(self.sessions.keys()):
            self.remove_session(session_id)
        
        logger.info("Terminal manager shutdown complete")


# 全局终端管理器实例
terminal_manager = TerminalManager()


def get_terminal_manager() -> TerminalManager:
    """获取终端管理器实例"""
    return terminal_manager