"""
密钥管理：主密钥加载与管理
"""
import os
from pathlib import Path
from typing import Optional
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import DATA_KEY_PATH, AES_KEY_LENGTH
from security.crypto import generate_random_key


# 全局变量：缓存已加载的数据密钥
_cached_data_key: Optional[bytes] = None


def load_or_init_data_key() -> bytes:
    """
    加载或初始化数据加密密钥（data.key）
    
    工作流程：
    1. 如果 data.key 文件不存在：
       - 生成新的随机32字节密钥
       - 将密钥写入 data.key 文件
       - 返回密钥
    2. 如果 data.key 文件已存在：
       - 从文件读取密钥
       - 返回密钥
    3. 密钥会被缓存在内存中，避免重复文件读取
    
    Returns:
        32字节的AES-256密钥
        
    Raises:
        IOError: 如果文件读写失败
    """
    global _cached_data_key
    
    # 如果已经缓存，直接返回
    if _cached_data_key is not None:
        return _cached_data_key
    
    key_path = Path(DATA_KEY_PATH)
    
    # 确保data目录存在
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    if key_path.exists():
        # 从文件读取现有密钥
        with open(key_path, 'rb') as f:
            data_key = f.read()
        
        # 验证密钥长度
        if len(data_key) != AES_KEY_LENGTH:
            raise ValueError(
                f"data.key 文件损坏：期望{AES_KEY_LENGTH}字节，"
                f"实际{len(data_key)}字节"
            )
        
        print(f"[密钥管理器] 已从 {key_path} 加载数据密钥")
    else:
        # 生成新的随机密钥
        data_key = generate_random_key(AES_KEY_LENGTH)
        
        # 写入文件
        with open(key_path, 'wb') as f:
            f.write(data_key)
        
        print(f"[密钥管理器] 已生成新的数据密钥并保存到 {key_path}")
    
    # 缓存密钥
    _cached_data_key = data_key
    
    return data_key


def clear_cached_key():
    """
    清除内存中缓存的密钥
    
    用于程序退出时的安全清理
    """
    global _cached_data_key
    
    if _cached_data_key is not None:
        # 尝试覆写内存中的密钥数据
        _cached_data_key = None
        print("[密钥管理器] 已清除缓存的密钥")


def get_data_key() -> bytes:
    """
    获取数据加密密钥（便捷方法）
    
    Returns:
        32字节的AES-256密钥
    """
    return load_or_init_data_key()


def key_exists() -> bool:
    """
    检查 data.key 文件是否存在
    
    Returns:
        True 如果文件存在，否则 False
    """
    return Path(DATA_KEY_PATH).exists()
