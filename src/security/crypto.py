"""
密码学工具：PBKDF2、AES-GCM
"""
import hashlib
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Optional


def derive_key_from_password(
    password: str,
    salt: bytes,
    iterations: int = 200000
) -> bytes:
    """
    使用 PBKDF2-HMAC-SHA256 从密码派生密钥
    
    Args:
        password: 用户密码
        salt: 盐值（字节）
        iterations: 迭代次数，默认200000
        
    Returns:
        派生的32字节密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 输出32字节（256位）
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    
    # 将密码编码为字节并派生密钥
    key = kdf.derive(password.encode('utf-8'))
    return key


def encrypt_aes_gcm(
    key: bytes,
    plaintext: bytes,
    aad: Optional[bytes] = None
) -> Tuple[bytes, bytes, bytes]:
    """
    使用 AES-GCM 加密数据
    
    Args:
        key: 32字节的AES-256密钥
        plaintext: 要加密的明文
        aad: 附加认证数据（可选）
        
    Returns:
        (iv, ciphertext, tag) 元组
        - iv: 12字节的初始化向量/Nonce
        - ciphertext: 密文
        - tag: 16字节的认证标签
    """
    if len(key) != 32:
        raise ValueError("密钥长度必须为32字节（AES-256）")
    
    # 创建 AESGCM 实例
    aesgcm = AESGCM(key)
    
    # 生成随机12字节的 IV/Nonce
    iv = os.urandom(12)
    
    # 加密数据（AES-GCM会自动生成并附加tag）
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, aad)
    
    # AES-GCM 的输出格式是 ciphertext + tag（最后16字节）
    ciphertext = ciphertext_with_tag[:-16]
    tag = ciphertext_with_tag[-16:]
    
    return iv, ciphertext, tag


def decrypt_aes_gcm(
    key: bytes,
    iv: bytes,
    ciphertext: bytes,
    tag: bytes,
    aad: Optional[bytes] = None
) -> bytes:
    """
    使用 AES-GCM 解密数据
    
    Args:
        key: 32字节的AES-256密钥
        iv: 12字节的初始化向量
        ciphertext: 密文
        tag: 16字节的认证标签
        aad: 附加认证数据（可选，必须与加密时相同）
        
    Returns:
        解密后的明文
        
    Raises:
        cryptography.exceptions.InvalidTag: 如果认证标签验证失败（数据被篡改）
    """
    if len(key) != 32:
        raise ValueError("密钥长度必须为32字节（AES-256）")
    
    if len(iv) != 12:
        raise ValueError("IV长度必须为12字节")
    
    if len(tag) != 16:
        raise ValueError("Tag长度必须为16字节")
    
    # 创建 AESGCM 实例
    aesgcm = AESGCM(key)
    
    # 重新组合密文和标签
    ciphertext_with_tag = ciphertext + tag
    
    # 解密并验证（如果tag验证失败会抛出InvalidTag异常）
    plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, aad)
    
    return plaintext


def generate_salt(length: int = 32) -> bytes:
    """
    生成随机盐值
    
    Args:
        length: 盐值长度（字节），默认32
        
    Returns:
        随机盐值
    """
    return os.urandom(length)


def generate_random_key(length: int = 32) -> bytes:
    """
    生成随机密钥
    
    Args:
        length: 密钥长度（字节），默认32（AES-256）
        
    Returns:
        随机密钥
    """
    return os.urandom(length)
