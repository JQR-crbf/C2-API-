from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
import asyncio
import json
from typing import Dict, List

from database import get_db, engine, Base
from models import User
from auth_utils import verify_token, decode_token

# 创建数据库表
Base.metadata.create_all(bind=engine)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"用户 {user_id} WebSocket连接已建立")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"用户 {user_id} WebSocket连接已断开")
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"发送消息给用户 {user_id} 失败: {e}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"广播消息给用户 {user_id} 失败: {e}")
                disconnected_users.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)

manager = ConnectionManager()

app = FastAPI(
    title="AI API开发自动化平台",
    description="通过自然语言描述自动生成API接口的智能平台",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 删除重复的认证函数定义，使用routers.auth中的版本

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 路由注册
from routers import auth, tasks, admin, notifications, testing
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(testing.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AI API开发自动化平台后端服务"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-api-platform-backend"}

# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    try:
        # 验证token并获取用户信息
        payload = decode_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            await websocket.close(code=4002, reason="Invalid token")
            return
        
        # 建立连接
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # 保持连接活跃，接收客户端心跳
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
        except WebSocketDisconnect:
            manager.disconnect(user_id)
            
    except Exception as e:
        print(f"WebSocket连接错误: {e}")
        await websocket.close(code=4003, reason="Connection error")

# 全局消息发送函数
async def send_realtime_notification(user_id: int, notification_type: str, data: dict):
    """发送实时通知"""
    message = {
        "type": notification_type,
        "data": data,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.send_personal_message(message, user_id)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    from services.task_processor import start_task_processor
    # 在后台启动任务处理器
    asyncio.create_task(start_task_processor())
    print("后台任务处理器已启动")
    print("WebSocket服务已启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的事件处理"""
    from services.task_processor import stop_task_processor
    stop_task_processor()
    print("后台任务处理器已停止")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)