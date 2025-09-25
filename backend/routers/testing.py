from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from database import get_db
from models import User
from schemas import MessageResponse
from routers.auth import get_current_user
import requests
import time
import json
from pydantic import BaseModel

router = APIRouter(prefix="/testing", tags=["API测试"])

class APITestRequest(BaseModel):
    """API测试请求模型"""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None

class APITestResponse(BaseModel):
    """API测试响应模型"""
    status: int
    statusText: str
    headers: Dict[str, str]
    data: Any
    responseTime: int
    success: bool

@router.post("/api", response_model=APITestResponse, summary="执行API测试")
async def test_api(
    test_request: APITestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行API测试请求"""
    start_time = time.time()
    
    try:
        # 准备请求参数
        request_kwargs = {
            'method': test_request.method.upper(),
            'url': test_request.url,
            'timeout': 30  # 30秒超时
        }
        
        # 添加headers
        if test_request.headers:
            request_kwargs['headers'] = test_request.headers
        
        # 添加请求体（仅对POST、PUT、PATCH方法）
        if test_request.method.upper() in ['POST', 'PUT', 'PATCH'] and test_request.body:
            try:
                # 尝试解析JSON
                json_data = json.loads(test_request.body)
                request_kwargs['json'] = json_data
            except json.JSONDecodeError:
                # 如果不是JSON，作为文本发送
                request_kwargs['data'] = test_request.body
                if 'headers' not in request_kwargs:
                    request_kwargs['headers'] = {}
                request_kwargs['headers']['Content-Type'] = 'text/plain'
        
        # 发送请求
        response = requests.request(**request_kwargs)
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)
        
        # 尝试解析响应数据
        try:
            response_data = response.json()
        except (json.JSONDecodeError, ValueError):
            response_data = response.text
        
        # 构建响应
        return APITestResponse(
            status=response.status_code,
            statusText=response.reason or 'Unknown',
            headers=dict(response.headers),
            data=response_data,
            responseTime=response_time,
            success=200 <= response.status_code < 300
        )
        
    except requests.exceptions.Timeout:
        response_time = int((time.time() - start_time) * 1000)
        return APITestResponse(
            status=408,
            statusText='Request Timeout',
            headers={},
            data={'error': '请求超时'},
            responseTime=response_time,
            success=False
        )
        
    except requests.exceptions.ConnectionError:
        response_time = int((time.time() - start_time) * 1000)
        return APITestResponse(
            status=0,
            statusText='Connection Error',
            headers={},
            data={'error': '连接失败，请检查URL是否正确'},
            responseTime=response_time,
            success=False
        )
        
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        return APITestResponse(
            status=500,
            statusText='Internal Error',
            headers={},
            data={'error': f'测试执行失败: {str(e)}'},
            responseTime=response_time,
            success=False
        )

@router.get("/endpoints", summary="获取可用的测试端点")
async def get_test_endpoints(
    current_user: User = Depends(get_current_user)
):
    """获取可用的测试端点列表"""
    endpoints = [
        {
            'name': '用户认证测试',
            'method': 'POST',
            'url': 'http://localhost:8080/api/auth/login',
            'description': '测试用户登录功能',
            'sample_body': {
                'username': 'admin',
                'password': 'admin123'
            }
        },
        {
            'name': '获取当前用户信息',
            'method': 'GET',
            'url': 'http://localhost:8080/api/auth/me',
            'description': '获取当前登录用户的信息',
            'headers': {
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            }
        },
        {
            'name': '获取任务列表',
            'method': 'GET',
            'url': 'http://localhost:8080/api/tasks',
            'description': '获取用户的任务列表',
            'headers': {
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            }
        },
        {
            'name': '健康检查',
            'method': 'GET',
            'url': 'http://localhost:8080/health',
            'description': '检查后端服务状态'
        }
    ]
    
    return {'endpoints': endpoints}

@router.get("/sample-data", summary="获取示例测试数据")
async def get_sample_test_data(
    current_user: User = Depends(get_current_user)
):
    """获取示例测试数据"""
    return {
        'login_request': {
            'username': 'admin',
            'password': 'admin123'
        },
        'user_registration': {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'full_name': '测试用户'
        },
        'task_creation': {
            'title': '用户管理API',
            'description': '创建用户管理相关的API接口',
            'input_params': {
                'username': 'string',
                'email': 'string',
                'password': 'string'
            },
            'output_params': {
                'user_id': 'integer',
                'message': 'string',
                'status': 'string'
            }
        }
    }