"""
Face++ API 配置

注册账号获取API Key和Secret:
https://console.faceplusplus.com.cn/
"""

# Face++ API配置（请替换为你自己的Key和Secret）
FACEPP_API_KEY = "kVcKPEMfJi0gRxEAt6KHVkeUdzd3dug-"
FACEPP_API_SECRET = "ZDoNSZnhjM2xrwLULd8ACrLRvkb2W3TK"

# Face++ API端点
FACEPP_DETECT_URL = "https://api-cn.faceplusplus.com/facepp/v3/detect"
FACEPP_COMPARE_URL = "https://api-cn.faceplusplus.com/facepp/v3/compare"

# 启用Face++ API（如果配置了API Key）
USE_FACEPP = FACEPP_API_KEY != "your_api_key_here" and FACEPP_API_SECRET != "your_api_secret_here"
