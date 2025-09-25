from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from database import get_db
from services.ai_service import AICodeGenerationService
from models import Task

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/ai",
    tags=["AI服务"]
)

# AI服务实例
ai_service = AICodeGenerationService()

# 请求模型
class CodeReviewRequest(BaseModel):
    """代码审查请求模型"""
    code: str
    task_description: Optional[str] = ""

class CodeFixRequest(BaseModel):
    """代码修复请求模型"""
    code: str
    error_message: str
    task_description: Optional[str] = ""

class CodeOptimizationRequest(BaseModel):
    """代码优化请求模型"""
    code: str
    optimization_type: str = "performance"  # performance, readability, security
    task_description: Optional[str] = ""

class TestGenerationRequest(BaseModel):
    """测试生成请求模型"""
    code: str
    test_type: str = "unit"  # unit, integration, api
    task_description: Optional[str] = ""

class DocumentationRequest(BaseModel):
    """文档生成请求模型"""
    code: str
    doc_type: str = "api"  # api, readme, comments
    task_description: Optional[str] = ""

class AIResponse(BaseModel):
    """AI响应模型"""
    success: bool
    result: Optional[str] = None
    error_message: Optional[str] = None

@router.post("/generate-code/{task_id}", response_model=AIResponse)
async def generate_code(
    task_id: int,
    db: Session = Depends(get_db)
):
    """生成代码
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        AI响应结果
    """
    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 调用AI服务生成代码
        success, data_models, service_layer, routing_layer, test_cases, error_msg = await ai_service.generate_code(
            task, db
        )
        
        if success:
            result = {
                "data_models": data_models,
                "service_layer": service_layer,
                "routing_layer": routing_layer,
                "test_cases": test_cases
            }
            return AIResponse(
                success=True,
                result=str(result)
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"代码生成异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码生成失败：{str(e)}"
        )

@router.post("/review-code", response_model=AIResponse)
async def review_code(
    request: CodeReviewRequest,
    db: Session = Depends(get_db)
):
    """代码审查
    
    Args:
        request: 代码审查请求
        db: 数据库会话
        
    Returns:
        代码审查结果
    """
    try:
        success, review_result, error_msg = await ai_service.review_code(
            request.code,
            request.task_description,
            db
        )
        
        if success:
            return AIResponse(
                success=True,
                result=review_result
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"代码审查异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码审查失败：{str(e)}"
        )

@router.post("/fix-code", response_model=AIResponse)
async def fix_code(
    request: CodeFixRequest,
    db: Session = Depends(get_db)
):
    """代码修复
    
    Args:
        request: 代码修复请求
        db: 数据库会话
        
    Returns:
        修复后的代码
    """
    try:
        success, fixed_code, error_msg = await ai_service.fix_code(
            request.code,
            request.error_message,
            request.task_description,
            db
        )
        
        if success:
            return AIResponse(
                success=True,
                result=fixed_code
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"代码修复异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码修复失败：{str(e)}"
        )

@router.post("/optimize-code", response_model=AIResponse)
async def optimize_code(
    request: CodeOptimizationRequest,
    db: Session = Depends(get_db)
):
    """代码优化
    
    Args:
        request: 代码优化请求
        db: 数据库会话
        
    Returns:
        优化后的代码
    """
    try:
        success, optimized_code, error_msg = await ai_service.optimize_code(
            request.code,
            request.optimization_type,
            request.task_description,
            db
        )
        
        if success:
            return AIResponse(
                success=True,
                result=optimized_code
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"代码优化异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码优化失败：{str(e)}"
        )

@router.post("/generate-tests", response_model=AIResponse)
async def generate_tests(
    request: TestGenerationRequest,
    db: Session = Depends(get_db)
):
    """生成测试用例
    
    Args:
        request: 测试生成请求
        db: 数据库会话
        
    Returns:
        生成的测试代码
    """
    try:
        success, test_code, error_msg = await ai_service.generate_tests(
            request.code,
            request.test_type,
            request.task_description,
            db
        )
        
        if success:
            return AIResponse(
                success=True,
                result=test_code
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"测试生成异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试生成失败：{str(e)}"
        )

@router.post("/generate-documentation", response_model=AIResponse)
async def generate_documentation(
    request: DocumentationRequest,
    db: Session = Depends(get_db)
):
    """生成文档
    
    Args:
        request: 文档生成请求
        db: 数据库会话
        
    Returns:
        生成的文档
    """
    try:
        success, documentation, error_msg = await ai_service.generate_documentation(
            request.code,
            request.doc_type,
            request.task_description,
            db
        )
        
        if success:
            return AIResponse(
                success=True,
                result=documentation
            )
        else:
            return AIResponse(
                success=False,
                error_message=error_msg
            )
            
    except Exception as e:
        logger.error(f"文档生成异常：{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档生成失败：{str(e)}"
        )

@router.get("/supported-functions")
async def get_supported_functions():
    """获取支持的AI功能列表
    
    Returns:
        支持的功能列表
    """
    return {
        "supported_functions": ai_service.supported_functions,
        "message": "AI服务支持的功能列表"
    }