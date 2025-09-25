import os
import subprocess
import logging
import tempfile
import json
import requests
import ast
import sys
from typing import Optional, Tuple, Dict, List, Any
from datetime import datetime
import asyncio
from pathlib import Path
import re

# 配置日志
logger = logging.getLogger(__name__)

class AutomatedTestService:
    """自动化测试服务
    
    提供代码的自动化测试功能，包括：
    - Python语法检查
    - 代码质量检查
    - 单元测试执行
    - API接口测试
    - 性能测试
    """
    
    def __init__(self, project_root: str = None):
        """初始化测试服务
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root or os.getcwd()
        self.logger = logger
        self.test_results = {}
        
    async def check_python_syntax(self, code: str, filename: str = "temp.py") -> Tuple[bool, List[str], Optional[str]]:
        """检查Python代码语法
        
        Args:
            code: 要检查的Python代码
            filename: 文件名（用于错误报告）
            
        Returns:
            Tuple[success, warnings, error_message]
        """
        try:
            warnings = []
            
            # 基本语法检查
            try:
                ast.parse(code)
                self.logger.info(f"语法检查通过: {filename}")
            except SyntaxError as e:
                error_msg = f"语法错误 (行 {e.lineno}): {e.msg}"
                self.logger.error(f"语法检查失败: {error_msg}")
                return False, [], error_msg
            
            # 代码质量检查
            quality_warnings = await self._check_code_quality(code)
            warnings.extend(quality_warnings)
            
            return True, warnings, None
            
        except Exception as e:
            error_msg = f"语法检查异常: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
    
    async def _check_code_quality(self, code: str) -> List[str]:
        """检查代码质量
        
        Args:
            code: 要检查的代码
            
        Returns:
            警告信息列表
        """
        warnings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查行长度
            if len(line) > 120:
                warnings.append(f"行 {i}: 代码行过长 ({len(line)} 字符)")
            
            # 检查TODO注释
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                warnings.append(f"行 {i}: 发现待办事项注释")
            
            # 检查print语句（可能是调试代码）
            if re.search(r'\bprint\s*\(', line) and not line.startswith('#'):
                warnings.append(f"行 {i}: 发现print语句，可能是调试代码")
            
            # 检查空的except块
            if line.startswith('except') and i < len(lines):
                next_lines = lines[i:i+3]
                if any('pass' in l.strip() for l in next_lines):
                    warnings.append(f"行 {i}: 发现空的异常处理块")
        
        return warnings
    
    async def run_unit_tests(
        self, 
        test_code: str, 
        main_code: str,
        test_filename: str = "test_generated.py"
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """运行单元测试
        
        Args:
            test_code: 测试代码
            main_code: 主要代码
            test_filename: 测试文件名
            
        Returns:
            Tuple[success, test_results, error_message]
        """
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 写入主要代码
                main_file = os.path.join(temp_dir, "main.py")
                with open(main_file, 'w', encoding='utf-8') as f:
                    f.write(main_code)
                
                # 写入测试代码
                test_file = os.path.join(temp_dir, test_filename)
                with open(test_file, 'w', encoding='utf-8') as f:
                    # 确保测试代码导入主模块
                    if 'import main' not in test_code and 'from main' not in test_code:
                        test_code = "import main\n" + test_code
                    f.write(test_code)
                
                # 运行pytest
                result = await self._run_pytest(temp_dir, test_filename)
                
                return result
                
        except Exception as e:
            error_msg = f"运行单元测试异常: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    async def _run_pytest(self, test_dir: str, test_file: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """运行pytest测试
        
        Args:
            test_dir: 测试目录
            test_file: 测试文件
            
        Returns:
            Tuple[success, results, error_message]
        """
        try:
            # 构建pytest命令
            cmd = [
                sys.executable, '-m', 'pytest', 
                test_file, 
                '-v', 
                '--tb=short'
            ]
            
            # 运行pytest
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=test_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = await process.communicate()
            
            # 解析输出
            test_results = {
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'total': 0,
                'duration': 0,
                'details': [],
                'stdout': stdout,
                'stderr': stderr
            }
            
            # 简单解析pytest输出
            if stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                        test_name = line.split('::')[1].split()[0] if '::' in line else line
                        outcome = 'PASSED' if 'PASSED' in line else ('FAILED' if 'FAILED' in line else 'SKIPPED')
                        
                        test_results['details'].append({
                            'name': test_name,
                            'outcome': outcome.lower(),
                            'duration': 0,
                            'message': ''
                        })
                        
                        if outcome == 'PASSED':
                            test_results['passed'] += 1
                        elif outcome == 'FAILED':
                            test_results['failed'] += 1
                        elif outcome == 'SKIPPED':
                            test_results['skipped'] += 1
                
                test_results['total'] = test_results['passed'] + test_results['failed'] + test_results['skipped']
            
            success = process.returncode == 0 and test_results['failed'] == 0
            
            if success:
                self.logger.info(f"单元测试通过: {test_results['passed']}/{test_results['total']}")
            else:
                self.logger.warning(f"单元测试失败: {test_results['failed']}/{test_results['total']}")
            
            return success, test_results, None if success else stderr
            
        except Exception as e:
            error_msg = f"运行pytest异常: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    async def test_api_endpoints(
        self, 
        base_url: str, 
        endpoints: List[Dict[str, Any]],
        auth_token: str = None
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """测试API接口
        
        Args:
            base_url: API基础URL
            endpoints: 接口列表，每个包含method, path, data等
            auth_token: 认证令牌
            
        Returns:
            Tuple[success, test_results, error_message]
        """
        try:
            test_results = {
                'total': len(endpoints),
                'passed': 0,
                'failed': 0,
                'details': [],
                'start_time': datetime.now().isoformat(),
                'end_time': None
            }
            
            headers = {'Content-Type': 'application/json'}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            for endpoint in endpoints:
                result = await self._test_single_endpoint(
                    base_url, endpoint, headers
                )
                
                test_results['details'].append(result)
                
                if result['success']:
                    test_results['passed'] += 1
                else:
                    test_results['failed'] += 1
            
            test_results['end_time'] = datetime.now().isoformat()
            
            success = test_results['failed'] == 0
            
            if success:
                self.logger.info(f"API测试通过: {test_results['passed']}/{test_results['total']}")
            else:
                self.logger.warning(f"API测试失败: {test_results['failed']}/{test_results['total']}")
            
            return success, test_results, None
            
        except Exception as e:
            error_msg = f"API测试异常: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    async def _test_single_endpoint(
        self, 
        base_url: str, 
        endpoint: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """测试单个API接口
        
        Args:
            base_url: 基础URL
            endpoint: 接口配置
            headers: 请求头
            
        Returns:
            测试结果
        """
        result = {
            'endpoint': endpoint.get('path', ''),
            'method': endpoint.get('method', 'GET'),
            'success': False,
            'status_code': None,
            'response_time': 0,
            'error': None,
            'response_data': None
        }
        
        try:
            url = f"{base_url.rstrip('/')}{endpoint.get('path', '')}"
            method = endpoint.get('method', 'GET').upper()
            data = endpoint.get('data')
            params = endpoint.get('params')
            expected_status = endpoint.get('expected_status', 200)
            
            start_time = datetime.now()
            
            # 发送请求
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            result.update({
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == expected_status
            })
            
            # 尝试解析JSON响应
            try:
                result['response_data'] = response.json()
            except:
                result['response_data'] = response.text[:500]  # 限制长度
            
            if not result['success']:
                result['error'] = f"期望状态码 {expected_status}，实际 {response.status_code}"
            
        except requests.exceptions.Timeout:
            result['error'] = "请求超时"
        except requests.exceptions.ConnectionError:
            result['error'] = "连接错误"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    async def run_performance_test(
        self, 
        base_url: str, 
        endpoint: str,
        concurrent_users: int = 10,
        duration_seconds: int = 30,
        auth_token: str = None
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """运行性能测试
        
        Args:
            base_url: API基础URL
            endpoint: 测试接口
            concurrent_users: 并发用户数
            duration_seconds: 测试持续时间（秒）
            auth_token: 认证令牌
            
        Returns:
            Tuple[success, performance_results, error_message]
        """
        try:
            results = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0,
                'requests_per_second': 0,
                'error_rate': 0,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'errors': []
            }
            
            headers = {'Content-Type': 'application/json'}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            url = f"{base_url.rstrip('/')}{endpoint}"
            
            # 创建并发任务
            tasks = []
            for _ in range(concurrent_users):
                task = asyncio.create_task(
                    self._performance_worker(url, headers, duration_seconds, results)
                )
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks)
            
            results['end_time'] = datetime.now().isoformat()
            
            # 计算统计信息
            if results['total_requests'] > 0:
                results['error_rate'] = (results['failed_requests'] / results['total_requests']) * 100
                results['requests_per_second'] = results['total_requests'] / duration_seconds
            
            success = results['error_rate'] < 5  # 错误率低于5%认为成功
            
            self.logger.info(f"性能测试完成: {results['total_requests']} 请求，错误率 {results['error_rate']:.2f}%")
            
            return success, results, None
            
        except Exception as e:
            error_msg = f"性能测试异常: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    async def _performance_worker(
        self, 
        url: str, 
        headers: Dict[str, str], 
        duration: int, 
        results: Dict[str, Any]
    ):
        """性能测试工作线程
        
        Args:
            url: 测试URL
            headers: 请求头
            duration: 测试持续时间
            results: 结果字典（共享）
        """
        end_time = datetime.now().timestamp() + duration
        response_times = []
        
        while datetime.now().timestamp() < end_time:
            try:
                start = datetime.now()
                response = requests.get(url, headers=headers, timeout=10)
                end = datetime.now()
                
                response_time = (end - start).total_seconds() * 1000
                response_times.append(response_time)
                
                results['total_requests'] += 1
                
                if response.status_code == 200:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
                    results['errors'].append(f"状态码: {response.status_code}")
                
                # 更新响应时间统计
                results['min_response_time'] = min(results['min_response_time'], response_time)
                results['max_response_time'] = max(results['max_response_time'], response_time)
                
            except Exception as e:
                results['total_requests'] += 1
                results['failed_requests'] += 1
                results['errors'].append(str(e))
            
            # 短暂休息避免过度压力
            await asyncio.sleep(0.1)
        
        # 计算平均响应时间
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            results['average_response_time'] = avg_time
    
    async def generate_test_report(
        self, 
        task_id: int,
        syntax_result: Tuple[bool, List[str], Optional[str]],
        unit_test_result: Tuple[bool, Dict[str, Any], Optional[str]],
        api_test_result: Tuple[bool, Dict[str, Any], Optional[str]] = None,
        performance_result: Tuple[bool, Dict[str, Any], Optional[str]] = None
    ) -> Dict[str, Any]:
        """生成测试报告
        
        Args:
            task_id: 任务ID
            syntax_result: 语法检查结果
            unit_test_result: 单元测试结果
            api_test_result: API测试结果
            performance_result: 性能测试结果
            
        Returns:
            完整的测试报告
        """
        report = {
            'task_id': task_id,
            'generated_at': datetime.now().isoformat(),
            'overall_success': True,
            'summary': {
                'syntax_check': syntax_result[0],
                'unit_tests': unit_test_result[0],
                'api_tests': api_test_result[0] if api_test_result else None,
                'performance_tests': performance_result[0] if performance_result else None
            },
            'details': {
                'syntax_check': {
                    'success': syntax_result[0],
                    'warnings': syntax_result[1],
                    'error': syntax_result[2]
                },
                'unit_tests': {
                    'success': unit_test_result[0],
                    'results': unit_test_result[1],
                    'error': unit_test_result[2]
                }
            }
        }
        
        if api_test_result:
            report['details']['api_tests'] = {
                'success': api_test_result[0],
                'results': api_test_result[1],
                'error': api_test_result[2]
            }
        
        if performance_result:
            report['details']['performance_tests'] = {
                'success': performance_result[0],
                'results': performance_result[1],
                'error': performance_result[2]
            }
        
        # 计算总体成功状态
        report['overall_success'] = all([
            syntax_result[0],
            unit_test_result[0],
            api_test_result[0] if api_test_result else True,
            performance_result[0] if performance_result else True
        ])
        
        # 生成建议
        recommendations = []
        
        if not syntax_result[0]:
            recommendations.append("修复代码语法错误")
        elif syntax_result[1]:  # 有警告
            recommendations.append("考虑修复代码质量警告")
        
        if not unit_test_result[0]:
            recommendations.append("修复失败的单元测试")
        
        if api_test_result and not api_test_result[0]:
            recommendations.append("修复API接口问题")
        
        if performance_result and not performance_result[0]:
            recommendations.append("优化API性能")
        
        report['recommendations'] = recommendations
        
        self.logger.info(f"测试报告生成完成，任务ID: {task_id}，总体状态: {report['overall_success']}")
        
        return report