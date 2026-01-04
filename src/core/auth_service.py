"""
用户认证服务：注册、登录、修改密码
"""
import sys
import base64
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import PBKDF2_ITERATIONS, SALT_LENGTH
from storage.file_repository import get_repository
from storage.models import User
from security.crypto import (
    derive_key_from_password,
    generate_salt
)
from core.logging_service import (
    log_user_registered,
    log_login_success,
    log_login_fail_password,
    log_login_fail_user_not_found,
    log_login_fail_face,
    log_password_changed
)
from security.face_recognizer import (
    capture_and_extract_face,
    capture_face_image,
    compute_distance,
    generate_mock_face_embedding,
    is_face_recognition_available,
    CV2_AVAILABLE,
    FaceRecognitionError
)


class AuthResult:
    """认证结果"""
    def __init__(self, success: bool, message: str, user: Optional[User] = None):
        self.success = success
        self.message = message
        self.user = user


def register_user(username: str, password: str) -> AuthResult:
    """
    注册新用户（简化版，不含人脸）
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        AuthResult 认证结果对象
    """
    try:
        # 参数验证
        if not username or not username.strip():
            return AuthResult(False, "用户名不能为空")
        
        if not password or len(password) < 6:
            return AuthResult(False, "密码长度至少6位")
        
        username = username.strip()
        
        # 获取仓库
        repo = get_repository()
        
        # 检查用户名是否已存在
        existing_user = repo.get_user_by_username(username)
        if existing_user is not None:
            return AuthResult(False, f"用户名 '{username}' 已存在")
        
        # 生成随机Salt
        salt = generate_salt(SALT_LENGTH)
        salt_b64 = base64.b64encode(salt).decode('ascii')
        
        # 使用PBKDF2派生密码哈希
        password_hash = derive_key_from_password(
            password,
            salt,
            PBKDF2_ITERATIONS
        )
        password_hash_b64 = base64.b64encode(password_hash).decode('ascii')
        
        # 创建用户对象
        user = User(
            username=username,
            salt=salt_b64,
            password_hash=password_hash_b64,
            face_enabled=False,
            face_embedding=None
        )
        
        # 保存到仓库
        repo.save_user(user)
        
        # 记录日志
        log_user_registered(username)
        
        return AuthResult(True, f"用户 '{username}' 注册成功", user)
        
    except Exception as e:
        return AuthResult(False, f"注册失败: {str(e)}")


def authenticate_password_only(username: str, password: str) -> AuthResult:
    """
    仅使用密码进行认证（单因素）
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        AuthResult 认证结果对象
    """
    try:
        # 参数验证
        if not username or not password:
            return AuthResult(False, "用户名和密码不能为空")
        
        username = username.strip()
        
        # 获取仓库
        repo = get_repository()
        
        # 查找用户
        user = repo.get_user_by_username(username)
        if user is None:
            log_login_fail_user_not_found(username)
            return AuthResult(False, "用户名或密码错误")  # 不泄露用户是否存在
        
        # 解码Salt
        salt = base64.b64decode(user.salt)
        
        # 使用相同参数计算密码哈希
        computed_hash = derive_key_from_password(
            password,
            salt,
            PBKDF2_ITERATIONS
        )
        computed_hash_b64 = base64.b64encode(computed_hash).decode('ascii')
        
        # 比对哈希值
        if computed_hash_b64 != user.password_hash:
            log_login_fail_password(username)
            return AuthResult(False, "用户名或密码错误")
        
        # 认证成功
        log_login_success(username)
        return AuthResult(True, f"用户 '{username}' 登录成功", user)
        
    except Exception as e:
        return AuthResult(False, f"认证失败: {str(e)}")


