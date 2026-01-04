"""
用户侧 GUI 视图
包含：注册、登录、修改密码界面
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.auth_service import (
    register_user_with_face,
    authenticate_user,
    change_password,
    register_user,
    verify_user_face_for_password_change
)
from src.core.security_config import get_force_mfa
from src.gui.ui_theme import (
    ModernTheme, StyleManager,
    create_modern_label, create_modern_button, create_modern_entry, create_card_frame
)


class RegisterView(tk.Frame):
    """用户注册界面"""

    def __init__(self, parent, on_success: Optional[Callable] = None):
        super().__init__(parent)
        self.theme = ModernTheme()
        self.on_success = on_success
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 设置背景
        self.configure(bg=self.theme.COLORS['bg_main'])

        # 创建主容器
        main_container = tk.Frame(self, bg=self.theme.COLORS['bg_main'])
        main_container.pack(expand=True, fill='both', padx=self.theme.SIZES['padding_large'],
                           pady=self.theme.SIZES['padding_large'])

        # 标题卡片
        title_card = create_card_frame(main_container)
        title_card.pack(fill='x', pady=(0, self.theme.SIZES['padding_medium']))

        # 标题
        title_label = create_modern_label(
            title_card,
            text="👤 新用户注册",
            style='title',
            fg=self.theme.COLORS['primary']
        )
        title_label.pack(pady=self.theme.SIZES['padding_small'])

        subtitle_label = create_modern_label(
            title_card,
            text="创建您的安全账户",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        )
        subtitle_label.pack()

        # 表单卡片
        form_card = create_card_frame(main_container)
        form_card.pack(fill='both', expand=True, pady=self.theme.SIZES['padding_small'])

        # 表单内容
        self._create_form_fields(form_card)

        # 按钮区域
        self._create_button_area(main_container)

        # 提示信息
        self._create_tips(main_container)

    def _create_form_fields(self, parent):
        """创建表单字段"""
        # 表单网格配置
        for i in range(5):
            parent.grid_rowconfigure(i, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # 用户名
        create_modern_label(
            parent,
            text="👤 用户名",
            style='body'
        ).grid(row=0, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.username_entry = create_modern_entry(parent, width=25)
        self.username_entry.grid(row=0, column=1, sticky='ew',
                                padx=(0, self.theme.SIZES['padding_large']),
                                pady=self.theme.SIZES['padding_medium'])

        # 密码
        create_modern_label(
            parent,
            text="🔒 密码",
            style='body'
        ).grid(row=1, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.password_entry = create_modern_entry(parent, width=25, show="*")
        self.password_entry.grid(row=1, column=1, sticky='ew',
                                padx=(0, self.theme.SIZES['padding_large']),
                                pady=self.theme.SIZES['padding_medium'])

        # 确认密码
        create_modern_label(
            parent,
            text="🔒 确认密码",
            style='body'
        ).grid(row=2, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.confirm_password_entry = create_modern_entry(parent, width=25, show="*")
        self.confirm_password_entry.grid(row=2, column=1, sticky='ew',
                                        padx=(0, self.theme.SIZES['padding_large']),
                                        pady=self.theme.SIZES['padding_medium'])

        # 人脸识别选项
        self.face_var = tk.BooleanVar(value=True)
        face_check_frame = tk.Frame(parent, bg=self.theme.COLORS['bg_card'])
        face_check_frame.grid(row=3, column=0, columnspan=2, pady=self.theme.SIZES['padding_medium'],
                             sticky='ew')

        # 使用现代化的复选框样式
        face_check = tk.Checkbutton(
            face_check_frame,
            text="📸 启用人脸识别 (推荐，更安全)",
            variable=self.face_var,
            bg=self.theme.COLORS['bg_card'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            selectcolor=self.theme.COLORS['bg_card'],
            activebackground=self.theme.COLORS['bg_card'],
            activeforeground=self.theme.COLORS['primary']
        )
        face_check.pack(anchor='w')

    def _create_button_area(self, parent):
        """创建按钮区域"""
        button_card = create_card_frame(parent)
        button_card.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        # 注册按钮
        register_btn = create_modern_button(
            button_card,
            text="✅ 立即注册",
            command=self._on_register,
            style='Success'
        )
        register_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 清空按钮
        clear_btn = create_modern_button(
            button_card,
            text="🔄 清空表单",
            command=self._clear_form,
            style='Warning'
        )
        clear_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

    def _create_tips(self, parent):
        """创建提示信息"""
        tips_card = create_card_frame(parent)
        tips_card.pack(fill='x', pady=(self.theme.SIZES['padding_small'], 0))

        tip_label = create_modern_label(
            tips_card,
            text="💡 启用人脸识别后，将在注册时录入人脸特征，请确保光线充足并正对摄像头",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        )
        tip_label.pack()
    
    def _on_register(self):
        """处理注册"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        enable_face = self.face_var.get()
        
        # 验证输入
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return
        
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return
        
        if len(password) < 6:
            messagebox.showerror("错误", "密码长度至少6个字符")
            return
        
        if password != confirm_password:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return
        
        # 执行注册
        try:
            if enable_face:
                messagebox.showinfo(
                    "提示",
                    "点击确定后将打开摄像头录入人脸\n请确保光线充足并正对摄像头"
                )
                result = register_user_with_face(username, password)
            else:
                result = register_user(username, password)
            
            if result.success:
                messagebox.showinfo("成功", f"用户 {username} 注册成功！")
                self._clear_form()
                if self.on_success:
                    self.on_success()
            else:
                messagebox.showerror("注册失败", result.message)
        
        except Exception as e:
            messagebox.showerror("错误", f"注册过程中发生错误：{str(e)}")
    
    def _clear_form(self):
        """清空表单"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)
        self.face_var.set(True)


class LoginView(tk.Frame):
    """用户登录界面"""

    def __init__(self, parent, on_success: Optional[Callable] = None):
        super().__init__(parent)
        self.theme = ModernTheme()
        self.on_success = on_success
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 设置背景
        self.configure(bg=self.theme.COLORS['bg_main'])

        # 创建主容器
        main_container = tk.Frame(self, bg=self.theme.COLORS['bg_main'])
        main_container.pack(expand=True, fill='both', padx=self.theme.SIZES['padding_large'],
                           pady=self.theme.SIZES['padding_large'])

        # 标题卡片
        title_card = create_card_frame(main_container)
        title_card.pack(fill='x', pady=(0, self.theme.SIZES['padding_medium']))

        # 标题
        title_label = create_modern_label(
            title_card,
            text="🔐 用户登录",
            style='title',
            fg=self.theme.COLORS['primary']
        )
        title_label.pack(pady=self.theme.SIZES['padding_small'])

        subtitle_label = create_modern_label(
            title_card,
            text="欢迎回来，请输入您的凭据",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        )
        subtitle_label.pack()

        # 表单卡片
        form_card = create_card_frame(main_container)
        form_card.pack(fill='both', expand=True, pady=self.theme.SIZES['padding_small'])

        # 表单内容
        self._create_login_fields(form_card)

        # 按钮区域
        self._create_login_buttons(main_container)

        # 状态信息
        self._create_status_area(main_container)

    def _create_login_fields(self, parent):
        """创建登录字段"""
        # 表单网格配置
        for i in range(3):
            parent.grid_rowconfigure(i, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # 用户名
        create_modern_label(
            parent,
            text="👤 用户名",
            style='body'
        ).grid(row=0, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_large'])

        self.username_entry = create_modern_entry(parent, width=25)
        self.username_entry.grid(row=0, column=1, sticky='ew',
                                padx=(0, self.theme.SIZES['padding_large']),
                                pady=self.theme.SIZES['padding_large'])

        # 密码
        create_modern_label(
            parent,
            text="🔒 密码",
            style='body'
        ).grid(row=1, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_large'])

        self.password_entry = create_modern_entry(parent, width=25, show="*")
        self.password_entry.grid(row=1, column=1, sticky='ew',
                                padx=(0, self.theme.SIZES['padding_large']),
                                pady=self.theme.SIZES['padding_large'])

        # 绑定回车键
        self.password_entry.bind('<Return>', lambda e: self._on_login())

    def _create_login_buttons(self, parent):
        """创建登录按钮"""
        button_card = create_card_frame(parent)
        button_card.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        # 登录按钮
        login_btn = create_modern_button(
            button_card,
            text="🚀 立即登录",
            command=self._on_login,
            style='Primary'
        )
        login_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 清空按钮
        clear_btn = create_modern_button(
            button_card,
            text="🔄 清空",
            command=self._clear_form,
            style='Warning'
        )
        clear_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

    def _create_status_area(self, parent):
        """创建状态区域"""
        status_card = create_card_frame(parent)
        status_card.pack(fill='x', pady=(self.theme.SIZES['padding_small'], 0))

        # 状态标签
        self.status_label = create_modern_label(
            status_card,
            text="",
            style='caption',
            fg=self.theme.COLORS['text_secondary']
        )
        self.status_label.pack()

        # 显示当前认证模式
        self._update_auth_mode_tip()

    def _update_auth_mode_tip(self):
        """更新认证模式提示"""
        try:
            force_mfa = get_force_mfa()
            if force_mfa:
                tip = "🔒 当前模式：强制双因素认证（密码 + 人脸）"
                color = self.theme.COLORS['info']
            else:
                tip = "✅ 当前模式：仅密码认证"
                color = self.theme.COLORS['success']

            self.status_label.config(text=tip, fg=color)
        except:
            self.status_label.config(text="", fg=self.theme.COLORS['text_secondary'])
    
    def _on_login(self):
        """处理登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # 验证输入
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return
        
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return
        
        # 执行登录
        try:
            # 检查是否需要人脸验证
            force_mfa = get_force_mfa()
            
            if force_mfa:
                messagebox.showinfo(
                    "提示",
                    "系统已启用双因素认证\n点击确定后将打开摄像头进行人脸验证"
                )
            
            result = authenticate_user(username, password)
            
            if result.success:
                messagebox.showinfo("登录成功", f"欢迎回来，{username}！")
                self._clear_form()
                if self.on_success:
                    self.on_success(username)
            else:
                messagebox.showerror("登录失败", result.message)
        
        except Exception as e:
            messagebox.showerror("错误", f"登录过程中发生错误：{str(e)}")
    
    def _clear_form(self):
        """清空表单"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)


class ChangePasswordView(tk.Frame):
    """修改密码界面"""

    def __init__(self, parent, current_user: Optional[str] = None):
        super().__init__(parent)
        self.theme = ModernTheme()
        self.current_user = current_user
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 设置背景
        self.configure(bg=self.theme.COLORS['bg_main'])

        # 创建主容器
        main_container = tk.Frame(self, bg=self.theme.COLORS['bg_main'])
        main_container.pack(expand=True, fill='both', padx=self.theme.SIZES['padding_large'],
                           pady=self.theme.SIZES['padding_large'])

        # 标题卡片
        title_card = create_card_frame(main_container)
        title_card.pack(fill='x', pady=(0, self.theme.SIZES['padding_medium']))

        # 标题
        title_label = create_modern_label(
            title_card,
            text="🔑 修改密码",
            style='title',
            fg=self.theme.COLORS['primary']
        )
        title_label.pack(pady=self.theme.SIZES['padding_small'])

        subtitle_label = create_modern_label(
            title_card,
            text="更新您的账户密码以保护安全",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        )
        subtitle_label.pack()

        # 表单卡片
        form_card = create_card_frame(main_container)
        form_card.pack(fill='both', expand=True, pady=self.theme.SIZES['padding_small'])

        # 表单内容
        self._create_form_fields(form_card)

        # 按钮区域
        self._create_button_area(main_container)

        # 提示信息
        self._create_tips(main_container)

    def _create_form_fields(self, parent):
        """创建表单字段"""
        # 表单网格配置
        for i in range(5):
            parent.grid_rowconfigure(i, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # 用户名
        create_modern_label(
            parent,
            text="👤 用户名",
            style='body'
        ).grid(row=0, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.username_entry = create_modern_entry(parent, width=25)
        if self.current_user:
            self.username_entry.insert(0, self.current_user)
            self.username_entry.config(state='readonly')
        self.username_entry.grid(row=0, column=1, sticky='ew',
                                padx=(0, self.theme.SIZES['padding_large']),
                                pady=self.theme.SIZES['padding_medium'])

        # 旧密码
        create_modern_label(
            parent,
            text="🔒 旧密码",
            style='body'
        ).grid(row=1, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.old_password_entry = create_modern_entry(parent, width=25, show="*")
        self.old_password_entry.grid(row=1, column=1, sticky='ew',
                                    padx=(0, self.theme.SIZES['padding_large']),
                                    pady=self.theme.SIZES['padding_medium'])

        # 新密码
        create_modern_label(
            parent,
            text="🔐 新密码",
            style='body'
        ).grid(row=2, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.new_password_entry = create_modern_entry(parent, width=25, show="*")
        self.new_password_entry.grid(row=2, column=1, sticky='ew',
                                    padx=(0, self.theme.SIZES['padding_large']),
                                    pady=self.theme.SIZES['padding_medium'])

        # 确认新密码
        create_modern_label(
            parent,
            text="🔐 确认新密码",
            style='body'
        ).grid(row=3, column=0, sticky='e', padx=(0, self.theme.SIZES['padding_medium']),
               pady=self.theme.SIZES['padding_medium'])

        self.confirm_password_entry = create_modern_entry(parent, width=25, show="*")
        self.confirm_password_entry.grid(row=3, column=1, sticky='ew',
                                        padx=(0, self.theme.SIZES['padding_large']),
                                        pady=self.theme.SIZES['padding_medium'])

        # 绑定回车键
        self.confirm_password_entry.bind('<Return>', lambda e: self._on_change_password())

    def _create_button_area(self, parent):
        """创建按钮区域"""
        button_card = create_card_frame(parent)
        button_card.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        # 修改按钮
        change_btn = create_modern_button(
            button_card,
            text="✅ 确认修改",
            command=self._on_change_password,
            style='Warning'
        )
        change_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 清空按钮
        clear_btn = create_modern_button(
            button_card,
            text="🔄 清空表单",
            command=self._clear_form,
            style='Primary'
        )
        clear_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

    def _create_tips(self, parent):
        """创建提示信息"""
        tips_card = create_card_frame(parent)
        tips_card.pack(fill='x', pady=(self.theme.SIZES['padding_small'], 0))

        tip_label = create_modern_label(
            tips_card,
            text="💡 修改密码后需要使用新密码重新登录",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        )
        tip_label.pack()
    
    def set_current_user(self, username: str):
        """设置当前用户"""
        self.current_user = username
        if hasattr(self, 'username_entry'):
            self.username_entry.config(state='normal')
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)
            self.username_entry.config(state='readonly')
    
    def _on_change_password(self):
        """处理修改密码"""
        username = self.username_entry.get().strip()
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # 验证输入
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return

        if not old_password:
            messagebox.showerror("错误", "请输入旧密码")
            return

        if not new_password:
            messagebox.showerror("错误", "请输入新密码")
            return

        if len(new_password) < 6:
            messagebox.showerror("错误", "新密码长度至少6个字符")
            return

        if new_password != confirm_password:
            messagebox.showerror("错误", "两次输入的新密码不一致")
            return

        if old_password == new_password:
            messagebox.showerror("错误", "新密码不能与旧密码相同")
            return

        # 显示人脸验证提示
        messagebox.showinfo(
            "提示",
            f"为了保护账户安全，修改密码前需要进行人脸验证\n\n用户：{username}\n\n点击确定后将打开摄像头进行人脸验证"
        )

        # 执行人脸验证
        try:
            result = verify_user_face_for_password_change(username)

            if result.success:
                # 人脸验证通过，直接执行密码修改
                try:
                    from src.core.auth_service import change_password
                    change_result = change_password(username, old_password, new_password)

                    if change_result.success:
                        messagebox.showinfo("✅ 修改成功", f"用户 {username} 的密码修改成功！\n\n请使用新密码重新登录。")
                        self._clear_form()
                    else:
                        messagebox.showerror("❌ 修改失败", change_result.message)

                except Exception as e:
                    messagebox.showerror("❌ 错误", f"修改密码过程中发生错误：{str(e)}")
            else:
                messagebox.showerror("人脸验证失败", result.message)

        except Exception as e:
            messagebox.showerror("错误", f"人脸验证过程中发生错误：{str(e)}")

        
    def _clear_form(self):
        """清空表单"""
        if not self.current_user:
            self.username_entry.delete(0, tk.END)
        self.old_password_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)


# 测试代码
if __name__ == "__main__":
    from src.security.key_manager import load_or_init_data_key
    from src.storage.file_repository import get_repository
    
    # 初始化数据
    data_key = load_or_init_data_key()
    repo = get_repository()
    repo.load_data(data_key)
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("用户界面测试")
    root.geometry("500x450")
    
    # 创建笔记本控件（选项卡）
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # 添加各个视图
    register_view = RegisterView(notebook)
    notebook.add(register_view, text="注册")
    
    login_view = LoginView(notebook)
    notebook.add(login_view, text="登录")
    
    change_password_view = ChangePasswordView(notebook)
    notebook.add(change_password_view, text="修改密码")
    
    root.mainloop()
