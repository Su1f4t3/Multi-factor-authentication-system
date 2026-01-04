"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class User:
    """用户数据模型"""
    username: str
    salt: str  # Base64 编码的盐值
    password_hash: str  # Base64 编码的密码哈希
    face_enabled: bool = False
    face_embedding: Optional[List[float]] = None  # 128 维人脸特征向量
    face_image_data: Optional[bytes] = None  # 人脸图片二进制数据（用于Face++）
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        import base64
        return {
            'id': self.id,
            'username': self.username,
            'salt': self.salt,
            'password_hash': self.password_hash,
            'face_enabled': self.face_enabled,
            'face_embedding': self.face_embedding,
            'face_image_data': base64.b64encode(self.face_image_data).decode('utf-8') if self.face_image_data else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        import base64
        face_image_data = None
        if data.get('face_image_data'):
            try:
                face_image_data = base64.b64decode(data['face_image_data'])
            except Exception:
                face_image_data = None
        
        return cls(
            id=data.get('id'),
            username=data['username'],
            salt=data['salt'],
            password_hash=data['password_hash'],
            face_enabled=data.get('face_enabled', False),
            face_embedding=data.get('face_embedding'),
            face_image_data=face_image_data
        )


@dataclass
class SystemConfig:
    """系统配置数据模型"""
    force_mfa: bool = True  # 是否强制双因素认证
    face_threshold: float = 0.5  # 人脸识别欧氏距离阈值
    hash_algorithm: str = "PBKDF2-HMAC-SHA256"
    encryption_algorithm: str = "AES-256-GCM"
    pbkdf2_iterations: int = 200000
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'force_mfa': self.force_mfa,
            'face_threshold': self.face_threshold,
            'hash_algorithm': self.hash_algorithm,
            'encryption_algorithm': self.encryption_algorithm,
            'pbkdf2_iterations': self.pbkdf2_iterations
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SystemConfig':
        """从字典创建配置对象"""
        return cls(
            force_mfa=data.get('force_mfa', True),
            face_threshold=data.get('face_threshold', 0.5),
            hash_algorithm=data.get('hash_algorithm', "PBKDF2-HMAC-SHA256"),
            encryption_algorithm=data.get('encryption_algorithm', "AES-256-GCM"),
            pbkdf2_iterations=data.get('pbkdf2_iterations', 200000)
        )


@dataclass
class DataModel:
    """顶层数据模型"""
    version: int = 1
    users: List[User] = field(default_factory=list)
    config: SystemConfig = field(default_factory=SystemConfig)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'version': self.version,
            'users': [user.to_dict() for user in self.users],
            'config': self.config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DataModel':
        """从字典创建数据模型对象"""
        return cls(
            version=data.get('version', 1),
            users=[User.from_dict(u) for u in data.get('users', [])],
            config=SystemConfig.from_dict(data.get('config', {}))
        )
