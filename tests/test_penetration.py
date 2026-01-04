"""
渗透测试脚本 - 多因素身份验证系统
模拟常见攻击手段，检验系统防护能力
"""
import os
import sys
import time
import json
import itertools
import string
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.auth_service import authenticate_password_only, register_user
from storage.file_repository import get_repository
from security.crypto import derive_key_from_password, generate_salt
from security.key_manager import load_or_init_data_key


class PenetrationTestResults:
    """渗透测试结果收集器"""
    def __init__(self):
        self.results = {
            'penetration_tests': {},
            'vulnerabilities_found': [],
            'security_score': 0,
            'test_summary': {
                'total_attacks': 0,
                'successful_attacks': 0,
                'blocked_attacks': 0
            }
        }

    def add_attack_result(self, attack_name: str, success: bool, details: Dict[str, Any]):
        """添加攻击测试结果"""
        self.results['penetration_tests'][attack_name] = {
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.results['test_summary']['total_attacks'] += 1
        if success:
            self.results['test_summary']['successful_attacks'] += 1
            self.results['vulnerabilities_found'].append(attack_name)
        else:
            self.results['test_summary']['blocked_attacks'] += 1

    def calculate_security_score(self):
        """计算安全评分"""
        total = self.results['test_summary']['total_attacks']
        blocked = self.results['test_summary']['blocked_attacks']

        if total > 0:
            self.results['security_score'] = (blocked / total) * 100

    def save_results(self, filename: str):
        """保存测试结果"""
        self.calculate_security_score()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


class PenetrationTester:
    """渗透测试类"""

    def __init__(self):
        self.results = PenetrationTestResults()
        self.weak_passwords = [
            "123456", "password", "123456789", "12345678", "12345",
            "1234567", "1234567890", "1234", "qwerty", "abc123",
            "111111", "123123", "admin", "letmein", "welcome"
        ]

    def test_brute_force_attack(self):
        """测试暴力破解攻击"""
        print("\n=== 暴力破解攻击测试 ===")

        # 创建测试用户
        test_username = f"brutetest_{int(time.time())}"
        weak_password = "123456"

        register_result = register_user(test_username, weak_password)
        if not register_result.success:
            print(f"无法创建测试用户: {register_result.message}")
            return

        print(f"创建测试用户: {test_username} (密码: {weak_password})")

        # 使用常见弱密码字典进行暴力破解
        attempts = 0
        successful = False
        start_time = time.time()

        for password in self.weak_passwords:
            attempts += 1
            result = authenticate_password_only(test_username, password)

            if result.success:
                successful = True
                end_time = time.time()
                duration = end_time - start_time

                print(f"[失败] 暴力破解成功!")
                print(f"   尝试次数: {attempts}")
                print(f"   用时: {duration:.2f}秒")
                print(f"   破解的密码: {password}")

                self.results.add_attack_result(
                    "暴力破解攻击",
                    True,
                    {
                        'attempts': attempts,
                        'duration_seconds': duration,
                        'password_found': password,
                        'attack_type': 'dictionary_attack'
                    }
                )
                break

            # 模拟攻击延迟
            time.sleep(0.01)

        if not successful:
            end_time = time.time()
            duration = end_time - start_time

            print(f"[通过] 暴力破解失败")
            print(f"   尝试次数: {attempts}")
            print(f"   用时: {duration:.2f}秒")

            self.results.add_attack_result(
                "暴力破解攻击",
                False,
                {
                    'attempts': attempts,
                    'duration_seconds': duration,
                    'passwords_tested': len(self.weak_passwords),
                    'attack_type': 'dictionary_attack'
                }
            )

    def test_user_enumeration(self):
        """测试用户枚举攻击"""
        print("\n=== 用户枚举攻击测试 ===")

        # 测试存在的用户和不存在的用户，看错误消息是否不同
        test_username = f"enumtest_{int(time.time())}"
        test_password = "TestPassword123"

        # 创建测试用户
        register_result = register_user(test_username, test_password)
        if not register_result.success:
            print(f"无法创建测试用户: {register_result.message}")
            return

        # 测试存在用户的错误消息
        result_existing = authenticate_password_only(test_username, "WrongPassword")
        error_existing = result_existing.message

        # 测试不存在用户的错误消息
        result_nonexistent = authenticate_password_only("nonexistent_user_12345", "AnyPassword")
        error_nonexistent = result_nonexistent.message

        print(f"存在用户错误消息: {error_existing}")
        print(f"不存在用户错误消息: {error_nonexistent}")

        # 检查错误消息是否相同（防止用户枚举）
        messages_identical = error_existing == error_nonexistent

        if messages_identical:
            print("[通过] 用户枚举攻击防护有效")
            self.results.add_attack_result(
                "用户枚举攻击",
                False,
                {
                    'protection_active': True,
                    'error_messages_identical': True,
                    'existing_user_error': error_existing,
                    'nonexistent_user_error': error_nonexistent
                }
            )
        else:
            print("[失败] 用户枚举攻击成功 - 错误消息不同")
            self.results.add_attack_result(
                "用户枚举攻击",
                True,
                {
                    'protection_active': False,
                    'error_messages_identical': False,
                    'existing_user_error': error_existing,
                    'nonexistent_user_error': error_nonexistent,
                    'vulnerability': 'different_error_messages'
                }
            )

    def test_sql_injection(self):
        """测试SQL注入攻击（虽然使用文件存储，但测试输入验证）"""
        print("\n=== SQL注入攻击测试 ===")

        # 测试常见的SQL注入载荷
        injection_payloads = [
            "admin'--",
            "admin' /*",
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "') OR '1'='1' --",
            "') OR ('1'='1' --",
            "admin' OR '1'='1' --",
            "admin' UNION SELECT * FROM users --"
        ]

        vulnerable = False

        for payload in injection_payloads:
            print(f"  测试载荷: {payload}")

            # 尝试使用注入载荷作为用户名
            result = authenticate_password_only(payload, "password")

            # 检查是否意外成功
            if result.success:
                print(f"  [失败] 可能存在注入漏洞 - 认证成功")
                vulnerable = True
                self.results.add_attack_result(
                    "SQL注入攻击",
                    True,
                    {
                        'payload': payload,
                        'unexpected_success': True,
                        'message': result.message
                    }
                )
                break
            else:
                print(f"  [通过] 注入尝试被阻止")

        if not vulnerable:
            print("[通过] SQL注入攻击防护有效")
            self.results.add_attack_result(
                "SQL注入攻击",
                False,
                {
                    'payloads_tested': len(injection_payloads),
                    'all_blocked': True
                }
            )

    def test_data_tampering(self):
        """测试数据篡改攻击"""
        print("\n=== 数据篡改攻击测试 ===")

        try:
            # 获取数据文件路径
            data_file = Path(__file__).parent.parent / 'data' / 'data.bin'

            if not data_file.exists():
                print("  数据文件不存在，跳过测试")
                return

            # 备份原始数据
            backup_file = data_file.with_suffix('.bin.backup')
            import shutil
            shutil.copy2(data_file, backup_file)

            # 读取原始数据
            with open(data_file, 'rb') as f:
                original_data = f.read()

            print(f"  原始数据大小: {len(original_data)} 字节")

            # 篡改数据（修改中间的一个字节）
            if len(original_data) > 100:
                tampered_data = bytearray(original_data)
                tampered_data[100] ^= 0x01  # 翻转一个字节

                # 写入篡改后的数据
                with open(data_file, 'wb') as f:
                    f.write(bytes(tampered_data))

                print("  数据已被篡改")

                # 尝试加载篡改后的数据
                try:
                    repo = get_repository()
                    data_key = load_or_init_data_key()
                    repo.load_data(data_key)

                    print("  [失败] 数据篡改未被发现!")
                    self.results.add_attack_result(
                        "数据篡改攻击",
                        True,
                        {
                            'tampering_detected': False,
                            'method': 'direct_file_modification'
                        }
                    )
                except Exception as e:
                    print(f"  [通过] 数据篡改被发现: {str(e)}")
                    self.results.add_attack_result(
                        "数据篡改攻击",
                        False,
                        {
                            'tampering_detected': True,
                            'error_message': str(e),
                            'method': 'direct_file_modification'
                        }
                    )
                finally:
                    # 恢复原始数据
                    shutil.copy2(backup_file, data_file)
                    backup_file.unlink()
                    print("  原始数据已恢复")

        except Exception as e:
            print(f"  测试过程中出错: {str(e)}")

    def test_timing_attack(self):
        """测试时序攻击"""
        print("\n=== 时序攻击测试 ===")

        # 创建测试用户
        test_username = f"timingtest_{int(time.time())}"
        test_password = "TimingTest123456"

        register_result = register_user(test_username, test_password)
        if not register_result.success:
            print(f"无法创建测试用户: {register_result.message}")
            return

        # 测试正确密码的认证时间
        correct_times = []
        for i in range(10):
            start = time.perf_counter()
            result = authenticate_password_only(test_username, test_password)
            end = time.perf_counter()
            if result.success:
                correct_times.append((end - start) * 1000)

        # 测试错误密码的认证时间
        incorrect_times = []
        for i in range(10):
            start = time.perf_counter()
            result = authenticate_password_only(test_username, "WrongPassword")
            end = time.perf_counter()
            if not result.success:
                incorrect_times.append((end - start) * 1000)

        if correct_times and incorrect_times:
            avg_correct = sum(correct_times) / len(correct_times)
            avg_incorrect = sum(incorrect_times) / len(incorrect_times)
            time_diff = abs(avg_correct - avg_incorrect)

            print(f"  正确密码平均时间: {avg_correct:.3f}ms")
            print(f"  错误密码平均时间: {avg_incorrect:.3f}ms")
            print(f"  时间差: {time_diff:.3f}ms")

            # 如果时间差大于5ms，可能存在时序攻击风险
            if time_diff > 5:
                print("  [警告]  可能存在时序攻击风险")
                self.results.add_attack_result(
                    "时序攻击",
                    True,
                    {
                        'vulnerable': True,
                        'avg_correct_ms': avg_correct,
                        'avg_incorrect_ms': avg_incorrect,
                        'time_difference_ms': time_diff,
                        'threshold_ms': 5
                    }
                )
            else:
                print("  [通过] 时序攻击防护有效")
                self.results.add_attack_result(
                    "时序攻击",
                    False,
                    {
                        'vulnerable': False,
                        'avg_correct_ms': avg_correct,
                        'avg_incorrect_ms': avg_incorrect,
                        'time_difference_ms': time_diff,
                        'threshold_ms': 5
                    }
                )

    def test_session_hijacking(self):
        """测试会话劫持攻击"""
        print("\n=== 会话劫持攻击测试 ===")

        # 由于系统是单机版且没有会话管理，此测试主要检查是否有会话机制
        print("  注意: 当前系统为单机版，没有网络会话管理")
        print("  [通过] 会话劫持攻击不适用")

        self.results.add_attack_result(
            "会话劫持攻击",
            False,
            {
                'applicable': False,
                'reason': 'standalone_application_no_sessions'
            }
        )

    def test_weak_password_policy(self):
        """测试弱密码策略"""
        print("\n=== 弱密码策略测试 ===")

        weak_passwords_to_test = [
            ("123", "3位数字"),
            ("12345", "5位数字"),
            ("password", "常见单词"),
            ("admin", "管理员默认密码"),
            ("111111", "重复字符"),
            ("abc123", "字母数字组合但太简单")
        ]

        vulnerabilities = []

        for password, description in weak_passwords_to_test:
            test_username = f"weakpwd_{int(time.time())}_{random.randint(1000, 9999)}"

            result = register_user(test_username, password)

            if result.success:
                print(f"  [失败] 弱密码被接受: {password} ({description})")
                vulnerabilities.append({
                    'password': password,
                    'description': description,
                    'username': test_username
                })
            else:
                print(f"  [通过] 弱密码被拒绝: {password} ({description})")

        if vulnerabilities:
            print(f"  发现 {len(vulnerabilities)} 个密码策略问题")
            self.results.add_attack_result(
                "弱密码策略",
                True,
                {
                    'vulnerable': True,
                    'weak_passwords_allowed': vulnerabilities,
                    'policy_issues': len(vulnerabilities)
                }
            )
        else:
            print("  [通过] 密码策略安全")
            self.results.add_attack_result(
                "弱密码策略",
                False,
                {
                    'vulnerable': False,
                    'passwords_tested': len(weak_passwords_to_test),
                    'all_blocked': True
                }
            )

    def run_all_penetration_tests(self):
        """运行所有渗透测试"""
        print("=" * 60)
        print("多因素身份验证系统 - 渗透测试套件")
        print("=" * 60)

        # 运行所有测试
        self.test_brute_force_attack()
        self.test_user_enumeration()
        self.test_sql_injection()
        self.test_data_tampering()
        self.test_timing_attack()
        self.test_session_hijacking()
        self.test_weak_password_policy()

        # 计算安全评分
        self.results.calculate_security_score()

        # 保存结果
        test_results_dir = Path(__file__).parent / 'results'
        test_results_dir.mkdir(exist_ok=True)

        results_file = test_results_dir / f'penetration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.results.save_results(str(results_file))

        # 打印总结
        print("\n" + "=" * 60)
        print("渗透测试总结")
        print("=" * 60)
        print(f"总攻击尝试: {self.results.results['test_summary']['total_attacks']}")
        print(f"成功攻击: {self.results.results['test_summary']['successful_attacks']}")
        print(f"被阻止攻击: {self.results.results['test_summary']['blocked_attacks']}")
        print(f"安全评分: {self.results.results['security_score']:.1f}/100")

        if self.results.results['vulnerabilities_found']:
            print("\n发现的漏洞:")
            for vuln in self.results.results['vulnerabilities_found']:
                print(f"  - {vuln}")
        else:
            print("\n[通过] 未发现严重漏洞")

        print(f"\n详细结果已保存到: {results_file}")

        return self.results


if __name__ == "__main__":
    import random
    tester = PenetrationTester()
    results = tester.run_all_penetration_tests()