def verify_user_face_for_password_change(username: str) -> AuthResult:
    """
    为修改密码验证用户人脸

    Args:
        username: 用户名

    Returns:
        AuthResult 验证结果对象
    """
    try:
        # 获取仓库
        repo = get_repository()

        # 查找用户
        user = repo.get_user_by_username(username)
        if user is None:
            return AuthResult(False, "用户不存在")

        # 检查用户是否启用人脸
        if not user.face_enabled or not user.face_embedding:
            return AuthResult(False, "用户未启用人脸识别功能")

        print(f"[认证服务] 为用户 '{username}' 进行人脸验证以修改密码...")

        # 检查人脸识别是否可用
        available, message = is_face_recognition_available()
        if not available:
            return AuthResult(False, f"人脸识别不可用: {message}")

        try:
            # 启用预览窗口和检测结果显示
            current_embedding = capture_and_extract_face(
                show_preview=True,
                show_detection=True
            )
        except FaceRecognitionError as e:
            return AuthResult(False, f"人脸采集失败: {str(e)}")

        # 获取系统配置
        config = repo.get_system_config()
        threshold = config.face_threshold

        # 计算欧氏距离
        distance = compute_distance(user.face_embedding, current_embedding)

        print(f"[认证服务] 人脸距离: {distance:.4f}, 阈值: {threshold}")

        if distance <= threshold:
            # 人脸验证通过
            print(f"[认证服务] 用户 '{username}' 人脸验证通过")
            return AuthResult(True, f"用户 '{username}' 人脸验证通过", user)
        else:
            # 人脸验证失败
            print(f"[认证服务] 用户 '{username}' 人脸验证失败")
            return AuthResult(False, f"人脸验证失败 (距离={distance:.4f} > {threshold})")

    except Exception as e:
        return AuthResult(False, f"人脸验证失败: {str(e)}")


def change_password(username: str, old_password: str, new_password: str) -> AuthResult:
    """
    修改用户密码
    
    Args:
        username: 用户名
        old_password: 旧密码
        new_password: 新密码
        
    Returns:
        AuthResult 认证结果对象
    """
    try:
        # 参数验证
        if not username or not old_password or not new_password:
            return AuthResult(False, "所有字段都不能为空")
        
        if len(new_password) < 6:
            return AuthResult(False, "新密码长度至少6位")
        
        if old_password == new_password:
            return AuthResult(False, "新密码不能与旧密码相同")
        
        username = username.strip()
        
        # 先验证旧密码
        auth_result = authenticate_password_only(username, old_password)
        if not auth_result.success:
            return AuthResult(False, "旧密码验证失败")
        
        user = auth_result.user
        
        # 生成新的Salt
        new_salt = generate_salt(SALT_LENGTH)
        new_salt_b64 = base64.b64encode(new_salt).decode('ascii')
        
        # 计算新密码哈希
        new_password_hash = derive_key_from_password(
            new_password,
            new_salt,
            PBKDF2_ITERATIONS
        )
        new_password_hash_b64 = base64.b64encode(new_password_hash).decode('ascii')
        
        # 更新用户信息
        user.salt = new_salt_b64
        user.password_hash = new_password_hash_b64
        
        # 保存到仓库
        repo = get_repository()
        repo.update_user(user)
        
        # 记录日志
        log_password_changed(username)
        
        return AuthResult(True, f"用户 '{username}' 密码修改成功")
        
    except Exception as e:
        return AuthResult(False, f"修改密码失败: {str(e)}")


def register_user_with_face(username: str, password: str, use_mock: bool = False) -> AuthResult:
    """
    注册新用户并录入人脸
    
    Args:
        username: 用户名
        password: 密码
        use_mock: 是否使用模拟人脸数据（用于测试）
        
    Returns:
        AuthResult 认证结果对象
    """
    try:
        # 先执行基础注册（不含人脸）
        result = register_user(username, password)
        if not result.success:
            return result
        
        user = result.user
        
        # 捕获人脸特征
        print(f"[认证服务] 正在为用户 '{username}' 录入人脸...")
        
        # 检查人脸识别是否可用
        available, message = is_face_recognition_available()
        if not available:
            return AuthResult(False, f"人脸识别不可用: {message}")
        
        try:
            # 启用预览窗口和检测结果显示
            face_embedding = capture_and_extract_face(
                show_preview=True,
                show_detection=True
            )
        except FaceRecognitionError as e:
            return AuthResult(False, f"人脸采集失败: {str(e)}")
        
        # 更新用户信息
        user.face_enabled = True
        user.face_embedding = face_embedding
        
        # 保存到仓库
        repo = get_repository()
        repo.update_user(user)
        
        print(f"[认证服务] 用户 '{username}' 人脸录入成功")
        
        return AuthResult(True, f"用户 '{username}' 注册并录入人脸成功", user)
        
    except Exception as e:
        return AuthResult(False, f"注册失败: {str(e)}")


