"""
文件存储仓库：data.bin 读写
"""
import json
import base64
from pathlib import Path
from typing import Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.app_config import DATA_BIN_PATH
from storage.models import User, SystemConfig, DataModel
from storage.schema_migration import SchemaMigration
from security.crypto import encrypt_aes_gcm, decrypt_aes_gcm
from cryptography.exceptions import InvalidTag


class FileRepository:
    """文件存储仓库，负责管理 data.bin 的加密读写"""
    
    def __init__(self):
        """初始化仓库"""
        self._data_model: Optional[DataModel] = None
        self._data_key: Optional[bytes] = None
        self._next_user_id = 1
    
    def load_data(self, data_key: bytes):
        """
        加载数据文件
        
        Args:
            data_key: 32字节的数据加密密钥
            
        Raises:
            InvalidTag: 如果数据完整性校验失败
        """
        self._data_key = data_key
        data_path = Path(DATA_BIN_PATH)
        
        if not data_path.exists():
            # 首次运行，初始化空数据结构
            print(f"[文件仓库] data.bin 不存在，初始化新的数据结构")
            self._data_model = DataModel(
                version=1,
                users=[],
                config=SystemConfig()
            )
            self.save_data()
        else:
            # 从文件加载并解密
            print(f"[文件仓库] 从 {data_path} 加载数据")
            
            with open(data_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 解析加密数据结构
            # 格式：iv(12字节) + ciphertext + tag(16字节)
            if len(encrypted_data) < 28:  # 至少需要 12 + 0 + 16
                raise ValueError("data.bin 文件格式错误：文件太小")
            
            iv = encrypted_data[:12]
            tag = encrypted_data[-16:]
            ciphertext = encrypted_data[12:-16]
            
            try:
                # 解密数据
                plaintext = decrypt_aes_gcm(data_key, iv, ciphertext, tag)
                
                # 反序列化 JSON
                json_text = plaintext.decode('utf-8')
                data_dict = json.loads(json_text)
                
                # 执行版本迁移（如果需要）
                data_dict = SchemaMigration.migrate(data_dict)
                
                # 构造数据模型
                self._data_model = DataModel.from_dict(data_dict)
                
                # 计算下一个用户ID
                if self._data_model.users:
                    max_id = max(u.id for u in self._data_model.users if u.id)
                    self._next_user_id = max_id + 1
                
                print(f"[文件仓库] 成功加载 {len(self._data_model.users)} 个用户")
                
            except InvalidTag:
                print("[文件仓库] 错误：数据完整性校验失败！data.bin 可能已被篡改")
                raise
    
    def save_data(self):
        """
        保存数据到文件
        
        Raises:
            ValueError: 如果数据未初始化
        """
        if self._data_model is None:
            raise ValueError("数据模型未初始化")
        
        if self._data_key is None:
            raise ValueError("数据密钥未设置")
        
        # 序列化为 JSON
        data_dict = self._data_model.to_dict()
        json_text = json.dumps(data_dict, ensure_ascii=False, indent=2)
        plaintext = json_text.encode('utf-8')
        
        # 加密数据
        iv, ciphertext, tag = encrypt_aes_gcm(self._data_key, plaintext)
        
        # 组合为：iv + ciphertext + tag
        encrypted_data = iv + ciphertext + tag
        
        # 确保目录存在
        data_path = Path(DATA_BIN_PATH)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(data_path, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"[文件仓库] 数据已保存到 {data_path}")
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名查找用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象，如果不存在则返回 None
        """
        if self._data_model is None:
            return None
        
        for user in self._data_model.users:
            if user.username == username:
                return user
        
        return None
    
    def get_all_users(self) -> List[User]:
        """
        获取所有用户
        
        Returns:
            用户列表
        """
        if self._data_model is None:
            return []
        
        return self._data_model.users.copy()
    
    def save_user(self, user: User):
        """
        保存新用户
        
        Args:
            user: 用户对象
            
        Raises:
            ValueError: 如果用户名已存在
        """
        if self._data_model is None:
            raise ValueError("数据模型未初始化")
        
        # 检查用户名是否已存在
        existing_user = self.get_user_by_username(user.username)
        if existing_user is not None:
            raise ValueError(f"用户名 '{user.username}' 已存在")
        
        # 分配ID
        if user.id is None:
            user.id = self._next_user_id
            self._next_user_id += 1
        
        # 添加到列表
        self._data_model.users.append(user)
        
        # 保存到文件
        self.save_data()
        
        print(f"[文件仓库] 已保存用户: {user.username} (ID: {user.id})")
    
    def update_user(self, user: User):
        """
        更新用户信息
        
        Args:
            user: 用户对象
            
        Raises:
            ValueError: 如果用户不存在
        """
        if self._data_model is None:
            raise ValueError("数据模型未初始化")
        
        # 查找用户
        for i, existing_user in enumerate(self._data_model.users):
            if existing_user.username == user.username:
                # 更新用户
                self._data_model.users[i] = user
                self.save_data()
                print(f"[文件仓库] 已更新用户: {user.username}")
                return
        
        raise ValueError(f"用户 '{user.username}' 不存在")
    
    def delete_user(self, username: str):
        """
        删除用户
        
        Args:
            username: 用户名
            
        Raises:
            ValueError: 如果用户不存在
        """
        if self._data_model is None:
            raise ValueError("数据模型未初始化")
        
        # 查找并删除用户
        for i, user in enumerate(self._data_model.users):
            if user.username == username:
                del self._data_model.users[i]
                self.save_data()
                print(f"[文件仓库] 已删除用户: {username}")
                return
        
        raise ValueError(f"用户 '{username}' 不存在")
    
    def get_system_config(self) -> SystemConfig:
        """
        获取系统配置
        
        Returns:
            系统配置对象
        """
        if self._data_model is None:
            return SystemConfig()
        
        return self._data_model.config
    
    def save_system_config(self, config: SystemConfig):
        """
        保存系统配置
        
        Args:
            config: 系统配置对象
        """
        if self._data_model is None:
            raise ValueError("数据模型未初始化")
        
        self._data_model.config = config
        self.save_data()
        print(f"[文件仓库] 已保存系统配置")


# 全局单例
_repository_instance: Optional[FileRepository] = None


def get_repository() -> FileRepository:
    """
    获取文件仓库单例
    
    Returns:
        FileRepository 实例
    """
    global _repository_instance
    
    if _repository_instance is None:
        _repository_instance = FileRepository()
    
    return _repository_instance
