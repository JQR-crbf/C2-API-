from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from database import get_db
from models import Task, User
from routers.auth import get_current_user
from services.automated_test_service import AutomatedTestService

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/test", tags=["automated-testing"])

# 请求模型
class SyntaxCheckRequest(BaseModel):
    """语法检查请求模型"""
    code: str
    filename: Optional[str] = "temp.py"

class UnitTestRequest(BaseModel):
    """单元测试请求模型"""
    test_code: str
    main_code: str
    test_filename: Optional[str] = "test_generated.py"

class APITestEndpoint(BaseModel):
    """API测试接口模型"""
    path: str
    method: str = "GET"
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    expected_status: int = 200

class APITestRequest(BaseModel):
    """API测试请求模型"""
    base_url: str
    endpoints: List[APITestEndpoint]
    auth_token: Optional[str] = None

class PerformanceTestRequest(BaseModel):
    """性能测试请求模型"""
    base_url: str
    endpoint: str
    concurrent_users: int = 10
    duration_seconds: int = 30
    auth_token: Optional[str] = None

class FullTestRequest(BaseModel):
    """完整测试请求模型"""
    task_id: int
    code: str
    test_code: Optional[str] = None
    api_tests: Optional[APITestRequest] = None
    performance_test: Optional[PerformanceTestRequest] = None

# 响应模型
class SyntaxCheckResponse(BaseModel):
    """语法检查响应模型"""
    success: bool
    warnings: List[str]
    error: Optional[str] = None
    filename: str
    checked_at: str

class TestResult(BaseModel):
    """测试结果模型"""
    name: str
    outcome: str
    duration: float
    message: str

class UnitTestResponse(BaseModel):
    """单元测试响应模型"""
    success: bool
    results: Dict[str, Any]
    error: Optional[str] = None
    test_filename: str
    executed_at: str

class APITestResponse(BaseModel):
    """API测试响应模型"""
    success: bool
    results: Dict[str, Any]
    error: Optional[str] = None
    tested_at: str

class PerformanceTestResponse(BaseModel):
    """性能测试响应模型"""
    success: bool
    results: Dict[str, Any]
    error: Optional[str] = None
    tested_at: str

class TestReportResponse(BaseModel):
    """测试报告响应模型"""
    task_id: int
    overall_success: bool
    summary: Dict[str, Any]
    details: Dict[str, Any]
    recommendations: List[str]
    generated_at: str

# 初始化测试服务
test_service = AutomatedTestService()

