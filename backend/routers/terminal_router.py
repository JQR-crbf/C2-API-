from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
import logging
import asyncio
from datetime import datetime

from database import get_db
from models import User
from auth_utils import verify_token
from services.terminal_service import get_terminal_manager, TerminalSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/terminal", tags=["终端"])
security = HTTPBearer()

# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection {connection_id} established")
    
    def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 清理会话连接映射
        session_to_remove = None
        for session_id, conn_id in self.session_connections.items():
            if conn_id == connection_id:
                session_to_remove = session_id
                break
        
        if session_to_remove:
            del self.session_connections[session_to_remove]
        
        logger.info(f"WebSocket connection {connection_id} disconnected")
    
    async def send_message(self, connection_id: str, message: dict):
        """发送消息到指定连接"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    def bind_session(self, session_id: str, connection_id: str):
        """绑定会话和连接"""
        self.session_connections[session_id] = connection_id
    
    def get_connection_by_session(self, session_id: str) -> Optional[str]:
        """根据会话ID获取连接ID"""
        return self.session_connections.get(session_id)

# 全局连接管理器
connection_manager = ConnectionManager()


async def verify_websocket_token(token: str, db: Session) -> User:
    """验证WebSocket连接的JWT token"""
    try:
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.websocket("/ws/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """终端WebSocket连接端点"""
    connection_id = f"{session_id}_{datetime.now().timestamp()}"
    
    try:
        # 验证token
        db = next(get_db())
        user = await verify_websocket_token(token, db)
        
        # 建立WebSocket连接
        await connection_manager.connect(websocket, connection_id)
        
        # 获取终端管理器
        terminal_manager = get_terminal_manager()
        
        # 获取或创建终端会话
        session = terminal_manager.get_session(session_id)
        if session is None:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Terminal session not found"
            }))
            return
        
        # 验证会话所有权
        if session.user_id != user.id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Access denied: session belongs to another user"
            }))
            return
        
        # 绑定会话和连接
        connection_manager.bind_session(session_id, connection_id)
        
        # 设置输出回调
        async def output_callback(data: str):
            await connection_manager.send_message(connection_id, {
                "type": "output",
                "data": data
            })
        
        # 如果会话未启动，启动它
        if not session.is_active:
            session.start(lambda data: asyncio.create_task(output_callback(data)))
        else:
            # 更新输出回调
            session.output_callback = lambda data: asyncio.create_task(output_callback(data))
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connected",
            "session_id": session_id,
            "message": "Terminal connected successfully"
        }))
        
        # 处理WebSocket消息
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "input":
                    # 处理用户输入
                    input_data = message.get("data", "")
                    session.write(input_data)
                
                elif message_type == "resize":
                    # 处理终端大小调整
                    rows = message.get("rows", 24)
                    cols = message.get("cols", 80)
                    session.resize(rows, cols)
                
                elif message_type == "ping":
                    # 处理心跳
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from WebSocket")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except HTTPException as e:
        logger.error(f"Authentication failed for WebSocket: {e.detail}")
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        connection_manager.disconnect(connection_id)


@router.post("/sessions", summary="创建终端会话")
async def create_terminal_session(
    shell: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """创建新的终端会话"""
    # 验证用户身份
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        current_user = db.query(User).filter(User.id == int(user_id)).first()
        if current_user is None or not current_user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    try:
        terminal_manager = get_terminal_manager()
        session_id = terminal_manager.create_session(current_user.id, shell)
        
        return {
            "session_id": session_id,
            "message": "Terminal session created successfully",
            "websocket_url": f"/terminal/ws/{session_id}"
        }
    except Exception as e:
        logger.error(f"Failed to create terminal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", summary="获取用户的终端会话列表")
async def list_terminal_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有终端会话"""
    from routers.auth import get_current_user
    
    current_user = await get_current_user(credentials, db)
    
    try:
        terminal_manager = get_terminal_manager()
        sessions = terminal_manager.get_user_sessions(current_user.id)
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.session_id,
                "shell": session.shell,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "is_active": session.is_alive(),
                "age": session.get_age(),
                "idle_time": session.get_idle_time()
            })
        
        return {
            "sessions": session_list,
            "total": len(session_list)
        }
    except Exception as e:
        logger.error(f"Failed to list terminal sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", summary="删除终端会话")
async def delete_terminal_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """删除指定的终端会话"""
    from routers.auth import get_current_user
    
    current_user = await get_current_user(credentials, db)
    
    try:
        terminal_manager = get_terminal_manager()
        session = terminal_manager.get_session(session_id)
        
        if session is None:
            raise HTTPException(status_code=404, detail="Terminal session not found")
        
        # 验证会话所有权
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 删除会话
        terminal_manager.remove_session(session_id)
        
        return {
            "message": "Terminal session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete terminal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="获取终端统计信息")
async def get_terminal_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取终端系统统计信息（仅管理员）"""
    from routers.auth import get_current_user
    
    current_user = await get_current_user(credentials, db)
    
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        terminal_manager = get_terminal_manager()
        stats = terminal_manager.get_session_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get terminal stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))