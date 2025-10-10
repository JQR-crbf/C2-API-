import requests
import json
import time

# 登录获取token
login_data = {
    "username": "jinqianru",
    "password": "123456"
}

print("正在尝试登录...")
login_response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
print(f"登录响应状态码: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    token = login_result.get('access_token')
    print("登录成功！")
    print(f"Token: {token[:50]}...")
    
    # 重新生成任务4的代码
    headers = {"Authorization": f"Bearer {token}"}
    regenerate_response = requests.post("http://localhost:8000/api/tasks/4/regenerate", headers=headers)
    print(f"\n重新生成代码响应状态码: {regenerate_response.status_code}")
    
    if regenerate_response.status_code == 200:
        regenerate_result = regenerate_response.json()
        print("重新生成代码成功！")
        print(f"响应消息: {regenerate_result.get('message')}")
        
        # 等待一段时间让AI生成代码
        print("\n等待AI生成代码...")
        for i in range(30):  # 等待30秒
            time.sleep(1)
            print(f"等待中... {i+1}/30秒", end='\r')
        
        print("\n\n检查任务4的最新状态...")
        task_response = requests.get("http://localhost:8000/api/tasks/4", headers=headers)
        if task_response.status_code == 200:
            task_data = task_response.json()
            print(f"任务状态: {task_data.get('status')}")
            print(f"生成的代码长度: {len(task_data.get('generated_code', ''))}")
            print(f"测试用例长度: {len(task_data.get('test_cases', ''))}")
            
            # 显示生成代码的前200个字符
            generated_code = task_data.get('generated_code', '')
            if generated_code and generated_code != '# 代码解析失败':
                print(f"\n生成代码预览:\n{generated_code[:200]}...")
            else:
                print(f"\n生成代码: {generated_code}")
        else:
            print(f"获取任务状态失败: {task_response.text}")
    else:
        print(f"重新生成代码失败: {regenerate_response.text}")
else:
    print(f"登录失败: {login_response.text}")