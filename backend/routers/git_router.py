from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.git_service import GitService
from database import get_db
from models import Task, User
from routers.auth import get_current_user
from sqlalchemy.orm import Session

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/git", tags=["Git操作"])

# 请求模型
class GitStatusResponse(BaseModel):
    """Git状态响应模型"""
    success: bool
    current_branch: Optional[str] = None
    has_changes: bool = False
    has_unpushed_commits: bool = False
    remote_configured: bool = False
    status_output: Optional[str] = None
    remote_info: Optional[str] = None
    message: Optional[str] = None

class CreateBranchRequest(BaseModel):
    """创建分支请求模型"""
    task_id: int = Field(..., description="任务ID")
    task_description: str = Field(..., description="任务描述")
    base_branch: str = Field(default="main", description="基础分支")

class CreateBranchResponse(BaseModel):
    """创建分支响应模型"""
    success: bool
    branch_name: Optional[str] = None
    message: Optional[str] = None

class CommitRequest(BaseModel):
    """提交代码请求模型"""
    task_id: int = Field(..., description="任务ID")
    task_title: str = Field(..., description="任务标题")
    file_list: Optional[List[str]] = Field(default=None, description="要提交的文件列表")
    commit_message: Optional[str] = Field(default=None, description="自定义提交信息")

class CommitResponse(BaseModel):
    """提交代码响应模型"""
    success: bool
    commit_hash: Optional[str] = None
    message: Optional[str] = None

class PushRequest(BaseModel):
    """推送代码请求模型"""
    branch_name: Optional[str] = Field(default=None, description="分支名称")
    remote_name: str = Field(default="origin", description="远程仓库名称")

class PushResponse(BaseModel):
    """推送代码响应模型"""
    success: bool
    output: Optional[str] = None
    message: Optional[str] = None

class PullRequest(BaseModel):
    """拉取代码请求模型"""
    branch: str = Field(default="main", description="要拉取的分支")

class PullResponse(BaseModel):
    """拉取代码响应模型"""
    success: bool
    output: Optional[str] = None
    message: Optional[str] = None

class BranchListResponse(BaseModel):
    """分支列表响应模型"""
    success: bool
    branches: List[str] = []
    message: Optional[str] = None

class DeleteBranchRequest(BaseModel):
    """删除分支请求模型"""
    branch_name: str = Field(..., description="分支名称")
    force: bool = Field(default=False, description="是否强制删除")

class DeleteBranchResponse(BaseModel):
    """删除分支响应模型"""
    success: bool
    output: Optional[str] = None
    message: Optional[str] = None

class PRInfoResponse(BaseModel):
    """PR信息响应模型"""
    title: str
    body: str
    head: str
    base: str

class GitWorkflowRequest(BaseModel):
    """Git工作流请求模型"""
    task_id: int = Field(..., description="任务ID")
    task_title: str = Field(..., description="任务标题")
    task_description: str = Field(..., description="任务描述")
    base_branch: str = Field(default="main", description="基础分支")
    target_branch: str = Field(default="main", description="目标分支")
    file_list: Optional[List[str]] = Field(default=None, description="要提交的文件列表")

class GitWorkflowResponse(BaseModel):
    """Git工作流响应模型"""
    success: bool
    branch_name: Optional[str] = None
    commit_hash: Optional[str] = None
    push_output: Optional[str] = None
    pr_info: Optional[PRInfoResponse] = None
    message: Optional[str] = None
    steps_completed: List[str] = []
    error_step: Optional[str] = None

# 初始化Git服务
git_service = GitService()

