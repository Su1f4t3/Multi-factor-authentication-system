# 多因素身份验证系统（课程设计）

本项目为本人课程设计作业（海南大学，密码科学与技术专业，《网络安全与系统》课程）。

本项目是一个基于 **Tkinter GUI** 的多因素身份验证（MFA）演示系统，包含用户注册/登录/修改密码、管理员管理与安全策略配置等功能，并支持“密码 + 人脸（Face++）”的双因素认证流程。

> 适用环境：Windows + Python 3.12（项目界面状态栏默认展示 3.12.6）。

## 主要功能

- 用户注册：用户名 + 密码；可选开启人脸录入
- 用户登录：密码验证；在系统开启强制 MFA 时增加人脸验证
- 修改密码：在强制 MFA 场景下需先做人脸验证
- 系统管理：查看/管理用户等（见管理员页签）
- 安全配置：开启/关闭强制 MFA 等（见“安全配置”页签）
- 本地加密存储：用户与配置数据加密保存到 `data/data.bin`

## 技术与安全要点（实现概览）

- 密码哈希：PBKDF2-HMAC-SHA256（迭代次数在 [src/config/app_config.py](src/config/app_config.py) 中配置）
- 数据加密：AES-256-GCM（带完整性校验，篡改会触发 `InvalidTag`）
- 人脸能力：
  - 摄像头采集依赖 OpenCV（`opencv-python`）
  - 人脸检测/比对调用 Face++ 云 API（需要联网与 API Key/Secret）

## 目录结构

- [src/main.py](src/main.py)：程序入口（启动 Tkinter 主窗口与各页签）
- [src/gui/](src/gui/)：界面层（注册/登录/管理/配置等视图）
- [src/core/](src/core/)：业务逻辑（认证流程、管理员服务、安全配置等）
- [src/security/](src/security/)：密码学与人脸识别封装（AES-GCM、PBKDF2、Face++、摄像头采集等）
- [src/storage/](src/storage/)：数据模型与文件仓库（加密读写 `data.bin`）
- [data/](data/)：运行时数据目录（首次运行自动创建）
- [security_tools/](security_tools/)：安全性自检脚本（加密/PBKDF2 验证）
- [tests/](tests/)：综合测试与渗透测试脚本（会生成 JSON 结果）

## 安装与运行（Windows）

### 1) 创建虚拟环境（推荐）

在项目根目录打开 PowerShell：

- 创建 venv：`py -3.12 -m venv .venv`
- 激活 venv：`.\.venv\Scripts\Activate.ps1`

### 2) 安装依赖

本项目除标准库外，主要依赖：

- `cryptography`：AES-GCM 等密码学能力
- `requests`：调用 Face++ API
- `numpy`：人脸模块中使用
- `opencv-python`：摄像头采集与图像编码（启用人脸流程时需要）

安装命令：

- `pip install cryptography requests numpy opencv-python`

> 说明：如果你不打算使用摄像头/人脸功能，也可以不装 `opencv-python`，但勾选“启用人脸识别”或强制 MFA 时会提示无法使用摄像头。

### 3) 配置 Face++（可选，但启用人脸功能必须）

Face++ Key/Secret 配置在 [src/config/facepp_config.py](src/config/facepp_config.py)。

- 到 Face++ 控制台申请：`https://console.faceplusplus.com.cn/`
- 将配置文件中的 `FACEPP_API_KEY` / `FACEPP_API_SECRET` 替换为你自己的


### 4) 启动程序

- `py -3.12 src\main.py`

启动后可在顶部页签中使用：用户注册 / 用户登录 / 修改密码 / 系统管理 / 安全配置。

## 数据文件说明

程序会在 [data/](data/) 下生成/使用以下文件（首次运行自动创建目录）：

- `data.bin`：加密后的业务数据（用户、系统配置等）
- `data.key`：数据加密密钥（由系统生成并持久化）
- `auth.log`：认证日志（如果启用/写入）
- `admin.key`：管理员相关密钥/标识（如有）

> 如果 `data.bin` 被外部篡改，解密时会触发完整性校验失败（AES-GCM 的 `InvalidTag`）。

## 测试（脚本方式）

本项目的测试在 [tests/](tests/) 下以“可直接运行的脚本”形式提供（非 pytest/unittest 入口）。

- 综合测试：`py -3.12 tests\test_comprehensive.py`
- 渗透测试：`py -3.12 tests\test_penetration.py`

测试结果会输出到 [tests/results/](tests/results/) 的 JSON 文件中。

## 常见问题

- 摄像头打不开/提示 OpenCV 未安装：安装 `opencv-python`，并确认系统相机权限已开启。
- 人脸功能不可用：需要联网，并正确配置 Face++ Key/Secret。
- 第一次运行没有数据：正常，系统会初始化空数据并生成加密文件。
