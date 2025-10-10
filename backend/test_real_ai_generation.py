#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实AI代码生成测试
"""

import sys
import os
import asyncio

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Task, TaskStatus
from services.ai_service import ai_service

async def test_real_ai_generation():
    """测试真实的AI代码生成"""
    print("🚀 开始真实AI代码生成测试...")
    
    db = SessionLocal()
    try:
        # 创建测试任务
        task = Task(
            user_id=7,
            title='商品库存管理API',
            description='创建一个商品库存管理API，包括查询库存、更新库存数量、库存预警等功能。支持按商品ID查询当前库存，批量更新库存，设置库存预警阈值。',
            input_params={
                'product_id': {
                    'type': 'integer', 
                    'required': True,
                    'description': '商品ID'
                },
                'quantity': {
                    'type': 'integer', 
                    'required': False,
                    'description': '库存数量（用于更新操作）'
                },
                'alert_threshold': {
                    'type': 'integer',
                    'required': False, 
                    'description': '库存预警阈值'
                }
            },
            output_params={
                'stock_info': {
                    'product_id': 'integer',
                    'product_name': 'string',
                    'current_stock': 'integer',
                    'reserved_stock': 'integer',
                    'available_stock': 'integer',
                    'alert_threshold': 'integer',
                    'is_low_stock': 'boolean',
                    'last_updated': 'datetime'
                },
                'status': 'success'
            },
            status=TaskStatus.BRANCH_CREATED
        )
        
        # 保存到数据库
        db.add(task)
        db.commit()
        db.refresh(task)
        
        print(f"✓ 创建测试任务成功，ID: {task.id}")
        print(f"任务标题: {task.title}")
        print(f"任务描述: {task.description}")
        
        # 检查API密钥
        if not ai_service.api_key:
            print("❌ 未配置API密钥，无法进行真实测试")
            return
        
        print(f"✓ 检测到API密钥: {ai_service.api_key[:10]}...")
        print(f"使用AI模型: {ai_service.model}")
        
        # 开始AI代码生成
        print("\n🤖 开始AI代码生成...")
        print("这可能需要30-60秒，请稍候...")
        
        success, generated_code, test_cases, error = await ai_service.generate_code(task, db)
        
        if success:
            print("\n🎉 AI代码生成成功!")
            print(f"生成代码长度: {len(generated_code)} 字符")
            print(f"测试用例长度: {len(test_cases)} 字符")
            
            print("\n=== 生成代码预览 (前800字符) ===")
            print(generated_code[:800])
            print("...")
            
            print("\n=== 测试用例预览 (前500字符) ===")
            print(test_cases[:500])
            print("...")
            
            # 保存完整代码到文件
            with open(f"generated_code_task_{task.id}.py", "w", encoding="utf-8") as f:
                f.write(f"# 任务ID: {task.id}\n")
                f.write(f"# 任务标题: {task.title}\n")
                f.write(f"# 生成时间: {task.updated_at}\n\n")
                f.write(generated_code)
            
            with open(f"generated_tests_task_{task.id}.py", "w", encoding="utf-8") as f:
                f.write(f"# 任务ID: {task.id}\n")
                f.write(f"# 测试用例\n\n")
                f.write(test_cases)
            
            print(f"\n✓ 完整代码已保存到: generated_code_task_{task.id}.py")
            print(f"✓ 测试用例已保存到: generated_tests_task_{task.id}.py")
            
            # 分析生成的代码
            print("\n=== 代码分析 ===")
            code_sections = [
                ("数据模型", "# === 数据模型"),
                ("数据模式", "# === 数据模式"),
                ("服务层", "# === 服务层"),
                ("路由层", "# === 路由层")
            ]
            
            for section_name, marker in code_sections:
                if marker in generated_code:
                    print(f"✓ 包含{section_name}")
                else:
                    print(f"✗ 缺少{section_name}")
            
            # 检查代码质量
            quality_checks = [
                ("FastAPI导入", "from fastapi import"),
                ("SQLAlchemy模型", "class.*Base"),
                ("Pydantic模式", "class.*BaseModel"),
                ("API路由", "@router"),
                ("错误处理", "HTTPException"),
                ("数据验证", "Field"),
                ("中文注释", "comment=")
            ]
            
            print("\n=== 代码质量检查 ===")
            for check_name, pattern in quality_checks:
                import re
                if re.search(pattern, generated_code):
                    print(f"✓ {check_name}")
                else:
                    print(f"⚠️  {check_name}")
        
        else:
            print(f"\n❌ AI代码生成失败: {error}")
        
        # 清理测试数据
        db.delete(task)
        db.commit()
        print(f"\n✓ 测试任务已清理")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

async def main():
    """主函数"""
    print("🧪 AI代码生成真实测试")
    print("=" * 50)
    
    # 检查基础配置
    print("=== 基础配置检查 ===")
    print(f"API密钥: {'已配置' if ai_service.api_key else '未配置'}")
    print(f"模型: {ai_service.model}")
    print(f"API URL: {ai_service.base_url}")
    
    if not ai_service.api_key:
        print("\n❌ 未配置API密钥，无法进行真实测试")
        print("请设置环境变量 OPENROUTER_API_KEY")
        return
    
    print("\n开始真实AI代码生成测试...")
    await test_real_ai_generation()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
