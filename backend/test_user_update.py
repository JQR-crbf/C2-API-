import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas import UserUpdate
from pydantic import ValidationError
import json

# 测试前端发送的数据格式
test_data_scenarios = [
    {
        "name": "中文角色名称",
        "data": {
            "username": "testuser_1758638952",
            "email": "test_1758638952@test.com",
            "role": "用户",  # 中文角色名称
            "password": "newpassword123"
        }
    },
    {
        "name": "英文user角色",
        "data": {
            "username": "testuser_1758638952",
            "email": "test_1758638952@test.com",
            "role": "user",
            "password": "newpassword123"
        }
    },
    {
        "name": "英文admin角色",
        "data": {
            "username": "testuser_1758638952",
            "email": "test_1758638952@test.com",
            "role": "admin",
            "password": "newpassword123"
        }
    },
    {
        "name": "空密码",
        "data": {
            "username": "testuser_1758638952",
            "email": "test_1758638952@test.com",
            "role": "user",
            "password": ""
        }
    },
    {
        "name": "无密码字段",
        "data": {
            "username": "testuser_1758638952",
            "email": "test_1758638952@test.com",
            "role": "user"
        }
    }
]

print("=== 测试UserUpdate模式验证 ===")

for scenario in test_data_scenarios:
    print(f"\n--- 测试场景: {scenario['name']} ---")
    test_data = scenario['data']
    print(f"测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        user_update = UserUpdate(**test_data)
        print("✅ 验证成功!")
        print(f"解析结果: {user_update.model_dump()}")
    except ValidationError as e:
        print("❌ 验证失败!")
        print(f"错误详情: {e}")
        print("具体错误:")
        for error in e.errors():
            print(f"  - 字段: {error['loc']}, 错误: {error['msg']}, 输入值: {error.get('input', 'N/A')}")