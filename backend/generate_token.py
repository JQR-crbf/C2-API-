#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import jwt
from datetime import datetime, timedelta

def generate_test_token():
    """生成测试用的JWT token"""
    # 使用与auth_utils.py相同的密钥
    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    
    # 创建payload
    payload = {
        "sub": "5",  # 用户ID
        "user_id": 5,
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24小时后过期
    }
    
    # 生成token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"生成的JWT token: {token}")
    return token

if __name__ == '__main__':
    generate_test_token()