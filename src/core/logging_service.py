"""
认证日志服务
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import AUTH_LOG_PATH


class AuthEvent:
    """认证事件类型"""
    SUCCESS = "SUCCESS"
    FAIL_WRONG_PASSWORD = "FAIL_WRONG_PASSWORD"
    FAIL_USER_NOT_FOUND = "FAIL_USER_NOT_FOUND"
    FAIL_FACE_MISMATCH = "FAIL_FACE_MISMATCH"
    FAIL_DATA_INTEGRITY = "FAIL_DATA_INTEGRITY"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    USER_REGISTERED = "USER_REGISTERED"


def log_auth_event(username: str, result: str, reason: str = ""):
    """
    记录认证事件到日志文件
    
    Args:
        username: 用户名（或匿名标识）
        result: 结果类型（SUCCESS/FAIL等）
        reason: 详细原因（可选）
    """
    # 确保日志目录存在
    log_path = Path(AUTH_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 格式化时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构建日志条目
    log_entry = f"{timestamp}  username={username}  result={result}"
    if reason:
        log_entry += f"  reason={reason}"
    
    # 追加到日志文件
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')
    
    # 同时打印到控制台（方便调试）
    print(f"[认证日志] {log_entry}")


def log_login_success(username: str):
    """记录登录成功"""
    log_auth_event(username, AuthEvent.SUCCESS, "登录成功")


def log_login_fail_password(username: str):
    """记录口令错误"""
    log_auth_event(username, AuthEvent.FAIL_WRONG_PASSWORD, "口令错误")


def log_login_fail_user_not_found(username: str):
    """记录用户不存在"""
    log_auth_event(username, AuthEvent.FAIL_USER_NOT_FOUND, "用户不存在")


def log_login_fail_face(username: str):
    """记录人脸验证失败"""
    log_auth_event(username, AuthEvent.FAIL_FACE_MISMATCH, "人脸比对失败")


def log_data_integrity_error(username: str = "SYSTEM"):
    """记录数据完整性错误"""
    log_auth_event(username, AuthEvent.FAIL_DATA_INTEGRITY, "数据完整性校验失败")


def log_password_changed(username: str):
    """记录密码修改"""
    log_auth_event(username, AuthEvent.PASSWORD_CHANGED, "密码已修改")


def log_user_registered(username: str):
    """记录用户注册"""
    log_auth_event(username, AuthEvent.USER_REGISTERED, "用户注册成功")


def get_recent_logs(count: int = 50) -> list:
    """
    获取最近的日志记录
    
    Args:
        count: 返回的日志条数
        
    Returns:
        日志行列表
    """
    log_path = Path(AUTH_LOG_PATH)
    
    if not log_path.exists():
        return []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 返回最后N条
    return lines[-count:] if len(lines) > count else lines


def clear_logs():
    """清空日志文件（仅用于测试）"""
    log_path = Path(AUTH_LOG_PATH)
    if log_path.exists():
        log_path.unlink()
        print("[认证日志] 日志文件已清空")
