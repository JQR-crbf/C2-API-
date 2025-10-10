import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 禁用SQLAlchemy日志
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from services.guided_deployment_service import GuidedDeploymentService

def test_field_removal():
    """测试step_description字段是否已被删除"""
    service = GuidedDeploymentService()
    
    # 创建一个模拟任务
    mock_task = {
        'id': 7,
        'name': 'Test Task',
        'files': ['app/models/test.py', 'app/api/v1/test.py']
    }
    
    # 生成部署步骤
    steps = service.generate_deployment_steps(mock_task, '/test/path')
    
    print(f"生成了 {len(steps)} 个步骤")
    print("\n检查前5个步骤的字段:")
    
    for i, step in enumerate(steps[:5]):
        print(f"\n步骤 {i+1}:")
        print(f"  字段: {list(step.keys())}")
        
        # 检查是否还有step_description字段
        if 'step_description' in step:
            print(f"  ❌ 错误: 步骤 {i+1} 仍然包含 step_description 字段")
        else:
            print(f"  ✅ 正确: 步骤 {i+1} 不包含 step_description 字段")
        
        # 显示步骤内容
        print(f"  step_number: {step.get('step_number')}")
        print(f"  step_name: {step.get('step_name')}")
        print(f"  command: {step.get('command')}")
    
    # 检查所有步骤是否都没有step_description字段
    has_description = any('step_description' in step for step in steps)
    
    if has_description:
        print("\n❌ 测试失败: 仍有步骤包含 step_description 字段")
    else:
        print("\n✅ 测试成功: 所有步骤都已删除 step_description 字段")
    
    # 验证所有步骤都有必需的字段
    required_fields = ['step_number', 'step_name', 'command']
    missing_fields = []
    
    for i, step in enumerate(steps):
        for field in required_fields:
            if field not in step:
                missing_fields.append(f"步骤 {i+1} 缺少字段: {field}")
    
    if missing_fields:
        print("\n❌ 发现缺少必需字段:")
        for missing in missing_fields:
            print(f"  {missing}")
    else:
        print("\n✅ 所有步骤都包含必需的字段 (step_number, step_name, command)")

if __name__ == "__main__":
    test_field_removal()