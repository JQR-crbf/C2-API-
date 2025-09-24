import requests
import json
import os
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from models import Task, TaskLog, TaskStatus
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICodeGenerationService:
    """AI代码生成服务"""
    
    def __init__(self, api_key: str = None):
        """初始化AI服务
        
        Args:
            api_key: OpenRouter API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.model = os.getenv('AI_MODEL', 'anthropic/claude-3-5-sonnet-20241022')
        
        if not self.api_key:
            logger.warning("未找到OpenRouter API密钥，请检查环境变量OPENROUTER_API_KEY")
    
    async def generate_code(
        self, 
        task: Task, 
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """生成代码
        
        Args:
            task: 任务对象
            db: 数据库会话
            
        Returns:
            Tuple[success, generated_code, test_cases, error_message]
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.AI_GENERATING
            self._add_task_log(task.id, TaskStatus.AI_GENERATING, "开始AI代码生成", db)
            db.commit()
            
            # 构建提示词
            prompt = self._build_prompt(task)
            
            # 调用OpenAI API
            response = await self._call_openai_api(prompt)
            
            if response:
                generated_code, test_cases = self._parse_response(response)
                
                # 更新任务
                task.generated_code = generated_code
                task.test_cases = test_cases
                task.status = TaskStatus.TEST_READY
                
                self._add_task_log(
                    task.id, 
                    TaskStatus.TEST_READY, 
                    "AI代码生成完成，准备测试环境", 
                    db
                )
                db.commit()
                
                logger.info(f"任务 {task.id} 代码生成成功")
                return True, generated_code, test_cases, None
            else:
                error_msg = "AI代码生成失败：无响应"
                self._add_task_log(task.id, task.status, error_msg, db)
                db.commit()
                return False, None, None, error_msg
                
        except Exception as e:
            error_msg = f"AI代码生成异常：{str(e)}"
            logger.error(error_msg)
            self._add_task_log(task.id, task.status, error_msg, db)
            db.commit()
            return False, None, None, error_msg
    
    def _build_prompt(self, task: Task) -> str:
        """构建AI提示词"""
        
        # 读取API开发指南作为开发规范
        development_guide = self._load_development_guide()
        
        prompt = f"""
你是一个专业的API开发工程师。请严格按照以下项目开发规范生成FastAPI代码和测试用例。

=== 项目开发规范 ===
{development_guide}

=== 当前开发任务 ===
任务标题：{task.title}
任务描述：{task.description}

输入参数定义：
{json.dumps(task.input_params, ensure_ascii=False, indent=2) if task.input_params else '无'}

输出参数定义：
{json.dumps(task.output_params, ensure_ascii=False, indent=2) if task.output_params else '无'}

=== 开发要求 ===
请严格按照上述项目开发规范，生成以下内容：

1. **数据模型文件** (models/your_model.py)：
   - 使用SQLAlchemy定义数据库表结构
   - 包含必要的字段、索引和关系
   - 添加适当的注释和配置

2. **数据模式文件** (schemas/your_schema.py)：
   - 定义请求/响应的Pydantic模型
   - 包含数据验证规则
   - 支持创建、更新、查询等操作

3. **服务层文件** (services/your_service.py)：
   - 实现业务逻辑处理
   - 包含CRUD操作方法
   - 添加错误处理和日志记录

4. **路由层文件** (api/v1/your_api.py)：
   - 定义FastAPI路由接口
   - 包含完整的CRUD操作端点
   - 添加Swagger文档注释
   - 实现统一的错误处理

5. **测试用例**：
   - 覆盖所有API端点
   - 包含正常、边界和异常情况
   - 使用pytest框架

=== 重要提醒 ===
- 必须严格遵循上述开发规范的分层架构
- 所有代码必须包含详细的中文注释
- 确保生成的代码可以直接在项目中使用
- 路由必须包含适当的tags用于Swagger分组
- 所有接口都要返回统一的ApiResponse格式

请按以下格式返回：

```python
# === 数据模型 (models/your_model.py) ===
[数据模型代码]
```

```python
# === 数据模式 (schemas/your_schema.py) ===
[数据模式代码]
```

```python
# === 服务层 (services/your_service.py) ===
[服务层代码]
```

```python
# === 路由层 (api/v1/your_api.py) ===
[路由层代码]
```

```python
# === 测试用例 ===
[测试代码]
```
"""
        return prompt
    
    def _load_development_guide(self) -> str:
        """加载API开发指南"""
        try:
            guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'API接口开发指南.md')
            if os.path.exists(guide_path):
                with open(guide_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"API开发指南文件不存在: {guide_path}")
                return self._get_default_guide()
        except Exception as e:
            logger.error(f"读取API开发指南失败: {str(e)}")
            return self._get_default_guide()
    
    def _get_default_guide(self) -> str:
        """获取默认开发指南"""
        return """
# 默认API开发规范

## 项目架构
本项目采用分层架构设计：
- 路由层(Router): 处理HTTP请求，参数验证，调用服务层
- 服务层(Service): 业务逻辑处理，数据操作
- 模型层(Model): 数据库表结构定义
- 数据模式层(Schema): 请求/响应数据验证和序列化

## 开发规范
1. 使用FastAPI框架
2. 遵循RESTful API设计原则
3. 统一使用ApiResponse响应格式
4. 包含完整的错误处理和日志记录
5. 添加详细的Swagger文档注释
"""
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """调用OpenRouter API"""
        try:
            if not self.api_key:
                logger.error("OpenRouter API密钥未配置")
                return None
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # 可选，用于统计
                "X-Title": "AI API Platform"  # 可选，用于统计
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的API开发工程师，擅长使用FastAPI框架开发高质量的API接口。请根据用户需求生成完整的API代码，包括路由、数据模型、错误处理和测试用例。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.3,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API请求异常: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"OpenRouter API调用出错: {str(e)}")
            return None
    
    def _parse_response(self, response: str) -> Tuple[str, str]:
        """解析AI响应，提取代码和测试用例"""
        try:
            # 记录原始响应用于调试
            logger.info(f"AI响应长度: {len(response)}")
            logger.debug(f"AI响应前500字符: {response[:500]}")
            
            # 提取所有代码块（除了测试用例）
            code_sections = []
            
            # 查找数据模型
            model_start = response.find("# === 数据模型")
            if model_start != -1:
                model_end = response.find("```", model_start)
                if model_end != -1:
                    next_section = response.find("```python", model_end + 3)
                    if next_section != -1:
                        model_code = response[model_start:next_section].strip()
                        code_sections.append(model_code)
            
            # 查找数据模式
            schema_start = response.find("# === 数据模式")
            if schema_start != -1:
                schema_end = response.find("```", schema_start)
                if schema_end != -1:
                    next_section = response.find("```python", schema_end + 3)
                    if next_section != -1:
                        schema_code = response[schema_start:next_section].strip()
                        code_sections.append(schema_code)
            
            # 查找服务层/业务逻辑层
            service_start = response.find("# === 服务层")
            if service_start == -1:
                service_start = response.find("# === 业务逻辑层")
            if service_start != -1:
                service_end = response.find("```", service_start)
                if service_end != -1:
                    next_section = response.find("```python", service_end + 3)
                    if next_section != -1:
                        service_code = response[service_start:next_section].strip()
                        code_sections.append(service_code)
            
            # 查找路由层
            router_start = response.find("# === 路由层")
            if router_start != -1:
                router_end = response.find("```", router_start)
                if router_end != -1:
                    next_section = response.find("```python", router_end + 3)
                    if next_section == -1:
                        # 如果没有下一个section，查找测试用例开始位置
                        test_section = response.find("# === 测试用例")
                        if test_section != -1:
                            router_code = response[router_start:test_section].strip()
                        else:
                            router_code = response[router_start:].strip()
                    else:
                        router_code = response[router_start:next_section].strip()
                    code_sections.append(router_code)
            
            # 合并所有代码段
            if code_sections:
                generated_code = "\n\n".join(code_sections)
            else:
                # 如果没有找到标准格式，尝试提取所有python代码块
                import re
                python_blocks = re.findall(r'```python\n(.*?)\n```', response, re.DOTALL)
                if python_blocks:
                    # 排除测试用例（通常包含test_或pytest关键字）
                    code_blocks = [block for block in python_blocks if not ('test_' in block.lower() or 'pytest' in block.lower())]
                    if code_blocks:
                        generated_code = "\n\n# ===== 分隔符 =====\n\n".join(code_blocks)
                    else:
                        generated_code = "# 未找到有效的代码块"
                else:
                    generated_code = "# 代码解析失败：未找到python代码块"
            
            # 提取测试用例
            test_start = response.find("# === 测试用例")
            if test_start != -1:
                # 查找测试用例后的代码块
                test_code_start = response.find("```python", test_start)
                if test_code_start != -1:
                    test_code_end = response.find("```", test_code_start + 9)
                    if test_code_end != -1:
                        test_cases = response[test_start:test_code_end + 3].strip()
                    else:
                        test_cases = response[test_start:].strip()
                else:
                    test_cases = "# 测试用例代码块未找到"
            else:
                # 尝试查找包含测试的代码块
                import re
                test_blocks = re.findall(r'```python\n(.*?)\n```', response, re.DOTALL)
                test_code_blocks = [block for block in test_blocks if ('test_' in block.lower() or 'pytest' in block.lower())]
                if test_code_blocks:
                    test_cases = "# === 测试用例 ===\n\n" + "\n\n".join(test_code_blocks)
                else:
                    test_cases = "# 测试用例解析失败"
            
            logger.info(f"代码解析完成，生成代码长度: {len(generated_code)}, 测试用例长度: {len(test_cases)}")
            return generated_code, test_cases
            
        except Exception as e:
            logger.error(f"响应解析失败：{str(e)}")
            return "# 代码解析异常", "# 测试用例解析异常"
    
    def _add_task_log(self, task_id: int, status: TaskStatus, message: str, db: Session):
        """添加任务日志"""
        task_log = TaskLog(
            task_id=task_id,
            status=status.value,
            message=message
        )
        db.add(task_log)

# 创建全局AI服务实例
ai_service = AICodeGenerationService()