@router.post("/syntax-check", response_model=SyntaxCheckResponse)
async def check_syntax(
    request: SyntaxCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """检查Python代码语法
    
    Args:
        request: 语法检查请求
        current_user: 当前用户
        
    Returns:
        语法检查结果
    """
    try:
        logger.info(f"用户 {current_user.username} 请求语法检查: {request.filename}")
        
        success, warnings, error = await test_service.check_python_syntax(
            request.code, request.filename
        )
        
        return SyntaxCheckResponse(
            success=success,
            warnings=warnings,
            error=error,
            filename=request.filename,
            checked_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"语法检查异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"语法检查失败: {str(e)}")

@router.post("/unit-test", response_model=UnitTestResponse)
async def run_unit_test(
    request: UnitTestRequest,
    current_user: User = Depends(get_current_user)
):
    """运行单元测试
    
    Args:
        request: 单元测试请求
        current_user: 当前用户
        
    Returns:
        单元测试结果
    """
    try:
        logger.info(f"用户 {current_user.username} 请求单元测试: {request.test_filename}")
        
        success, results, error = await test_service.run_unit_tests(
            request.test_code, request.main_code, request.test_filename
        )
        
        return UnitTestResponse(
            success=success,
            results=results,
            error=error,
            test_filename=request.test_filename,
            executed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"单元测试异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"单元测试失败: {str(e)}")

@router.post("/api-test", response_model=APITestResponse)
async def run_api_test(
    request: APITestRequest,
    current_user: User = Depends(get_current_user)
):
    """运行API接口测试
    
    Args:
        request: API测试请求
        current_user: 当前用户
        
    Returns:
        API测试结果
    """
    try:
        logger.info(f"用户 {current_user.username} 请求API测试: {request.base_url}")
        
        # 转换接口列表为字典格式
        endpoints = []
        for endpoint in request.endpoints:
            endpoints.append({
                'path': endpoint.path,
                'method': endpoint.method,
                'data': endpoint.data,
                'params': endpoint.params,
                'expected_status': endpoint.expected_status
            })
        
        success, results, error = await test_service.test_api_endpoints(
            request.base_url, endpoints, request.auth_token
        )
        
        return APITestResponse(
            success=success,
            results=results,
            error=error,
            tested_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"API测试异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API测试失败: {str(e)}")

@router.post("/performance-test", response_model=PerformanceTestResponse)
async def run_performance_test(
    request: PerformanceTestRequest,
    current_user: User = Depends(get_current_user)
):
    """运行性能测试
    
    Args:
        request: 性能测试请求
        current_user: 当前用户
        
    Returns:
        性能测试结果
    """
    try:
        logger.info(f"用户 {current_user.username} 请求性能测试: {request.base_url}{request.endpoint}")
        
        success, results, error = await test_service.run_performance_test(
            request.base_url,
            request.endpoint,
            request.concurrent_users,
            request.duration_seconds,
            request.auth_token
        )
        
        return PerformanceTestResponse(
            success=success,
            results=results,
            error=error,
            tested_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"性能测试异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"性能测试失败: {str(e)}")

@router.post("/full-test", response_model=TestReportResponse)
async def run_full_test(
    request: FullTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行完整的自动化测试
    
    Args:
        request: 完整测试请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        完整测试报告
    """
    try:
        logger.info(f"用户 {current_user.username} 请求完整测试，任务ID: {request.task_id}")
        
        # 验证任务存在且属于当前用户
        task = db.query(Task).filter(
            Task.id == request.task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
        
        # 运行语法检查
        syntax_result = await test_service.check_python_syntax(
            request.code, f"task_{request.task_id}.py"
        )
        
        # 运行单元测试（如果提供了测试代码）
        unit_test_result = (True, {}, None)
        if request.test_code:
            unit_test_result = await test_service.run_unit_tests(
                request.test_code, request.code, f"test_task_{request.task_id}.py"
            )
        
        # 运行API测试（如果提供了配置）
        api_test_result = None
        if request.api_tests:
            endpoints = []
            for endpoint in request.api_tests.endpoints:
                endpoints.append({
                    'path': endpoint.path,
                    'method': endpoint.method,
                    'data': endpoint.data,
                    'params': endpoint.params,
                    'expected_status': endpoint.expected_status
                })
            
            api_test_result = await test_service.test_api_endpoints(
                request.api_tests.base_url, endpoints, request.api_tests.auth_token
            )
        
        # 运行性能测试（如果提供了配置）
        performance_result = None
        if request.performance_test:
            performance_result = await test_service.run_performance_test(
                request.performance_test.base_url,
                request.performance_test.endpoint,
                request.performance_test.concurrent_users,
                request.performance_test.duration_seconds,
                request.performance_test.auth_token
            )
        
        # 生成测试报告
        report = await test_service.generate_test_report(
            request.task_id,
            syntax_result,
            unit_test_result,
            api_test_result,
            performance_result
        )
        
        # 更新任务状态
        if report['overall_success']:
            task.status = "completed"
            task.test_status = "passed"
        else:
            task.test_status = "failed"
        
        task.test_results = str(report)  # 存储测试结果
        db.commit()
        
        return TestReportResponse(
            task_id=report['task_id'],
            overall_success=report['overall_success'],
            summary=report['summary'],
            details=report['details'],
            recommendations=report['recommendations'],
            generated_at=report['generated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完整测试异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完整测试失败: {str(e)}")

@router.get("/task/{task_id}/report", response_model=TestReportResponse)
async def get_test_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务的测试报告
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        测试报告
    """
    try:
        # 验证任务存在且属于当前用户
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
        
        if not task.test_results:
            raise HTTPException(status_code=404, detail="该任务没有测试报告")
        
        # 解析测试结果
        import json
        report = json.loads(task.test_results)
        
        return TestReportResponse(
            task_id=report['task_id'],
            overall_success=report['overall_success'],
            summary=report['summary'],
            details=report['details'],
            recommendations=report['recommendations'],
            generated_at=report['generated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取测试报告异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试报告失败: {str(e)}")

@router.get("/health")
async def test_health():
    """测试服务健康检查
    
    Returns:
        服务状态
    """
    return {
        "status": "healthy",
        "service": "automated-testing",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "syntax-check",
            "unit-test",
            "api-test",
            "performance-test",
            "full-test"
        ]
    }