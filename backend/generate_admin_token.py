#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from database import engine
from models import User
from auth_utils import create_user_token
from datetime import timedelta

def generate_admin_token():
    """为admin用户生成访问token"""
    
    # 创建数据库会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查找admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("错误：未找到admin用户")
            return
        
        print(f"找到admin用户:")
        print(f"  用户名: {admin_user.username}")
        print(f"  邮箱: {admin_user.email}")
        print(f"  角色: {admin_user.role}")
        print(f"  用户ID: {admin_user.id}")
        
        # 生成token
        access_token = create_user_token(
            user_id=admin_user.id,
            username=admin_user.username,
            role=str(admin_user.role)
        )
        
        print(f"\n=== Admin用户Token生成成功 ===")
        print(f"Token: {access_token}")
        print(f"\n=== 使用说明 ===")
        print(f"1. 打开浏览器开发者工具（F12）")
        print(f"2. 在控制台中执行以下代码：")
        print(f"   localStorage.setItem('access_token', '{access_token}');")
        print(f"   location.reload();")
        print(f"3. 刷新页面后，admin用户应该能看到所有任务")
        
    except Exception as e:
        print(f"生成token时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_admin_token()