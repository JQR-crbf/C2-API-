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
    """增强版AI代码生成服务"""
    
    def __init__(self, api_key: str = None):
        """初始化AI服务
        
        Args:
            api_key: OpenRouter API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.model = os.getenv('AI_MODEL', 'anthropic/claude-3-5-sonnet-20241022')
        
        # 支持的AI功能类型
        self.supported_functions = {
            'code_generation': '代码生成',
            'code_review': '代码审查',
            'bug_fix': '问题修复',
            'code_optimization': '代码优化',
            'test_generation': '测试用例生成',
            'documentation': '文档生成',
            'refactoring': '代码重构'
        }
        
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
    
    async def review_code(
        self, 
        code: str, 
        task_description: str = "",
        db: Session = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """代码审查功能
        
        Args:
            code: 待审查的代码
            task_description: 任务描述
            db: 数据库会话
            
        Returns:
            Tuple[success, review_result, error_message]
        """
        try:
            prompt = self._build_code_review_prompt(code, task_description)
            response = await self._call_openai_api(prompt)
            
            if response:
                logger.info("代码审查完成")
                return True, response, None
            else:
                error_msg = "代码审查失败：无响应"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"代码审查异常：{str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def fix_code(
        self, 
        code: str, 
        error_message: str,
        task_description: str = "",
        db: Session = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """代码修复功能
        
        Args:
            code: 有问题的代码
            error_message: 错误信息
            task_description: 任务描述
            db: 数据库会话
            
        Returns:
            Tuple[success, fixed_code, error_message]
        """
        try:
            prompt = self._build_code_fix_prompt(code, error_message, task_description)
            response = await self._call_openai_api(prompt)
            
            if response:
                fixed_code = self._extract_code_from_response(response)
                logger.info("代码修复完成")
                return True, fixed_code, None
            else:
                error_msg = "代码修复失败：无响应"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"代码修复异常：{str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def optimize_code(
        self, 
        code: str, 
        optimization_type: str = "performance",
        task_description: str = "",
        db: Session = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """代码优化功能
        
        Args:
            code: 待优化的代码
            optimization_type: 优化类型 (performance, readability, security)
            task_description: 任务描述
            db: 数据库会话
            
        Returns:
            Tuple[success, optimized_code, error_message]
        """
        try:
            prompt = self._build_code_optimization_prompt(code, optimization_type, task_description)
            response = await self._call_openai_api(prompt)
            
            if response:
                optimized_code = self._extract_code_from_response(response)
                logger.info(f"代码优化完成 - 类型: {optimization_type}")
                return True, optimized_code, None
            else:
                error_msg = "代码优化失败：无响应"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"代码优化异常：{str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def generate_tests(
        self, 
        code: str, 
        test_type: str = "unit",
        task_description: str = "",
        db: Session = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """生成测试用例
        
        Args:
            code: 待测试的代码
            test_type: 测试类型 (unit, integration, api)
            task_description: 任务描述
            db: 数据库会话
            
        Returns:
            Tuple[success, test_code, error_message]
        """
        try:
            prompt = self._build_test_generation_prompt(code, test_type, task_description)
            response = await self._call_openai_api(prompt)
            
            if response:
                test_code = self._extract_code_from_response(response)
                logger.info(f"测试用例生成完成 - 类型: {test_type}")
                return True, test_code, None
            else:
                error_msg = "测试用例生成失败：无响应"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"测试用例生成异常：{str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def generate_documentation(
        self, 
        code: str, 
        doc_type: str = "api",
        task_description: str = "",
        db: Session = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """生成文档
        
        Args:
            code: 代码
            doc_type: 文档类型 (api, readme, comments)
            task_description: 任务描述
            db: 数据库会话
            
        Returns:
            Tuple[success, documentation, error_message]
        """
        try:
            prompt = self._build_documentation_prompt(code, doc_type, task_description)
            response = await self._call_openai_api(prompt)
            
            if response:
                logger.info(f"文档生成完成 - 类型: {doc_type}")
                return True, response, None
            else:
                error_msg = "文档生成失败：无响应"
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"文档生成异常：{str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
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
    
    def _build_code_review_prompt(self, code: str, task_description: str = "") -> str:
        """构建代码审查提示词"""
        prompt = f"""
