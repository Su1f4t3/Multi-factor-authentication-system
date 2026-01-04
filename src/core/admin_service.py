"""
管理员服务：用户管理、日志查看
"""
import sys
import base64
from pathlib import Path
from typing import List, Optional, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import ADMIN_KEY_PATH, AUTH_LOG_PATH, PBKDF2_ITERATIONS
from storage.file_repository import get_repository
from storage.models import User
from security.crypto import derive_key_from_password, generate_salt
from core.logging_service import get_recent_logs


class AdminLoginResult:
    """管理员登录结果"""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def init_admin_key(admin_password: str = "admin123"):
    """
    初始化管理员密钥文件
    
    Args:
        admin_password: 管理员密码（默认：admin123）
        
    Returns:
        是否成功
    """
    admin_key_path = Path(ADMIN_KEY_PATH)
    
    if admin_key_path.exists():
        print(f"[管理员服务] admin.key 已存在，跳过初始化")
        return False
    
    # 确保目录存在
    admin_key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成随机盐
    salt = generate_salt(32)
    
    # 使用PBKDF2计算管理员密码哈希
    password_hash = derive_key_from_password(
        admin_password,
        salt,
        PBKDF2_ITERATIONS
    )
    
    # 编码为Base64
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(password_hash).decode('ascii')
    
    # 写入文件：salt:hash格式
    with open(admin_key_path, 'w', encoding='utf-8') as f:
        f.write(f"{salt_b64}:{hash_b64}\n")
    
    print(f"[管理员服务] 已生成 admin.key，管理员密码: {admin_password}")
    return True


def admin_login(password: str) -> AdminLoginResult:
    """
    管理员登录验证
    
    Args:
        password: 管理员密码
        
    Returns:
        AdminLoginResult 登录结果
    """
    admin_key_path = Path(ADMIN_KEY_PATH)
    
    if not admin_key_path.exists():
        # 自动初始化
        print("[管理员服务] admin.key 不存在，自动初始化...")
        init_admin_key()
    
    try:
        # 读取admin.key
        with open(admin_key_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 解析 salt:hash 格式
        if ':' not in content:
            return AdminLoginResult(False, "admin.key 格式错误")
        
        salt_b64, stored_hash_b64 = content.split(':', 1)
        
        # 解码
        salt = base64.b64decode(salt_b64)
        stored_hash = base64.b64decode(stored_hash_b64)
        
        # 计算输入密码的哈希
        computed_hash = derive_key_from_password(
            password,
            salt,
            PBKDF2_ITERATIONS
        )
        
        # 比对哈希
        if computed_hash == stored_hash:
            print("[管理员服务] 管理员登录成功")
            return AdminLoginResult(True, "管理员登录成功")
        else:
            print("[管理员服务] 管理员密码错误")
            return AdminLoginResult(False, "管理员密码错误")
        
    except Exception as e:
        return AdminLoginResult(False, f"登录失败: {str(e)}")


def list_users() -> List[Dict]:
    """
    获取所有用户的基本信息
    
    Returns:
        用户信息字典列表
    """
    try:
        repo = get_repository()
        users = repo.get_all_users()
        
        user_list = []
        for user in users:
            user_info = {
                'id': user.id,
                'username': user.username,
                'face_enabled': user.face_enabled,
                'has_face_embedding': user.face_embedding is not None
            }
            user_list.append(user_info)
        
        print(f"[管理员服务] 获取到 {len(user_list)} 个用户")
        return user_list
        
    except Exception as e:
        print(f"[管理员服务] 获取用户列表失败: {e}")
        return []


def view_auth_logs(count: int = 50) -> List[str]:
    """
    查看认证日志
    
    Args:
        count: 返回的日志条数
        
    Returns:
        日志行列表
    """
    try:
        logs = get_recent_logs(count)
        print(f"[管理员服务] 获取到 {len(logs)} 条日志")
        return logs
    except Exception as e:
        print(f"[管理员服务] 读取日志失败: {e}")
        return []


def reset_user_face(username: str) -> bool:
    """
    重置用户的人脸数据
    
    Args:
        username: 用户名
        
    Returns:
        是否成功
    """
    try:
        repo = get_repository()
        
        # 查找用户
        user = repo.get_user_by_username(username)
        if user is None:
            print(f"[管理员服务] 用户 '{username}' 不存在")
            return False
        
        # 重置人脸数据
        user.face_enabled = False
        user.face_embedding = None
        
        # 保存更新
        repo.update_user(user)
        
        print(f"[管理员服务] 已重置用户 '{username}' 的人脸数据")
        return True
        
    except Exception as e:
        print(f"[管理员服务] 重置人脸失败: {e}")
        return False


def delete_user(username: str) -> bool:
    """
    删除用户
    
    Args:
        username: 用户名
        
    Returns:
        是否成功
    """
    try:
        repo = get_repository()
        repo.delete_user(username)
        print(f"[管理员服务] 已删除用户 '{username}'")
        return True
    except Exception as e:
        print(f"[管理员服务] 删除用户失败: {e}")
        return False


def get_system_statistics() -> Dict:
    """
    获取系统统计信息
    
    Returns:
        统计信息字典
    """
    try:
        repo = get_repository()
        users = repo.get_all_users()
        config = repo.get_system_config()
        
        face_enabled_count = sum(1 for u in users if u.face_enabled)
        
        stats = {
            'total_users': len(users),
            'face_enabled_users': face_enabled_count,
            'force_mfa': config.force_mfa,
            'face_threshold': config.face_threshold
        }
        
        return stats
        
    except Exception as e:
        print(f"[管理员服务] 获取统计信息失败: {e}")
        return {}
