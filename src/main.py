"""
多因素身份验证系统 - 主入口
"""
import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from security.key_manager import load_or_init_data_key, clear_cached_key
from storage.file_repository import get_repository
from gui.user_views import RegisterView, LoginView, ChangePasswordView
from gui.admin_views import AdminView
from gui.config_views import SecurityConfigView
from gui.ui_theme import StyleManager, ModernTheme, create_modern_label, create_card_frame


class MFAApp:
    """多因素身份验证系统主应用"""

    def __init__(self, root):
        self.root = root
        self.theme = ModernTheme()

        # 设置窗口属性
        self.root.title("多因素身份验证系统")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # 设置窗口居中
        self.center_window()

        # 初始化样式管理器
        self.style_manager = StyleManager(root)

        # 初始化数据
        self.init_data()

        # 当前登录的用户
        self.current_user = None

        # 创建主界面
        self.create_main_interface()
    
    def init_data(self):
        """初始化数据存储"""
        try:
            # 加载或生成数据密钥
            data_key = load_or_init_data_key()
            
            # 加载数据仓库
            self.repository = get_repository()
            self.repository.load_data(data_key)
            
            print("[主程序] 数据初始化完成")
            
        except Exception as e:
            print(f"[主程序] 数据初始化失败: {e}")
            import traceback
            traceback.print_exc()
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_main_interface(self):
        """创建主界面"""
        # 设置主窗口背景
        self.root.configure(bg=self.theme.COLORS['bg_main'])

        # 创建标题区域
        self.create_header()

        # 创建主内容区域
        self.create_content_area()

        # 创建底部状态栏
        self.create_status_bar()

    def create_header(self):
        """创建标题区域"""
        # 标题卡片框架
        header_frame = create_card_frame(self.root)
        header_frame.pack(fill=tk.X, padx=self.theme.SIZES['padding_large'],
                        pady=self.theme.SIZES['padding_medium'])

        # 主标题
        title_label = create_modern_label(
            header_frame,
            text="🔐 多因素身份验证系统",
            style='title',
            fg=self.theme.COLORS['primary']
        )
        title_label.pack(pady=(0, self.theme.SIZES['margin_small']))

        # 副标题
        subtitle_label = create_modern_label(
            header_frame,
            text="Multi-Factor Authentication System",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        )
        subtitle_label.pack()

        # 添加分割线
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(self.theme.SIZES['padding_medium'], 0))

    def create_content_area(self):
        """创建主内容区域"""
        # 内容框架
        content_frame = ttk.Frame(self.root, style='Modern.TFrame')
        content_frame.pack(fill='both', expand=True, padx=self.theme.SIZES['padding_large'],
                         pady=(0, self.theme.SIZES['padding_medium']))

        # 创建现代化选项卡
        self.notebook = ttk.Notebook(content_frame, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # 用户功能选项卡
        self.create_user_tabs()

    def create_user_tabs(self):
        """创建用户功能选项卡"""
        # 注册界面
        self.register_view = RegisterView(
            self.notebook,
            on_success=self.on_register_success
        )
        self.notebook.add(self.register_view, text="  用户注册  ")

        # 登录界面
        self.login_view = LoginView(
            self.notebook,
            on_success=self.on_login_success
        )
        self.notebook.add(self.login_view, text="  用户登录  ")

        # 修改密码界面
        self.change_password_view = ChangePasswordView(
            self.notebook,
            current_user=self.current_user
        )
        self.notebook.add(self.change_password_view, text="  修改密码  ")

        # 管理员界面
        self.admin_view = AdminView(self.notebook)
        self.notebook.add(self.admin_view, text="  系统管理  ")

        # 安全配置界面
        self.config_view = SecurityConfigView(self.notebook)
        self.notebook.add(self.config_view, text="  安全配置  ")

    def create_status_bar(self):
        """创建状态栏"""
        # 状态栏框架
        status_frame = create_card_frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=self.theme.SIZES['padding_large'],
                        pady=(0, self.theme.SIZES['padding_medium']))

        # 获取用户数量
        try:
            user_count = len(self.repository.get_all_users())
            status_text = f"🟢 系统就绪 | 👥 已加载 {user_count} 个用户 | 🐍 Python 3.12.6 | 🚀 现代化界面"
        except:
            status_text = "🟢 系统就绪 | 🐍 Python 3.12.6 | 🚀 现代化界面"

        # 状态标签
        self.status_label = create_modern_label(
            status_frame,
            text=status_text,
            style='caption',
            fg=self.theme.COLORS['text_secondary']
        )
        self.status_label.pack(fill=tk.X)
    
    def on_register_success(self):
        """注册成功回调"""
        # 更新用户数量
        try:
            user_count = len(self.repository.get_all_users())
            status_text = f"🟢 系统就绪 | 👥 已加载 {user_count} 个用户 | 🐍 Python 3.12.6 | 🚀 现代化界面"
            self.status_label.config(text=status_text)
        except:
            pass
    
    def on_login_success(self, username: str):
        """登录成功回调"""
        self.current_user = username
        # 更新修改密码界面的用户名
        self.change_password_view.set_current_user(username)
        # 切换到修改密码选项卡
        self.notebook.select(self.change_password_view)


def main():
    """主函数"""
    root = tk.Tk()
    app = MFAApp(root)
    
    # 设置退出时的清理函数
    def on_closing():
        print("[主程序] 正在退出...")
        clear_cached_key()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
