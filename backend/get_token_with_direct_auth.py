#!/usr/bin/env python3
"""
直接生成认证令牌，用于测试API调用
绕过密码验证，直接为jinqianru用户生成有效token
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

from database import get_db
from models import User
from auth_utils import create_user_token

def generate_token_for_jinqianru():
    """为jinqianru用户直接生成token"""
    
    print("🔑 正在为jinqianru用户生成认证令牌...")
    
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 查找jinqianru用户
        user = db.query(User).filter(User.email == "123@qq.com").first()
        
        if not user:
            print("❌ 未找到jinqianru用户")
            return None
            
        print(f"✅ 找到用户: {user.username} (ID: {user.id})")
        print(f"   邮箱: {user.email}")
        print(f"   角色: {user.role}")
        print(f"   状态: {'激活' if user.is_active else '未激活'}")
        
        # 直接生成token
        token = create_user_token(
            user_id=user.id,
            username=user.username,
            role=user.role.value
        )
        
        print(f"\n🎯 Token生成成功!")
        print(f"Token: {token}")
        
        # 保存到文件供其他脚本使用
        with open("valid_token.txt", "w") as f:
            f.write(token)
        print(f"✅ Token已保存到 valid_token.txt 文件")
        
        return token
        
    except Exception as e:
        print(f"❌ 生成token失败: {str(e)}")
        return None
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    token = generate_token_for_jinqianru()
    if token:
        print(f"\n🚀 可以使用此token进行API测试:")
        print(f"   Authorization: Bearer {token}")
    else:
        print(f"\n💥 Token生成失败，请检查错误信息")