"""
安全配置管理
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.file_repository import get_repository
from storage.models import SystemConfig


def get_force_mfa() -> bool:
    """
    获取强制双因素认证开关状态
    
    Returns:
        是否强制双因素认证
    """
    repo = get_repository()
    config = repo.get_system_config()
    return config.force_mfa


def set_force_mfa(enabled: bool) -> bool:
    """
    设置强制双因素认证开关
    
    Args:
        enabled: 是否启用强制双因素认证
        
    Returns:
        是否成功
    """
    try:
        repo = get_repository()
        config = repo.get_system_config()
        
        old_value = config.force_mfa
        config.force_mfa = enabled
        repo.save_system_config(config)
        
        mode = "强制双因素" if enabled else "仅密码模式"
        print(f"[安全配置] force_mfa: {old_value} -> {enabled} ({mode})")
        return True
        
    except Exception as e:
        print(f"[安全配置] 设置失败: {e}")
        return False


def get_face_threshold() -> float:
    """
    获取人脸识别欧氏距离阈值
    
    Returns:
        当前阈值
    """
    repo = get_repository()
    config = repo.get_system_config()
    return config.face_threshold


def set_face_threshold(threshold: float) -> bool:
    """
    设置人脸识别欧氏距离阈值
    
    Args:
        threshold: 新的阈值（0.0 - 1.0）
        
    Returns:
        是否成功
    """
    try:
        if threshold < 0.0 or threshold > 1.0:
            print(f"[安全配置] 阈值范围错误: {threshold} (应在 0.0-1.0)")
            return False
        
        repo = get_repository()
        config = repo.get_system_config()
        
        old_value = config.face_threshold
        config.face_threshold = threshold
        repo.save_system_config(config)
        
        print(f"[安全配置] face_threshold: {old_value} -> {threshold}")
        return True
        
    except Exception as e:
        print(f"[安全配置] 设置失败: {e}")
        return False


def get_face_enabled_users_count() -> int:
    """
    统计启用人脸验证的用户数量
    
    Returns:
        启用人脸的用户数
    """
    try:
        repo = get_repository()
        users = repo.get_all_users()
        
        count = sum(1 for user in users if user.face_enabled)
        
        print(f"[安全配置] 启用人脸验证的用户数: {count}/{len(users)}")
        return count
        
    except Exception as e:
        print(f"[安全配置] 统计失败: {e}")
        return 0


def get_all_security_config() -> dict:
    """
    获取所有安全配置信息
    
    Returns:
        配置字典
    """
    try:
        repo = get_repository()
        config = repo.get_system_config()
        users = repo.get_all_users()
        
        face_enabled_count = sum(1 for user in users if user.face_enabled)
        
        config_dict = {
            'force_mfa': config.force_mfa,
            'face_threshold': config.face_threshold,
            'hash_algorithm': config.hash_algorithm,
            'encryption_algorithm': config.encryption_algorithm,
            'pbkdf2_iterations': config.pbkdf2_iterations,
            'total_users': len(users),
            'face_enabled_users': face_enabled_count
        }
        
        return config_dict
        
    except Exception as e:
        print(f"[安全配置] 获取配置失败: {e}")
        return {}


def display_security_config():
    """
    显示当前安全配置（便捷方法）
    """
    config = get_all_security_config()
    
    print("=" * 60)
    print("当前安全配置")
    print("=" * 60)
    
    mode = "强制双因素认证" if config.get('force_mfa') else "仅密码模式"
    print(f"认证模式: {mode}")
    print(f"人脸识别阈值: {config.get('face_threshold', 0.5)}")
    print(f"哈希算法: {config.get('hash_algorithm', 'N/A')}")
    print(f"加密算法: {config.get('encryption_algorithm', 'N/A')}")
    print(f"PBKDF2迭代次数: {config.get('pbkdf2_iterations', 0):,}")
    print(f"\n用户统计:")
    print(f"  总用户数: {config.get('total_users', 0)}")
    print(f"  启用人脸: {config.get('face_enabled_users', 0)}")
    print("=" * 60)