你是一名资深的代码审查专家，请对以下代码进行全面审查：

任务描述：{task_description}

代码内容：
```
{code}
```

请从以下几个方面进行审查：
1. 代码质量和可读性
2. 性能优化建议
3. 安全性问题
4. 最佳实践遵循情况
5. 潜在的bug和问题
6. 代码结构和设计模式

请提供详细的审查报告，包括具体的改进建议。
"""
        return prompt
    
    def _build_code_fix_prompt(self, code: str, error_message: str, task_description: str = "") -> str:
        """构建代码修复提示词"""
        prompt = f"""
你是一名专业的代码调试专家，请修复以下代码中的问题：

任务描述：{task_description}

错误信息：
{error_message}

有问题的代码：
```
{code}
```

请提供修复后的完整代码，确保：
1. 修复所有错误
2. 保持原有功能不变
3. 遵循最佳实践
4. 添加必要的错误处理
5. 包含详细的中文注释

请只返回修复后的代码，不要包含其他说明。
"""
        return prompt
    
    def _build_code_optimization_prompt(self, code: str, optimization_type: str, task_description: str = "") -> str:
        """构建代码优化提示词"""
        optimization_focus = {
            "performance": "性能优化，包括算法效率、内存使用、执行速度等",
            "readability": "可读性优化，包括代码结构、命名规范、注释完善等",
            "security": "安全性优化，包括输入验证、权限控制、数据保护等"
        }
        
        focus = optimization_focus.get(optimization_type, "综合优化")
        
        prompt = f"""
你是一名代码优化专家，请对以下代码进行{focus}：

任务描述：{task_description}

原始代码：
```
{code}
```

优化要求：
1. 重点关注{focus}
2. 保持原有功能完整性
3. 遵循Python最佳实践
4. 添加详细的中文注释
5. 确保代码的可维护性

请提供优化后的完整代码。
"""
        return prompt
    
    def _build_test_generation_prompt(self, code: str, test_type: str, task_description: str = "") -> str:
        """构建测试用例生成提示词"""
        test_focus = {
            "unit": "单元测试，测试单个函数或方法",
            "integration": "集成测试，测试模块间的交互",
            "api": "API测试，测试接口的输入输出"
        }
        
        focus = test_focus.get(test_type, "综合测试")
        
        prompt = f"""
你是一名测试工程师，请为以下代码生成{focus}：

任务描述：{task_description}

待测试代码：
```
{code}
```

测试要求：
1. 使用pytest框架
2. 覆盖正常情况和异常情况
3. 包含边界值测试
4. 添加详细的中文注释
5. 确保测试的完整性和可靠性

请生成完整的测试代码。
"""
        return prompt
    
    def _build_documentation_prompt(self, code: str, doc_type: str, task_description: str = "") -> str:
        """构建文档生成提示词"""
        doc_focus = {
            "api": "API文档，包括接口说明、参数、返回值等",
            "readme": "README文档，包括项目介绍、使用方法、安装说明等",
            "comments": "代码注释，为代码添加详细的中文注释"
        }
        
        focus = doc_focus.get(doc_type, "技术文档")
        
        prompt = f"""
你是一名技术文档专家，请为以下代码生成{focus}：

任务描述：{task_description}

代码内容：
```
{code}
```

文档要求：
1. 使用中文编写
2. 结构清晰，易于理解
3. 包含具体的使用示例
4. 详细说明参数和返回值
5. 包含注意事项和最佳实践

请生成完整的文档内容。
"""
        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """从AI响应中提取代码"""
        # 尝试提取代码块
        import re
        
        # 匹配```python 或 ``` 包围的代码块
        code_pattern = r'```(?:python)?\s*\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # 返回第一个代码块
            return matches[0].strip()
        
        # 如果没有找到代码块，返回原始响应
        return response.strip()
    
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