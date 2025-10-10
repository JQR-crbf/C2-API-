#!/usr/bin/env python3
"""
测试登录API性能
"""

import requests
import time

def test_login_performance():
    """测试登录API性能"""
    print('测试登录API性能...')
    
    start_time = time.time()
    try:
        response = requests.post('http://localhost:8080/api/auth/login', 
                               json={'username': 'jinqianru', 'password': '123456'},
                               timeout=5)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        print(f'登录API响应时间: {response_time:.2f}ms')
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ 登录成功')
            data = response.json()
            print(f'用户: {data["user_info"]["username"]}')
            print(f'角色: {data["user_info"]["role"]}')
        else:
            print(f'❌ 登录失败: {response.text}')
            
    except requests.exceptions.Timeout:
        print('⏰ 请求超时 (>5秒)')
    except Exception as e:
        print(f'❌ 请求失败: {e}')

if __name__ == "__main__":
    test_login_performance()