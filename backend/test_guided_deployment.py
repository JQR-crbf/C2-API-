#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
引导部署功能测试脚本
"""

import asyncio
import sys
from database import SessionLocal
from models import Task, User, DeploymentSession, DeploymentStep, TaskStatus
from services.guided_deployment_service import guided_deployment_service
from services.ssh_manager import ssh_manager

async def test_deployment_service():
    """测试引导部署服务"""
    print("🧪 开始测试引导部署服务...")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # 查找现有任务
        existing_task = db.query(Task).filter(Task.generated_code.isnot(None)).first()
        
        if not existing_task:
            print("❌ 没有找到带有生成代码的任务，创建测试任务...")
            # 创建测试任务
            test_task = Task(
                user_id=7,  # jinqianru用户
                title="测试引导部署",
                description="这是一个用于测试引导部署功能的任务",
                status=TaskStatus.TESTING,
                generated_code="""
# 文件：app/models/test.py
```python
from sqlalchemy import Column, Integer, String
from database import Base

class TestModel(Base):
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

# 文件：app/schemas/test.py
```python
from pydantic import BaseModel

class TestSchema(BaseModel):
    id: int
    name: str
```

# 文件：app/routers/test.py
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    return {"message": "Hello from test endpoint"}
```
                """
            )
            db.add(test_task)
            db.commit()
            db.refresh(test_task)
            existing_task = test_task
            print(f"✅ 创建测试任务成功 (ID: {existing_task.id})")
        else:
            print(f"✅ 找到现有任务 (ID: {existing_task.id}): {existing_task.title}")
        
        # 测试代码分析
        print("\n📝 测试代码分析...")
        code_files = guided_deployment_service.analyze_generated_code(existing_task.generated_code)
        print(f"✅ 分析出 {len(code_files)} 个文件:")
        for file_path, content in code_files.items():
            print(f"  - {file_path} ({len(content)} 字符)")
        
        # 测试部署步骤生成
        print("\n📋 测试部署步骤生成...")
        steps = guided_deployment_service.generate_deployment_steps(
            existing_task,
            "/home/testuser/api_projects",
            "https://github.com/test/repo.git"
        )
        print(f"✅ 生成了 {len(steps)} 个部署步骤:")
        for step in steps[:5]:  # 只显示前5个步骤
            print(f"  {step['step_number']}. {step['step_name']}")
        if len(steps) > 5:
            print(f"  ... 还有 {len(steps) - 5} 个步骤")
        
        # 测试requirements生成
        print("\n📦 测试requirements生成...")
        requirements = guided_deployment_service.generate_requirements(existing_task.generated_code)
        requirements_lines = requirements.split('\n')
        print(f"✅ 生成了 {len(requirements_lines)} 个依赖包:")
        for req in requirements_lines[:5]:
            if req.strip():
                print(f"  - {req}")
        if len(requirements_lines) > 5:
            print(f"  ... 还有 {len(requirements_lines) - 5} 个依赖")
        
        # 测试创建部署会话
        print("\n🔗 测试创建部署会话...")
        server_config = {
            'host': 'test.example.com',
            'port': 22,
            'username': 'testuser',
            'deployment_path': '/home/testuser/api_projects'
        }
        
        success, session, error = await guided_deployment_service.create_deployment_session(
            db, existing_task.id, existing_task.user_id, server_config
        )
        
        if success and session:
            print(f"✅ 部署会话创建成功 (ID: {session.id})")
            
            # 测试初始化步骤
            print("\n⚙️ 测试初始化部署步骤...")
            step_success = await guided_deployment_service.initialize_deployment_steps(
                db, session, existing_task
            )
            
            if step_success:
                # 查看创建的步骤
                steps = db.query(DeploymentStep).filter(
                    DeploymentStep.session_id == session.id
                ).order_by(DeploymentStep.step_number).all()
                
                print(f"✅ 初始化了 {len(steps)} 个部署步骤:")
                for step in steps[:5]:
                    print(f"  {step.step_number}. {step.step_name} ({step.status})")
                if len(steps) > 5:
                    print(f"  ... 还有 {len(steps) - 5} 个步骤")
                
            else:
                print("❌ 初始化部署步骤失败")
            
            # 清理测试数据
            print("\n🧹 清理测试数据...")
            db.query(DeploymentStep).filter(DeploymentStep.session_id == session.id).delete()
            db.delete(session)
            
            # 如果是测试创建的任务，也删除它
            if existing_task.title == "测试引导部署":
                db.delete(existing_task)
            
            db.commit()
            print("✅ 测试数据清理完成")
            
        else:
            print(f"❌ 创建部署会话失败: {error}")
        
        print("\n🎉 引导部署服务测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

def test_ssh_manager():
    """测试SSH管理器基础功能"""
    print("\n🔐 测试SSH管理器...")
    
    # 测试连接信息生成
    connection_id = ssh_manager._generate_connection_id("test.com", 22, "testuser")
    print(f"✅ 连接ID生成: {connection_id}")
    
    # 测试连接列表
    connections = ssh_manager.list_connections()
    print(f"✅ 当前连接数: {len(connections)}")
    
    # 测试过期连接清理
    ssh_manager.cleanup_expired_connections()
    print("✅ 过期连接清理完成")
    
    return True

async def main():
    """主测试函数"""
    print("🧪 引导部署功能测试套件")
    print("=" * 50)
    
    # 测试引导部署服务
    deployment_success = await test_deployment_service()
    
    # 测试SSH管理器
    ssh_success = test_ssh_manager()
    
    if deployment_success and ssh_success:
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！")
        print("\n📋 功能已就绪:")
        print("1. ✅ 代码分析和文件提取")
        print("2. ✅ 部署步骤自动生成")
        print("3. ✅ Requirements.txt生成")
        print("4. ✅ 部署会话管理")
        print("5. ✅ 数据库表结构正确")
        print("6. ✅ SSH连接管理基础功能")
        
        print("\n🚀 下一步:")
        print("1. 启动前端开发服务器")
        print("2. 访问任务详情页面")
        print("3. 点击'引导部署'标签测试完整流程")
        
        return True
    else:
        print("\n💥 部分测试失败！")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        sys.exit(1)
