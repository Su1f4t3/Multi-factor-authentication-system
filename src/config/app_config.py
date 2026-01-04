"""
应用全局配置
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 数据文件路径
DATA_BIN_PATH = DATA_DIR / "data.bin"
DATA_KEY_PATH = DATA_DIR / "data.key"
AUTH_LOG_PATH = DATA_DIR / "auth.log"
ADMIN_KEY_PATH = DATA_DIR / "admin.key"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 密码学配置
PBKDF2_ITERATIONS = 200000  # PBKDF2 迭代次数
PBKDF2_ALGORITHM = "sha256"  # PBKDF2 使用的哈希算法
SALT_LENGTH = 32  # Salt 长度（字节）
AES_KEY_LENGTH = 32  # AES-256 密钥长度（字节）
AES_IV_LENGTH = 12  # AES-GCM IV/Nonce 长度（字节）

# 人脸识别配置
DEFAULT_FACE_THRESHOLD = 0.3  # 距离阈值
# Face++: (100-confidence)/100，范围0-1，通常0.2-0.3为同一人（对应70-80%置信度）
FACE_EMBEDDING_SIZE = 128  # 人脸特征向量维度（仅用于兼容性，实际使用Face++ API）

# 算法信息
HASH_ALGORITHM = "PBKDF2-HMAC-SHA256"
ENCRYPTION_ALGORITHM = "AES-256-GCM"

# 系统配置
DEFAULT_FORCE_MFA = True  # 默认强制双因素认证
