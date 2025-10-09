#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_db
from models import Task
from services.guided_deployment_service import GuidedDeploymentService
import re

def analyze_task_7_deployment_steps():
    """分析任务7的部署步骤数量"""
    db = next(get_db())
    try:
        task = db.query(Task).filter(Task.id == 7).first()
        
        if not task:
            print("任务7不存在")
            return
        
        print("=== 任务7部署步骤分析 ===")
        print(f"任务标题: {task.title}")
        print(f"任务描述: {task.description}")
        
        # 分析生成的代码结构
        generated_code = task.generated_code
        if not generated_code:
            print("任务未生成代码，无法分析部署步骤")
            return
        
        print("\n=== 代码结构分析 ===")
        
        # 解析代码中的文件结构
        file_sections = []
        
        # 查找所有的文件标记
        file_patterns = [
            r'# === 数据模型 \(([^)]+)\) ===',
            r'# === 数据模式 \(([^)]+)\) ===', 
            r'# === 服务层 \(([^)]+)\) ===',
            r'# === 路由层 \(([^)]+)\) ==='
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, generated_code)
            file_sections.extend(matches)
        
        print(f"检测到的文件数量: {len(file_sections)}")
        for i, file_path in enumerate(file_sections, 1):
            print(f"  {i}. {file_path}")
        
        # 根据guided_deployment_service.py的逻辑计算步骤
        print("\n=== 部署步骤计算 ===")
        
        # 基础步骤（固定）
        base_steps = [
            "进入项目目录",
            "切换到主分支", 
            "获取最新代码"
        ]
        
        # 文件操作步骤
        file_steps = []
        
        # 为每个文件生成步骤
        for file_path in file_sections:
            # 每个文件需要的步骤：
            # 1. 创建目录结构
            # 2. 创建__init__.py文件
            # 3. 创建并编辑文件
            # 4. 保存文件
            
            file_steps.extend([
                f"创建目录结构 ({file_path})",
                f"创建 __init__.py 文件",
                f"创建并编辑 {file_path}",
                f"保存 {file_path}"
            ])
        
        # API路由注册步骤（如果有API文件）
        api_files = [f for f in file_sections if 'api' in f.lower()]
        router_steps = []
        if api_files:
            router_steps.extend([
                "编辑主路由文件",
                "注册新API路由",
                "保存路由配置",
                "备份 __init__.py"
            ])
        
        # 项目配置步骤（固定）
        config_steps = [
            "返回项目根目录",
            "创建 requirements.txt",
            "写入依赖配置",
            "安装项目依赖",
            "启动项目进行测试",
            "测试API接口",
            "停止测试进程"
        ]
        
        # Git操作步骤（可选，如果有git_repo_url）
        git_steps = [
            "添加文件到Git",
            "提交代码变更", 
            "推送到远程仓库"
        ]
        
        # 计算总步骤数
        all_steps = base_steps + file_steps + router_steps + config_steps + git_steps
        
        print(f"\n=== 详细步骤列表 ===")
        print(f"基础步骤 ({len(base_steps)}个):")
        for i, step in enumerate(base_steps, 1):
            print(f"  {i}. {step}")
        
        print(f"\n文件操作步骤 ({len(file_steps)}个):")
        for i, step in enumerate(file_steps, len(base_steps) + 1):
            print(f"  {i}. {step}")
        
        if router_steps:
            print(f"\n路由注册步骤 ({len(router_steps)}个):")
            for i, step in enumerate(router_steps, len(base_steps) + len(file_steps) + 1):
                print(f"  {i}. {step}")
        
        print(f"\n项目配置步骤 ({len(config_steps)}个):")
        start_idx = len(base_steps) + len(file_steps) + len(router_steps) + 1
        for i, step in enumerate(config_steps, start_idx):
            print(f"  {i}. {step}")
        
        print(f"\nGit操作步骤 ({len(git_steps)}个):")
        start_idx = len(base_steps) + len(file_steps) + len(router_steps) + len(config_steps) + 1
        for i, step in enumerate(git_steps, start_idx):
            print(f"  {i}. {step}")
        
        print(f"\n=== 总结 ===")
        print(f"总步骤数: {len(all_steps)}")
        print(f"  - 基础步骤: {len(base_steps)}")
        print(f"  - 文件操作步骤: {len(file_steps)}")
        print(f"  - 路由注册步骤: {len(router_steps)}")
        print(f"  - 项目配置步骤: {len(config_steps)}")
        print(f"  - Git操作步骤: {len(git_steps)}")
        
        print(f"\n检测到的文件类型分布:")
        models_count = len([f for f in file_sections if 'model' in f.lower()])
        schemas_count = len([f for f in file_sections if 'schema' in f.lower()])
        services_count = len([f for f in file_sections if 'service' in f.lower()])
        api_count = len([f for f in file_sections if 'api' in f.lower()])
        
        print(f"  - 数据模型文件: {models_count}")
        print(f"  - 数据模式文件: {schemas_count}")
        print(f"  - 服务层文件: {services_count}")
        print(f"  - API路由文件: {api_count}")
        
        # 验证步骤数是否合理
        expected_file_steps = len(file_sections) * 4  # 每个文件4个步骤
        if len(file_steps) == expected_file_steps:
            print(f"\n✅ 文件步骤计算正确: {len(file_sections)}个文件 × 4步骤/文件 = {expected_file_steps}步骤")
        else:
            print(f"\n❌ 文件步骤计算异常: 预期{expected_file_steps}，实际{len(file_steps)}")
            
    except Exception as e:
        print(f"分析失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_task_7_deployment_steps()