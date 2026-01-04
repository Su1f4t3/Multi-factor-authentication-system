"""
Face++ API 封装模块
"""
import requests
import base64
import sys
from pathlib import Path
from typing import Optional, Tuple, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.facepp_config import (
    FACEPP_API_KEY,
    FACEPP_API_SECRET,
    FACEPP_DETECT_URL,
    FACEPP_COMPARE_URL,
    USE_FACEPP
)


class FacePPError(Exception):
    """Face++ API异常"""
    pass


def image_to_base64(image_data: bytes) -> str:
    """
    将图像数据转换为base64字符串
    
    Args:
        image_data: 图像二进制数据
        
    Returns:
        base64编码的字符串
    """
    return base64.b64encode(image_data).decode('utf-8')


def detect_face_facepp(image_data: bytes, return_attributes: str = "none") -> dict:
    """
    使用Face++ API检测人脸
    
    Args:
        image_data: 图像二进制数据
        return_attributes: 需要返回的属性（如 "gender,age,smiling,headpose"）
        
    Returns:
        Face++ API返回的检测结果
        
    Raises:
        FacePPError: API调用失败
    """
    if not USE_FACEPP:
        raise FacePPError("Face++ API未配置，请在 facepp_config.py 中设置API Key和Secret")
    
    print(f"[Face++] 调用人脸检测API...")
    
    try:
        # 准备请求数据
        data = {
            'api_key': FACEPP_API_KEY,
            'api_secret': FACEPP_API_SECRET,
            'return_landmark': 0,
            'return_attributes': return_attributes
        }
        
        files = {
            'image_file': ('face.jpg', image_data, 'image/jpeg')
        }
        
        # 发送请求
        response = requests.post(FACEPP_DETECT_URL, data=data, files=files, timeout=10)
        result = response.json()
        
        # 检查错误
        if 'error_message' in result:
            raise FacePPError(f"Face++ API错误: {result['error_message']}")
        
        # 检查是否检测到人脸
        if not result.get('faces'):
            raise FacePPError("未检测到人脸")
        
        face_count = len(result['faces'])
        print(f"[Face++] 检测到 {face_count} 张人脸")
        
        return result
        
    except requests.RequestException as e:
        raise FacePPError(f"Face++ API请求失败: {str(e)}")
    except Exception as e:
        raise FacePPError(f"Face++处理失败: {str(e)}")


def compare_faces_facepp(image_data1: bytes, image_data2: bytes) -> Tuple[float, float]:
    """
    使用Face++ API比对两张人脸
    
    Args:
        image_data1: 第一张图像的二进制数据
        image_data2: 第二张图像的二进制数据
        
    Returns:
        (confidence, threshold): 相似度(0-100)和建议阈值
        
    Raises:
        FacePPError: API调用失败
    """
    if not USE_FACEPP:
        raise FacePPError("Face++ API未配置")
    
    print(f"[Face++] 调用人脸比对API...")
    
    try:
        # 准备请求数据
        data = {
            'api_key': FACEPP_API_KEY,
            'api_secret': FACEPP_API_SECRET
        }
        
        files = {
            'image_file1': ('face1.jpg', image_data1, 'image/jpeg'),
            'image_file2': ('face2.jpg', image_data2, 'image/jpeg')
        }
        
        # 发送请求
        response = requests.post(FACEPP_COMPARE_URL, data=data, files=files, timeout=10)
        result = response.json()
        
        # 检查错误
        if 'error_message' in result:
            raise FacePPError(f"Face++ API错误: {result['error_message']}")
        
        confidence = result.get('confidence', 0)
        threshold = result.get('thresholds', {}).get('1e-3', 70.0)  # 千分之一误识率的阈值
        
        print(f"[Face++] 相似度: {confidence:.2f}, 建议阈值: {threshold:.2f}")
        
        return confidence, threshold
        
    except requests.RequestException as e:
        raise FacePPError(f"Face++ API请求失败: {str(e)}")
    except Exception as e:
        raise FacePPError(f"Face++处理失败: {str(e)}")


def extract_face_token(image_data: bytes) -> str:
    """
    提取人脸token（用于后续比对）
    
    Args:
        image_data: 图像二进制数据
        
    Returns:
        Face token字符串
        
    Raises:
        FacePPError: API调用失败
    """
    result = detect_face_facepp(image_data)
    
    if not result.get('faces'):
        raise FacePPError("未检测到人脸")
    
    face_token = result['faces'][0].get('face_token')
    
    if not face_token:
        raise FacePPError("无法获取face token")
    
    print(f"[Face++] Face token: {face_token[:20]}...")
    
    return face_token


def get_face_rectangle(image_data: bytes) -> Optional[dict]:
    """
    获取人脸矩形框位置
    
    Args:
        image_data: 图像二进制数据
        
    Returns:
        包含 top, left, width, height 的字典，如果没有检测到返回None
    """
    try:
        result = detect_face_facepp(image_data)
        
        if not result.get('faces'):
            return None
        
        face = result['faces'][0]
        rect = face.get('face_rectangle', {})
        
        return {
            'top': rect.get('top', 0),
            'left': rect.get('left', 0),
            'width': rect.get('width', 0),
            'height': rect.get('height', 0)
        }
        
    except Exception:
        return None


# 测试函数
if __name__ == "__main__":
    print(f"Face++ 配置状态: {'已配置' if USE_FACEPP else '未配置'}")
    
    if USE_FACEPP:
        print(f"API Key: {FACEPP_API_KEY[:10]}...")
        print("Face++ API可以使用")
    else:
        print("请在 facepp_config.py 中配置API Key和Secret")
        print("注册地址: https://console.faceplusplus.com.cn/")
