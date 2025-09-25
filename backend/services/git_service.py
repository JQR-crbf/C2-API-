import os
import subprocess
import logging
from typing import Optional, Tuple, Dict, List
from datetime import datetime
import asyncio
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class GitService:
    """Git操作自动化服务
    
    提供Git仓库的自动化操作功能，包括：
    - 分支创建和管理
    - 代码提交和推送
    - 仓库状态检查
    - 冲突检测和处理
    """
    
    def __init__(self, repo_path: str = None):
        """初始化Git服务
        
        Args:
            repo_path: Git仓库路径，如果为None则使用当前工作目录
        """
        self.repo_path = repo_path or os.getcwd()
        self.logger = logger
        
    async def check_git_status(self) -> Tuple[bool, Dict[str, any], Optional[str]]:
        """检查Git仓库状态
        
        Returns:
            Tuple[success, status_info, error_message]
        """
        try:
            # 检查是否为Git仓库
            is_repo = await self._run_git_command(['rev-parse', '--git-dir'])
            if not is_repo[0]:
                return False, {}, "当前目录不是Git仓库"
            
            # 获取当前分支
            current_branch = await self._run_git_command(['branch', '--show-current'])
            if not current_branch[0]:
                return False, {}, "无法获取当前分支信息"
            
            # 获取仓库状态
            status_result = await self._run_git_command(['status', '--porcelain'])
            if not status_result[0]:
                return False, {}, "无法获取仓库状态"
            
            # 检查远程仓库
            remote_result = await self._run_git_command(['remote', '-v'])
            
            # 检查未提交的更改
            has_changes = bool(status_result[1].strip())
            
            # 检查是否有未推送的提交
            unpushed_result = await self._run_git_command(['log', '@{u}..HEAD', '--oneline'])
            has_unpushed = bool(unpushed_result[1].strip()) if unpushed_result[0] else False
            
            status_info = {
                'current_branch': current_branch[1].strip(),
                'has_changes': has_changes,
                'has_unpushed_commits': has_unpushed,
                'remote_configured': bool(remote_result[1].strip()),
                'status_output': status_result[1],
                'remote_info': remote_result[1] if remote_result[0] else ''
            }
            
            self.logger.info(f"Git状态检查完成: {status_info}")
            return True, status_info, None
            
        except Exception as e:
            error_msg = f"Git状态检查失败: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    async def pull_latest_code(self, branch: str = 'main') -> Tuple[bool, str, Optional[str]]:
        """拉取最新代码
        
        Args:
            branch: 要拉取的分支名称
            
        Returns:
            Tuple[success, output, error_message]
        """
        try:
            # 首先检查当前分支
            current_branch_result = await self._run_git_command(['branch', '--show-current'])
            if not current_branch_result[0]:
                return False, '', "无法获取当前分支"
            
            current_branch = current_branch_result[1].strip()
            
            # 如果不在目标分支，先切换
            if current_branch != branch:
                checkout_result = await self._run_git_command(['checkout', branch])
                if not checkout_result[0]:
                    return False, '', f"切换到分支 {branch} 失败: {checkout_result[1]}"
            
            # 拉取最新代码
            pull_result = await self._run_git_command(['pull', 'origin', branch])
            if not pull_result[0]:
                return False, '', f"拉取代码失败: {pull_result[1]}"
            
            self.logger.info(f"成功拉取分支 {branch} 的最新代码")
            return True, pull_result[1], None
            
        except Exception as e:
            error_msg = f"拉取代码异常: {str(e)}"
            self.logger.error(error_msg)
            return False, '', error_msg
    
    async def create_feature_branch(
        self, 
        task_id: int, 
        task_description: str,
        base_branch: str = 'main'
    ) -> Tuple[bool, str, Optional[str]]:
        """创建功能分支
        
        Args:
            task_id: 任务ID
            task_description: 任务描述
            base_branch: 基础分支
            
        Returns:
            Tuple[success, branch_name, error_message]
        """
        try:
            # 生成分支名称
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 清理任务描述，只保留字母数字和连字符
            clean_description = ''.join(c if c.isalnum() or c in '-_' else '-' for c in task_description.lower())
            clean_description = clean_description[:30]  # 限制长度
            branch_name = f"feature/task-{task_id}-{clean_description}-{timestamp}"
            
            # 确保在基础分支上
            checkout_result = await self._run_git_command(['checkout', base_branch])
            if not checkout_result[0]:
                return False, '', f"切换到基础分支 {base_branch} 失败: {checkout_result[1]}"
            
            # 拉取最新代码
            pull_result = await self._run_git_command(['pull', 'origin', base_branch])
            if not pull_result[0]:
                self.logger.warning(f"拉取基础分支最新代码失败: {pull_result[1]}")
            
            # 创建新分支
            create_result = await self._run_git_command(['checkout', '-b', branch_name])
            if not create_result[0]:
                return False, '', f"创建分支失败: {create_result[1]}"
            
            self.logger.info(f"成功创建功能分支: {branch_name}")
            return True, branch_name, None
            
        except Exception as e:
            error_msg = f"创建分支异常: {str(e)}"
            self.logger.error(error_msg)
            return False, '', error_msg
    
    async def commit_changes(
        self, 
        task_id: int,
        task_title: str,
        file_list: List[str] = None,
        commit_message: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """提交代码更改
        
        Args:
            task_id: 任务ID
            task_title: 任务标题
            file_list: 要提交的文件列表，如果为None则提交所有更改
            commit_message: 自定义提交信息
            
        Returns:
            Tuple[success, commit_hash, error_message]
        """
        try:
            # 检查是否有更改
            status_result = await self._run_git_command(['status', '--porcelain'])
            if not status_result[0]:
                return False, '', "无法检查仓库状态"
            
            if not status_result[1].strip():
                return False, '', "没有需要提交的更改"
            
            # 添加文件
            if file_list:
                for file_path in file_list:
                    add_result = await self._run_git_command(['add', file_path])
                    if not add_result[0]:
                        self.logger.warning(f"添加文件 {file_path} 失败: {add_result[1]}")
            else:
                # 添加所有更改
                add_result = await self._run_git_command(['add', '.'])
                if not add_result[0]:
                    return False, '', f"添加文件失败: {add_result[1]}"
            
            # 生成提交信息
            if not commit_message:
                commit_message = self._generate_commit_message(task_id, task_title)
            
            # 提交更改
            commit_result = await self._run_git_command(['commit', '-m', commit_message])
            if not commit_result[0]:
                return False, '', f"提交失败: {commit_result[1]}"
            
            # 获取提交哈希
            hash_result = await self._run_git_command(['rev-parse', 'HEAD'])
            commit_hash = hash_result[1].strip()[:8] if hash_result[0] else 'unknown'
            
            self.logger.info(f"成功提交更改，提交哈希: {commit_hash}")
            return True, commit_hash, None
            
        except Exception as e:
            error_msg = f"提交代码异常: {str(e)}"
            self.logger.error(error_msg)
            return False, '', error_msg
    
    async def push_to_remote(
        self, 
        branch_name: str = None,
        remote_name: str = 'origin'
    ) -> Tuple[bool, str, Optional[str]]:
        """推送到远程仓库
        
        Args:
            branch_name: 分支名称，如果为None则使用当前分支
            remote_name: 远程仓库名称
            
        Returns:
            Tuple[success, output, error_message]
        """
        try:
            # 获取当前分支
            if not branch_name:
                current_branch_result = await self._run_git_command(['branch', '--show-current'])
                if not current_branch_result[0]:
                    return False, '', "无法获取当前分支"
                branch_name = current_branch_result[1].strip()
            
            # 推送到远程仓库
            push_result = await self._run_git_command(['push', '-u', remote_name, branch_name])
            if not push_result[0]:
                return False, '', f"推送失败: {push_result[1]}"
            
            self.logger.info(f"成功推送分支 {branch_name} 到远程仓库 {remote_name}")
            return True, push_result[1], None
            
        except Exception as e:
            error_msg = f"推送代码异常: {str(e)}"
            self.logger.error(error_msg)
            return False, '', error_msg
    
    async def create_pull_request_info(
        self, 
        task_id: int,
        task_title: str,
        task_description: str,
        branch_name: str,
        target_branch: str = 'main'
    ) -> Dict[str, str]:
        """生成Pull Request信息
        
        Args:
            task_id: 任务ID
            task_title: 任务标题
            task_description: 任务描述
            branch_name: 源分支
            target_branch: 目标分支
            
        Returns:
            PR信息字典
        """
        pr_title = f"feat: {task_title} (Task #{task_id})"
        
        pr_body = f"""## 任务描述
{task_description}

## 更改内容
- 由AI API平台自动生成的API代码
- 任务ID: {task_id}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试状态
- [ ] 代码语法检查通过
- [ ] 单元测试通过
- [ ] API接口测试通过

## 审核要点
- 检查生成的API接口是否符合需求
- 验证数据模型和验证逻辑
- 确认错误处理和安全性

---
*此PR由AI API开发自动化平台生成*
"""
        
        return {
            'title': pr_title,
            'body': pr_body,
            'head': branch_name,
            'base': target_branch
        }
    
    def _generate_commit_message(self, task_id: int, task_title: str) -> str:
        """生成标准化的提交信息
        
        Args:
            task_id: 任务ID
            task_title: 任务标题
            
        Returns:
            格式化的提交信息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        commit_message = f"""feat: Add API for {task_title}

- Generated by AI API Platform
- Task ID: {task_id}
- Generated time: {timestamp}
- Auto-generated code with tests

Co-authored-by: AI-API-Platform <ai@api-platform.com>"""
        
        return commit_message
    
    async def _run_git_command(self, args: List[str]) -> Tuple[bool, str]:
        """执行Git命令
        
        Args:
            args: Git命令参数列表
            
        Returns:
            Tuple[success, output]
        """
        try:
            # 构建完整命令
            cmd = ['git'] + args
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                text=True
            )
            
            stdout, _ = await process.communicate()
            
            success = process.returncode == 0
            output = stdout.strip() if stdout else ''
            
            if success:
                self.logger.debug(f"Git命令成功: {' '.join(args)}")
            else:
                self.logger.warning(f"Git命令失败: {' '.join(args)}, 输出: {output}")
            
            return success, output
            
        except Exception as e:
            self.logger.error(f"执行Git命令异常: {' '.join(args)}, 错误: {str(e)}")
            return False, str(e)
    
    async def get_branch_list(self) -> Tuple[bool, List[str], Optional[str]]:
        """获取分支列表
        
        Returns:
            Tuple[success, branch_list, error_message]
        """
        try:
            result = await self._run_git_command(['branch', '-a'])
            if not result[0]:
                return False, [], f"获取分支列表失败: {result[1]}"
            
            branches = []
            for line in result[1].split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    # 清理分支名称
                    branch = line.replace('remotes/origin/', '').strip()
                    if branch and branch not in branches:
                        branches.append(branch)
            
            return True, branches, None
            
        except Exception as e:
            error_msg = f"获取分支列表异常: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
    
    async def delete_branch(
        self, 
        branch_name: str, 
        force: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """删除分支
        
        Args:
            branch_name: 分支名称
            force: 是否强制删除
            
        Returns:
            Tuple[success, output, error_message]
        """
        try:
            # 确保不在要删除的分支上
            current_branch_result = await self._run_git_command(['branch', '--show-current'])
            if current_branch_result[0] and current_branch_result[1].strip() == branch_name:
                # 切换到main分支
                checkout_result = await self._run_git_command(['checkout', 'main'])
                if not checkout_result[0]:
                    return False, '', f"无法切换到main分支: {checkout_result[1]}"
            
            # 删除本地分支
            delete_flag = '-D' if force else '-d'
            delete_result = await self._run_git_command(['branch', delete_flag, branch_name])
            if not delete_result[0]:
                return False, '', f"删除本地分支失败: {delete_result[1]}"
            
            # 删除远程分支
            remote_delete_result = await self._run_git_command(['push', 'origin', '--delete', branch_name])
            if not remote_delete_result[0]:
                self.logger.warning(f"删除远程分支失败: {remote_delete_result[1]}")
            
            self.logger.info(f"成功删除分支: {branch_name}")
            return True, delete_result[1], None
            
        except Exception as e:
            error_msg = f"删除分支异常: {str(e)}"
            self.logger.error(error_msg)
            return False, '', error_msg