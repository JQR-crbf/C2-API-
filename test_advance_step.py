import requests
import json

# 配置
BASE_URL = "http://localhost:8080"
USERNAME = "jinqianru"
PASSWORD = "123456"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
ADVANCE_STEP_URL = f"{BASE_URL}/api/tasks/{{task_id}}/advance"

def get_auth_token():
    """获取认证令牌"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_advance_step(task_id, token):
    """测试推进步骤功能"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试推进步骤
    advance_data = {
        "action": "advance",
        "comment": "测试推进步骤功能"
    }
    
    url = ADVANCE_STEP_URL.format(task_id=task_id)
    response = requests.post(url, json=advance_data, headers=headers)
    
    print(f"推进步骤测试结果:")
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.status_code == 200

def main():
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        print("无法获取认证令牌，测试终止")
        return
    
    print(f"成功获取认证令牌")
    
    # 使用一个已存在的任务ID进行测试（假设任务ID为1）
    task_id = 1
    
    # 测试推进步骤
    success = test_advance_step(task_id, token)
    
    if success:
        print("✅ 推进步骤功能测试成功！")
    else:
        print("❌ 推进步骤功能测试失败")

if __name__ == "__main__":
    main()