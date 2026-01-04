"""
综合测试套件 - 多因素身份验证系统
包含功能测试、安全测试和性能测试
"""
import os
import sys
import time
import json
import random
import string
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.auth_service import (
    register_user,
    authenticate_user,
    authenticate_password_only,
    change_password,
    register_user_with_face
)
from storage.file_repository import get_repository
from security.crypto import (
    derive_key_from_password,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    generate_salt
)
from security.key_manager import load_or_init_data_key
from storage.models import SystemConfig


class TestResults:
    """测试结果收集器"""
    def __init__(self):
        self.results = {
            'functional_tests': {},
            'security_tests': {},
            'performance_tests': {},
            'test_summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }

    def add_result(self, category: str, test_name: str, passed: bool, details: Any = None):
        """添加测试结果"""
        if category not in self.results:
            self.results[category] = {}

        self.results[category][test_name] = {
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.results['test_summary']['total_tests'] += 1
        if passed:
            self.results['test_summary']['passed'] += 1
        else:
            self.results['test_summary']['failed'] += 1

    def save_results(self, filename: str):
        """保存测试结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


class FunctionalTests:
    """功能测试类"""

    def __init__(self):
        self.test_users = []
        self.results = TestResults()

    def test_user_registration(self):
        """测试用户注册功能"""
        print("\n=== 测试用户注册 ===")

        test_cases = [
            ("testuser1", "Test123456", True, "正常注册"),
            ("", "Test123456", False, "空用户名"),
            ("testuser2", "123", False, "密码太短"),
            ("testuser3", "Test123456", True, "第二个用户注册"),
            ("testuser1", "Test123456", False, "重复用户名"),
        ]

        for username, password, should_pass, description in test_cases:
            try:
                result = register_user(username, password)
                passed = result.success == should_pass

                if passed and result.success:
                    self.test_users.append((username, password))

                self.results.add_result(
                    'functional_tests',
                    f'注册测试-{description}',
                    passed,
                    {
                        'username': username,
                        'expected': should_pass,
                        'actual': result.success,
                        'message': result.message
                    }
                )

                print(f"  {description}: {'[通过]' if passed else '[失败]'} - {result.message}")

            except Exception as e:
                self.results.add_result(
                    'functional_tests',
                    f'注册测试-{description}',
                    False,
                    {'error': str(e)}
                )
                print(f"  {description}: [异常] - {str(e)}")

    def test_password_authentication(self):
        """测试密码认证功能"""
        print("\n=== 测试密码认证 ===")

        if not self.test_users:
            print("  没有测试用户，跳过认证测试")
            return

        test_cases = [
            (self.test_users[0][0], self.test_users[0][1], True, "正确密码"),
            (self.test_users[0][0], "WrongPassword123", False, "错误密码"),
            ("nonexistent", "Test123456", False, "不存在的用户"),
            ("", "", False, "空输入"),
        ]

        for username, password, should_pass, description in test_cases:
            try:
                result = authenticate_password_only(username, password)
                passed = result.success == should_pass

                self.results.add_result(
                    'functional_tests',
                    f'密码认证-{description}',
                    passed,
                    {
                        'username': username,
                        'expected': should_pass,
                        'actual': result.success,
                        'message': result.message
                    }
                )

                print(f"  {description}: {'[通过]' if passed else '[失败]'} - {result.message}")

            except Exception as e:
                self.results.add_result(
                    'functional_tests',
                    f'密码认证-{description}',
                    False,
                    {'error': str(e)}
                )
                print(f"  {description}: [异常] - {str(e)}")

    def test_password_change(self):
        """测试密码修改功能"""
        print("\n=== 测试密码修改 ===")

        if not self.test_users:
            print("  没有测试用户，跳过密码修改测试")
            return

        username, old_password = self.test_users[0]
        new_password = "NewTest123456"

        test_cases = [
            (username, old_password, new_password, True, "正常修改密码"),
            (username, "WrongOld", new_password, False, "旧密码错误"),
            (username, old_password, "123", False, "新密码太短"),
            (username, old_password, old_password, False, "新旧密码相同"),
        ]

        for username, old_pwd, new_pwd, should_pass, description in test_cases:
            try:
                result = change_password(username, old_pwd, new_pwd)
                passed = result.success == should_pass

                self.results.add_result(
                    'functional_tests',
                    f'密码修改-{description}',
                    passed,
                    {
                        'username': username,
                        'expected': should_pass,
                        'actual': result.success,
                        'message': result.message
                    }
                )

                print(f"  {description}: {'[通过]' if passed else '[失败]'} - {result.message}")

                # 如果修改成功，更新测试用户密码
                if passed:
                    self.test_users[0] = (username, new_pwd)

            except Exception as e:
                self.results.add_result(
                    'functional_tests',
                    f'密码修改-{description}',
                    False,
                    {'error': str(e)}
                )
                print(f"  {description}: [异常] - {str(e)}")


class SecurityTests:
    """安全测试类"""

    def __init__(self):
        self.results = TestResults()

    def test_encryption_strength(self):
        """测试加密强度"""
        print("\n=== 测试加密强度 ===")

        # 测试PBKDF2
        test_password = "TestPassword123"
        test_salt = generate_salt(32)

        # 测试不同迭代次数的性能
        iterations_list = [1000, 10000, 100000, 200000]
        pbkdf2_times = []

        for iterations in iterations_list:
            start_time = time.time()
            key = derive_key_from_password(test_password, test_salt, iterations)
            end_time = time.time()

            elapsed = (end_time - start_time) * 1000  # 转换为毫秒
            pbkdf2_times.append(elapsed)

            print(f"  PBKDF2 {iterations:,} 次迭代: {elapsed:.2f}ms")

        # 测试AES-GCM加密
        test_key = load_or_init_data_key()
        test_data = "这是一段需要加密的测试数据，包含中文字符。This is test data for encryption.".encode('utf-8')

        encryption_times = []
        decryption_times = []

        for i in range(100):
            # 加密测试
            start_time = time.time()
            iv, ciphertext, tag = encrypt_aes_gcm(test_key, test_data)
            end_time = time.time()
            encryption_times.append((end_time - start_time) * 1000)

            # 解密测试
            start_time = time.time()
            decrypted = decrypt_aes_gcm(test_key, iv, ciphertext, tag)
            end_time = time.time()
            decryption_times.append((end_time - start_time) * 1000)

            # 验证解密正确性
            if decrypted != test_data:
                print(f"  [失败] 第{i+1}次解密失败！")
                break

        avg_encrypt = statistics.mean(encryption_times)
        avg_decrypt = statistics.mean(decryption_times)

        print(f"  AES-GCM 加密平均时间: {avg_encrypt:.3f}ms")
        print(f"  AES-GCM 解密平均时间: {avg_decrypt:.3f}ms")

        # 保存结果
        self.results.add_result(
            'security_tests',
            'PBKDF2性能测试',
            True,
            {
                'iterations_times': dict(zip(iterations_list, pbkdf2_times)),
                '200k_time': pbkdf2_times[-1]
            }
        )

        self.results.add_result(
            'security_tests',
            'AES-GCM性能测试',
            True,
            {
                'avg_encrypt_ms': avg_encrypt,
                'avg_decrypt_ms': avg_decrypt,
                'samples': len(encryption_times)
            }
        )

    def test_data_integrity(self):
        """测试数据完整性"""
        print("\n=== 测试数据完整性 ===")

        test_key = load_or_init_data_key()
        original_data = "重要的测试数据，不能被篡改".encode('utf-8')

        # 正常加密
        iv, ciphertext, tag = encrypt_aes_gcm(test_key, original_data)

        # 正常解密
        try:
            decrypted = decrypt_aes_gcm(test_key, iv, ciphertext, tag)
            integrity_ok = decrypted == original_data

            self.results.add_result(
                'security_tests',
                '正常加解密',
                integrity_ok,
                {'original': original_data.decode(), 'decrypted': decrypted.decode()}
            )
            print(f"  正常加解密: {'[通过]' if integrity_ok else '[失败]'}")
        except Exception as e:
            print(f"  正常加解密: [异常] - {str(e)}")

        # 篡改密文测试
        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 0x01  # 翻转第一个字节

        try:
            decrypt_aes_gcm(test_key, iv, bytes(tampered_ciphertext), tag)
            print("  篡改检测: [失败] 失败 - 应该检测到篡改")

            self.results.add_result(
                'security_tests',
                '篡改检测',
                False,
                {'error': '未能检测到密文篡改'}
            )
        except Exception as e:
            print("  篡改检测: [通过] 通过 - 成功检测到篡改")

            self.results.add_result(
                'security_tests',
                '篡改检测',
                True,
                {'detected': True, 'error_type': str(e)}
            )

        # 篡改标签测试
        tampered_tag = bytearray(tag)
        tampered_tag[0] ^= 0x01

        try:
            decrypt_aes_gcm(test_key, iv, ciphertext, bytes(tampered_tag))
            print("  标签篡改检测: [失败] 失败 - 应该检测到标签篡改")

            self.results.add_result(
                'security_tests',
                '标签篡改检测',
                False,
                {'error': '未能检测到标签篡改'}
            )
        except Exception as e:
            print("  标签篡改检测: [通过] 通过 - 成功检测到标签篡改")

            self.results.add_result(
                'security_tests',
                '标签篡改检测',
                True,
                {'detected': True, 'error_type': str(e)}
            )

    def test_password_security(self):
        """测试密码安全性"""
        print("\n=== 测试密码安全性 ===")

        # 测试盐值唯一性
        salts = []
        for i in range(100):
            salt = generate_salt(32)
            salts.append(salt)

        unique_salts = len(set(salts))
        salts_unique = unique_salts == len(salts)

        print(f"  盐值唯一性: 生成100个盐值，唯一{unique_salts}个")
        print(f"  盐值唯一性: {'[通过] 通过' if salts_unique else '[失败] 失败'}")

        self.results.add_result(
            'security_tests',
            '盐值唯一性',
            salts_unique,
            {
                'generated': len(salts),
                'unique': unique_salts,
                'uniqueness_rate': unique_salts / len(salts)
            }
        )

        # 测试相同密码不同盐值产生不同哈希
        password = "TestPassword123"
        hashes = []

        for i in range(10):
            salt = generate_salt(32)
            hash_value = derive_key_from_password(password, salt, 200000)
            hashes.append(hash_value)

        unique_hashes = len(set(hashes))
        hashes_unique = unique_hashes == len(hashes)

        print(f"  哈希唯一性: 相同密码10个不同盐值，唯一{unique_hashes}个哈希")
        print(f"  哈希唯一性: {'[通过] 通过' if hashes_unique else '[失败] 失败'}")

        self.results.add_result(
            'security_tests',
            '哈希唯一性',
            hashes_unique,
            {
                'password': password,
                'hashes_generated': len(hashes),
                'unique_hashes': unique_hashes
            }
        )


class PerformanceTests:
    """性能测试类"""

    def __init__(self):
        self.results = TestResults()

    def test_authentication_performance(self):
        """测试认证性能"""
        print("\n=== 测试认证性能 ===")

        # 创建测试用户
        test_username = f"perftest_{int(time.time())}"
        test_password = "PerfTest123456"

        register_result = register_user(test_username, test_password)
        if not register_result.success:
            print(f"  无法创建测试用户: {register_result.message}")
            return

        # 测试密码认证性能
        auth_times = []
        for i in range(100):
            start_time = time.time()
            result = authenticate_password_only(test_username, test_password)
            end_time = time.time()

            if result.success:
                auth_times.append((end_time - start_time) * 1000)
            else:
                print(f"  第{i+1}次认证失败: {result.message}")

        if auth_times:
            avg_time = statistics.mean(auth_times)
            min_time = min(auth_times)
            max_time = max(auth_times)
            p95 = statistics.quantiles(auth_times, n=20)[18]  # 95th percentile
            p99 = statistics.quantiles(auth_times, n=100)[98]  # 99th percentile

            print(f"  密码认证性能 ({len(auth_times)}次测试):")
            print(f"    平均时间: {avg_time:.2f}ms")
            print(f"    最小时间: {min_time:.2f}ms")
            print(f"    最大时间: {max_time:.2f}ms")
            print(f"    95%分位数: {p95:.2f}ms")
            print(f"    99%分位数: {p99:.2f}ms")

            self.results.add_result(
                'performance_tests',
                '密码认证性能',
                True,
                {
                    'samples': len(auth_times),
                    'avg_ms': avg_time,
                    'min_ms': min_time,
                    'max_ms': max_time,
                    'p95_ms': p95,
                    'p99_ms': p99
                }
            )

        # 测试数据加载性能
        load_times = []
        for i in range(50):
            start_time = time.time()
            repo = get_repository()
            repo.load_data(load_or_init_data_key())
            end_time = time.time()

            load_times.append((end_time - start_time) * 1000)

        avg_load = statistics.mean(load_times)
        print(f"  数据加载性能 ({len(load_times)}次测试):")
        print(f"    平均时间: {avg_load:.2f}ms")

        self.results.add_result(
            'performance_tests',
            '数据加载性能',
            True,
            {
                'samples': len(load_times),
                'avg_ms': avg_load
            }
        )

    def test_encryption_performance(self):
        """测试加密性能"""
        print("\n=== 测试加密性能 ===")

        test_key = load_or_init_data_key()

        # 测试不同大小数据的加密性能
        data_sizes = [1024, 10240, 102400, 1024000]  # 1KB, 10KB, 100KB, 1MB
        encryption_results = {}

        for size in data_sizes:
            test_data = os.urandom(size)
            encrypt_times = []
            decrypt_times = []

            for i in range(20):
                # 加密测试
                start_time = time.time()
                iv, ciphertext, tag = encrypt_aes_gcm(test_key, test_data)
                end_time = time.time()
                encrypt_times.append((end_time - start_time) * 1000)

                # 解密测试
                start_time = time.time()
                decrypted = decrypt_aes_gcm(test_key, iv, ciphertext, tag)
                end_time = time.time()
                decrypt_times.append((end_time - start_time) * 1000)

            avg_encrypt = statistics.mean(encrypt_times)
            avg_decrypt = statistics.mean(decrypt_times)

            encryption_results[f'{size}_bytes'] = {
                'avg_encrypt_ms': avg_encrypt,
                'avg_decrypt_ms': avg_decrypt,
                'throughput_mb_s': (size / 1024 / 1024) / (avg_encrypt / 1000) if avg_encrypt > 0 else 0
            }

            print(f"  {size//1024}KB 数据加密:")
            print(f"    加密: {avg_encrypt:.2f}ms ({(size/1024)/avg_encrypt:.2f} KB/ms)" if avg_encrypt > 0 else f"    加密: {avg_encrypt:.2f}ms (太快无法测量)")
            print(f"    解密: {avg_decrypt:.2f}ms ({(size/1024)/avg_decrypt:.2f} KB/ms)" if avg_decrypt > 0 else f"    解密: {avg_decrypt:.2f}ms (太快无法测量)")

        self.results.add_result(
            'performance_tests',
            '加密性能测试',
            True,
            encryption_results
        )


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("多因素身份验证系统 - 综合测试套件")
    print("=" * 60)

    # 创建测试结果目录
    test_results_dir = Path(__file__).parent / 'results'
    test_results_dir.mkdir(exist_ok=True)

    # 运行功能测试
    print("\n[功能测试] 运行功能测试...")
    functional_tests = FunctionalTests()
    functional_tests.test_user_registration()
    functional_tests.test_password_authentication()
    functional_tests.test_password_change()

    # 运行安全测试
    print("\n[安全测试] 运行安全测试...")
    security_tests = SecurityTests()
    security_tests.test_encryption_strength()
    security_tests.test_data_integrity()
    security_tests.test_password_security()

    # 运行性能测试
    print("\n[性能测试] 运行性能测试...")
    performance_tests = PerformanceTests()
    performance_tests.test_authentication_performance()
    performance_tests.test_encryption_performance()

    # 汇总结果
    all_results = TestResults()

    # 合并所有测试结果
    for test_class in [functional_tests, security_tests, performance_tests]:
        for category, tests in test_class.results.results.items():
            if category == 'test_summary':
                continue
            if category not in all_results.results:
                all_results.results[category] = {}
            all_results.results[category].update(tests)

    # 计算总体统计
    total_tests = 0
    total_passed = 0
    for category in ['functional_tests', 'security_tests', 'performance_tests']:
        if category in all_results.results:
            for test_name, test_result in all_results.results[category].items():
                total_tests += 1
                if test_result['passed']:
                    total_passed += 1

    all_results.results['test_summary'] = {
        'total_tests': total_tests,
        'passed': total_passed,
        'failed': total_tests - total_passed,
        'pass_rate': total_passed / total_tests if total_tests > 0 else 0,
        'timestamp': datetime.now().isoformat()
    }

    # 保存结果
    results_file = test_results_dir / f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    all_results.save_results(str(results_file))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_tests - total_passed}")
    print(f"通过率: {(total_passed/total_tests*100):.1f}%")
    print(f"结果已保存到: {results_file}")

    return all_results


if __name__ == "__main__":
    results = run_all_tests()