@router.get("/status", response_model=GitStatusResponse, summary="检查Git仓库状态")
async def get_git_status(
    current_user: User = Depends(get_current_user)
):
    """检查Git仓库状态
    
    返回当前仓库的状态信息，包括：
    - 当前分支
    - 是否有未提交的更改
    - 是否有未推送的提交
    - 远程仓库配置状态
    """
    try:
        success, status_info, error_msg = await git_service.check_git_status()
        
        if not success:
            return GitStatusResponse(
                success=False,
                message=error_msg or "检查Git状态失败"
            )
        
        return GitStatusResponse(
            success=True,
            current_branch=status_info.get('current_branch'),
            has_changes=status_info.get('has_changes', False),
            has_unpushed_commits=status_info.get('has_unpushed_commits', False),
            remote_configured=status_info.get('remote_configured', False),
            status_output=status_info.get('status_output'),
            remote_info=status_info.get('remote_info'),
            message="Git状态检查成功"
        )
        
    except Exception as e:
        logger.error(f"检查Git状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查Git状态失败: {str(e)}")

@router.post("/pull", response_model=PullResponse, summary="拉取最新代码")
async def pull_latest_code(
    request: PullRequest,
    current_user: User = Depends(get_current_user)
):
    """拉取最新代码
    
    从远程仓库拉取指定分支的最新代码
    """
    try:
        success, output, error_msg = await git_service.pull_latest_code(request.branch)
        
        if not success:
            return PullResponse(
                success=False,
                message=error_msg or "拉取代码失败"
            )
        
        return PullResponse(
            success=True,
            output=output,
            message=f"成功拉取分支 {request.branch} 的最新代码"
        )
        
    except Exception as e:
        logger.error(f"拉取代码异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"拉取代码失败: {str(e)}")

@router.post("/branch/create", response_model=CreateBranchResponse, summary="创建功能分支")
async def create_feature_branch(
    request: CreateBranchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建功能分支
    
    基于指定的基础分支创建新的功能分支
    """
    try:
        # 验证任务是否存在
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        success, branch_name, error_msg = await git_service.create_feature_branch(
            request.task_id,
            request.task_description,
            request.base_branch
        )
        
        if not success:
            return CreateBranchResponse(
                success=False,
                message=error_msg or "创建分支失败"
            )
        
        # 更新任务状态
        task.git_branch = branch_name
        db.commit()
        
        return CreateBranchResponse(
            success=True,
            branch_name=branch_name,
            message=f"成功创建功能分支: {branch_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建分支异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建分支失败: {str(e)}")

@router.post("/commit", response_model=CommitResponse, summary="提交代码更改")
async def commit_changes(
    request: CommitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交代码更改
    
    将当前的代码更改提交到Git仓库
    """
    try:
        # 验证任务是否存在
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        success, commit_hash, error_msg = await git_service.commit_changes(
            request.task_id,
            request.task_title,
            request.file_list,
            request.commit_message
        )
        
        if not success:
            return CommitResponse(
                success=False,
                message=error_msg or "提交代码失败"
            )
        
        # 更新任务状态
        task.git_commit_hash = commit_hash
        db.commit()
        
        return CommitResponse(
            success=True,
            commit_hash=commit_hash,
            message=f"成功提交代码，提交哈希: {commit_hash}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交代码异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交代码失败: {str(e)}")

@router.post("/push", response_model=PushResponse, summary="推送代码到远程仓库")
async def push_to_remote(
    request: PushRequest,
    current_user: User = Depends(get_current_user)
):
    """推送代码到远程仓库
    
    将本地提交推送到远程仓库
    """
    try:
        success, output, error_msg = await git_service.push_to_remote(
            request.branch_name,
            request.remote_name
        )
        
        if not success:
            return PushResponse(
                success=False,
                message=error_msg or "推送代码失败"
            )
        
        return PushResponse(
            success=True,
            output=output,
            message="成功推送代码到远程仓库"
        )
        
    except Exception as e:
        logger.error(f"推送代码异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推送代码失败: {str(e)}")

@router.get("/branches", response_model=BranchListResponse, summary="获取分支列表")
async def get_branch_list(
    current_user: User = Depends(get_current_user)
):
    """获取分支列表
    
    返回仓库中所有分支的列表
    """
    try:
        success, branches, error_msg = await git_service.get_branch_list()
        
        if not success:
            return BranchListResponse(
                success=False,
                message=error_msg or "获取分支列表失败"
            )
        
        return BranchListResponse(
            success=True,
            branches=branches,
            message="成功获取分支列表"
        )
        
    except Exception as e:
        logger.error(f"获取分支列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分支列表失败: {str(e)}")

@router.delete("/branch", response_model=DeleteBranchResponse, summary="删除分支")
async def delete_branch(
    request: DeleteBranchRequest,
    current_user: User = Depends(get_current_user)
):
    """删除分支
    
    删除指定的本地和远程分支
    """
    try:
        success, output, error_msg = await git_service.delete_branch(
            request.branch_name,
            request.force
        )
        
        if not success:
            return DeleteBranchResponse(
                success=False,
                message=error_msg or "删除分支失败"
            )
        
        return DeleteBranchResponse(
            success=True,
            output=output,
            message=f"成功删除分支: {request.branch_name}"
        )
        
    except Exception as e:
        logger.error(f"删除分支异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除分支失败: {str(e)}")

@router.get("/pr-info/{task_id}", response_model=PRInfoResponse, summary="获取PR信息")
async def get_pr_info(
    task_id: int,
    target_branch: str = "main",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Pull Request信息
    
    生成用于创建Pull Request的标准化信息
    """
    try:
        # 验证任务是否存在
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if not task.git_branch:
            raise HTTPException(status_code=400, detail="任务尚未创建Git分支")
        
        pr_info = await git_service.create_pull_request_info(
            task_id,
            task.title,
            task.description or "",
            task.git_branch,
            target_branch
        )
        
        return PRInfoResponse(**pr_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PR信息异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取PR信息失败: {str(e)}")

@router.post("/workflow", response_model=GitWorkflowResponse, summary="执行完整Git工作流")
async def execute_git_workflow(
    request: GitWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行完整Git工作流
    
    包括：创建分支 -> 提交代码 -> 推送到远程 -> 生成PR信息
    """
    try:
        # 验证任务是否存在
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        steps_completed = []
        
        # 步骤1: 创建功能分支
        success, branch_name, error_msg = await git_service.create_feature_branch(
            request.task_id,
            request.task_description,
            request.base_branch
        )
        
        if not success:
            return GitWorkflowResponse(
                success=False,
                message=error_msg or "创建分支失败",
                error_step="create_branch"
            )
        
        steps_completed.append("创建功能分支")
        
        # 步骤2: 提交代码
        success, commit_hash, error_msg = await git_service.commit_changes(
            request.task_id,
            request.task_title,
            request.file_list
        )
        
        if not success:
            return GitWorkflowResponse(
                success=False,
                branch_name=branch_name,
                message=error_msg or "提交代码失败",
                steps_completed=steps_completed,
                error_step="commit_changes"
            )
        
        steps_completed.append("提交代码更改")
        
        # 步骤3: 推送到远程仓库
        success, push_output, error_msg = await git_service.push_to_remote(branch_name)
        
        if not success:
            return GitWorkflowResponse(
                success=False,
                branch_name=branch_name,
                commit_hash=commit_hash,
                message=error_msg or "推送代码失败",
                steps_completed=steps_completed,
                error_step="push_to_remote"
            )
        
        steps_completed.append("推送到远程仓库")
        
        # 步骤4: 生成PR信息
        pr_info = await git_service.create_pull_request_info(
            request.task_id,
            request.task_title,
            request.task_description,
            branch_name,
            request.target_branch
        )
        
        steps_completed.append("生成PR信息")
        
        # 更新任务状态
        task.git_branch = branch_name
        task.git_commit_hash = commit_hash
        task.status = "completed"
        db.commit()
        
        return GitWorkflowResponse(
            success=True,
            branch_name=branch_name,
            commit_hash=commit_hash,
            push_output=push_output,
            pr_info=PRInfoResponse(**pr_info),
            message="Git工作流执行成功",
            steps_completed=steps_completed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行Git工作流异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行Git工作流失败: {str(e)}")