def authenticate_user(username: str, password: str, use_mock: bool = False) -> AuthResult:
    """
    用户认证（支持双因素）
    
    Args:
        username: 用户名
        password: 密码
        use_mock: 是否使用模拟人脸数据（用于测试）
        
    Returns:
        AuthResult 认证结果对象
    """
    try:
        # Factor 1: 口令验证
        print(f"[认证服务] 验证用户 '{username}' 的口令...")
        password_result = authenticate_password_only(username, password)
        
        if not password_result.success:
            # 口令验证失败，直接返回
            return password_result
        
        user = password_result.user
        
        # 获取系统配置
        repo = get_repository()
        config = repo.get_system_config()
        
        # 判断是否需要人脸验证
        if not config.force_mfa:
            # 仅密码模式
            print(f"[认证服务] 系统配置为仅密码模式，跳过人脸验证")
            return password_result
        
        # Factor 2: 人脸验证
        if not user.face_enabled or not user.face_embedding:
            # 用户未启用人脸验证
            print(f"[认证服务] 用户 '{username}' 未启用人脸验证")
            return AuthResult(False, "系统要求双因素认证，但用户未录入人脸")
        
        print(f"[认证服务] 验证用户 '{username}' 的人脸...")
        
        # 检查人脸识别是否可用
        available, message = is_face_recognition_available()
        if not available:
            return AuthResult(False, f"人脸识别不可用: {message}")
        
        try:
            # 启用预览窗口和检测结果显示
            current_embedding = capture_and_extract_face(
                show_preview=True,
                show_detection=True
            )
        except FaceRecognitionError as e:
            return AuthResult(False, f"人脸采集失败: {str(e)}")
        
        # 计算欧氏距离
        distance = compute_distance(user.face_embedding, current_embedding)
        threshold = config.face_threshold
        
        print(f"[认证服务] 人脸距离: {distance:.4f}, 阈值: {threshold}")
        
        if distance <= threshold:
            # 人脸验证通过
            print(f"[认证服务] 用户 '{username}' 双因素认证通过")
            # 注意：这里不再调用log_login_success，因为在password验证时已经记录了
            # 我们记录一个特别的双因素成功日志
            from core.logging_service import log_auth_event, AuthEvent
            log_auth_event(username, "MFA_SUCCESS", f"双因素认证成功 (距离={distance:.4f})")
            return AuthResult(True, f"用户 '{username}' 双因素认证成功", user)
        else:
            # 人脸验证失败
            print(f"[认证服务] 用户 '{username}' 人脸验证失败")
            log_login_fail_face(username)
            return AuthResult(False, f"人脸验证失败 (距离={distance:.4f} > {threshold})")
        
    except Exception as e:
        return AuthResult(False, f"认证失败: {str(e)}")


def verify_user_face_for_password_change(username: str) -> AuthResult:
    """
    为修改密码验证用户人脸

    Args:
        username: 用户名

    Returns:
        AuthResult 验证结果对象
    """
    try:
        # 获取仓库
        repo = get_repository()

        # 查找用户
        user = repo.get_user_by_username(username)
        if user is None:
            return AuthResult(False, "用户不存在")

        # 检查用户是否启用人脸
        if not user.face_enabled or not user.face_embedding:
            return AuthResult(False, "用户未启用人脸识别功能")

        print(f"[认证服务] 为用户 '{username}' 进行人脸验证以修改密码...")

        # 检查人脸识别是否可用
        available, message = is_face_recognition_available()
        if not available:
            return AuthResult(False, f"人脸识别不可用: {message}")

        try:
            # 启用预览窗口和检测结果显示
            current_embedding = capture_and_extract_face(
                show_preview=True,
                show_detection=True
            )
        except FaceRecognitionError as e:
            return AuthResult(False, f"人脸采集失败: {str(e)}")

        # 获取系统配置
        config = repo.get_system_config()
        threshold = config.face_threshold

        # 计算欧氏距离
        distance = compute_distance(user.face_embedding, current_embedding)

        print(f"[认证服务] 人脸距离: {distance:.4f}, 阈值: {threshold}")

        if distance <= threshold:
            # 人脸验证通过
            print(f"[认证服务] 用户 '{username}' 人脸验证通过")
            return AuthResult(True, f"用户 '{username}' 人脸验证通过", user)
        else:
            # 人脸验证失败
            print(f"[认证服务] 用户 '{username}' 人脸验证失败")
            return AuthResult(False, f"人脸验证失败 (距离={distance:.4f} > {threshold})")

    except Exception as e:
        return AuthResult(False, f"人脸验证失败: {str(e)}")
