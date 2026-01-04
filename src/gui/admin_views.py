"""
管理员界面：用户管理、日志查看
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, simpledialog
from typing import Callable, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.admin_service import (
    admin_login,
    list_users,
    view_auth_logs,
    reset_user_face,
    delete_user,
    get_system_statistics
)
from src.gui.ui_theme import (
    ModernTheme, StyleManager,
    create_modern_label, create_modern_button, create_modern_entry, create_card_frame
)


class AdminLoginDialog(tk.Toplevel):
    """管理员登录对话框"""

    def __init__(self, parent, on_success: Optional[Callable] = None):
        super().__init__(parent)
        self.theme = ModernTheme()
        self.on_success = on_success
        self.result = False

        self.title("🛡️ 管理员登录")
        self.geometry("450x300")
        self.resizable(False, False)

        # 设置窗口背景
        self.configure(bg=self.theme.COLORS['bg_main'])

        # 居中显示
        self.transient(parent)
        self.grab_set()

        self._init_ui()

        # 窗口居中
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _init_ui(self):
        """初始化界面"""
        # 主容器
        main_container = tk.Frame(self, bg=self.theme.COLORS['bg_main'])
        main_container.pack(expand=True, fill='both', padx=self.theme.SIZES['padding_large'],
                           pady=self.theme.SIZES['padding_large'])

        # 标题卡片
        title_card = create_card_frame(main_container)
        title_card.pack(fill='x', pady=(0, self.theme.SIZES['padding_medium']))

        # 标题
        title_label = create_modern_label(
            title_card,
            text="🛡️ 管理员身份验证",
            style='subtitle',
            fg=self.theme.COLORS['primary']
        )
        title_label.pack(pady=self.theme.SIZES['padding_small'])

        subtitle_label = create_modern_label(
            title_card,
            text="请输入管理员密码以访问系统管理功能",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        )
        subtitle_label.pack()

        # 表单卡片
        form_card = create_card_frame(main_container)
        form_card.pack(fill='both', expand=True, pady=self.theme.SIZES['padding_small'])

        # 密码输入
        create_modern_label(
            form_card,
            text="🔑 管理员密码",
            style='body'
        ).pack(pady=(self.theme.SIZES['padding_medium'], self.theme.SIZES['padding_small']))

        self.password_entry = create_modern_entry(form_card, width=25, show="*")
        self.password_entry.pack(pady=self.theme.SIZES['padding_small'])
        self.password_entry.focus()

        # 绑定回车键
        self.password_entry.bind('<Return>', lambda e: self._on_login())

        # 按钮区域
        button_card = create_card_frame(main_container)
        button_card.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        # 登录按钮
        login_btn = create_modern_button(
            button_card,
            text="🔓 验证身份",
            command=self._on_login,
            style='Primary'
        )
        login_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 取消按钮
        cancel_btn = create_modern_button(
            button_card,
            text="❌ 取消",
            command=self.destroy,
            style='Danger'
        )
        cancel_btn.pack(side='left', padx=self.theme.SIZES['padding_small'])
    
    def _on_login(self):
        """处理登录"""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showerror("错误", "请输入管理员密码", parent=self)
            return
        
        # 执行登录
        result = admin_login(password)
        
        if result.success:
            self.result = True
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            messagebox.showerror("登录失败", result.message, parent=self)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()


class AdminView(tk.Frame):
    """管理员界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.is_logged_in = False
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建登录提示界面
        self.login_frame = tk.Frame(self)
        self.login_frame.pack(expand=True, fill='both')
        
        tk.Label(
            self.login_frame,
            text="管理员功能",
            font=("Arial", 16, "bold")
        ).pack(pady=30)
        
        tk.Label(
            self.login_frame,
            text="需要管理员权限才能访问",
            font=("Arial", 12),
            fg="gray"
        ).pack(pady=10)
        
        login_btn = tk.Button(
            self.login_frame,
            text="管理员登录",
            command=self._show_login_dialog,
            width=15,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold")
        )
        login_btn.pack(pady=20)
        
        # 创建管理界面（初始隐藏）
        self.admin_frame = tk.Frame(self)
        self._create_admin_interface()
    
    def _show_login_dialog(self):
        """显示登录对话框"""
        dialog = AdminLoginDialog(self, on_success=self._on_login_success)
        self.wait_window(dialog)
    
    def _on_login_success(self):
        """登录成功回调"""
        self.is_logged_in = True
        self.login_frame.pack_forget()
        self.admin_frame.pack(expand=True, fill='both')
        self._refresh_user_list()
        self._refresh_statistics()
    
    def _create_admin_interface(self):
        """创建管理界面"""
        # 标题
        title_frame = tk.Frame(self.admin_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            title_frame,
            text="管理员控制面板",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)
        
        logout_btn = tk.Button(
            title_frame,
            text="退出登录",
            command=self._logout,
            width=10
        )
        logout_btn.pack(side=tk.RIGHT)
        
        # 创建Notebook（选项卡）
        notebook = ttk.Notebook(self.admin_frame)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 用户管理选项卡
        self.user_tab = tk.Frame(notebook)
        notebook.add(self.user_tab, text="  用户管理  ")
        self._create_user_management_tab()
        
        # 日志查看选项卡
        self.log_tab = tk.Frame(notebook)
        notebook.add(self.log_tab, text="  日志查看  ")
        self._create_log_viewer_tab()
        
        # 统计信息选项卡
        self.stats_tab = tk.Frame(notebook)
        notebook.add(self.stats_tab, text="  统计信息  ")
        self._create_statistics_tab()
    
    def _create_user_management_tab(self):
        """创建用户管理选项卡"""
        # 工具栏
        toolbar = tk.Frame(self.user_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            toolbar,
            text="刷新列表",
            command=self._refresh_user_list,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            toolbar,
            text="重置人脸",
            command=self._reset_user_face,
            width=12,
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            toolbar,
            text="删除用户",
            command=self._delete_user,
            width=12,
            bg="#f44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        # 用户列表
        list_frame = tk.Frame(self.user_tab)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("ID", "用户名", "人脸状态")
        self.user_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # 设置列
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("用户名", text="用户名")
        self.user_tree.heading("人脸状态", text="人脸状态")
        
        self.user_tree.column("ID", width=50, anchor='center')
        self.user_tree.column("用户名", width=200, anchor='w')
        self.user_tree.column("人脸状态", width=150, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.user_tree.yview
        )
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        self.user_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_log_viewer_tab(self):
        """创建日志查看选项卡"""
        # 工具栏
        toolbar = tk.Frame(self.log_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            toolbar,
            text="刷新日志",
            command=self._refresh_logs,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Label(toolbar, text="显示条数:").pack(side=tk.LEFT, padx=5)
        
        self.log_count_var = tk.StringVar(value="50")
        log_count_entry = tk.Entry(toolbar, textvariable=self.log_count_var, width=8)
        log_count_entry.pack(side=tk.LEFT, padx=5)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            self.log_tab,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=20
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def _create_statistics_tab(self):
        """创建统计信息选项卡"""
        # 统计信息框架
        stats_frame = tk.Frame(self.stats_tab)
        stats_frame.pack(expand=True, pady=50)
        
        tk.Label(
            stats_frame,
            text="系统统计信息",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # 统计标签
        self.stats_labels = {}
        
        stats_items = [
            ("total_users", "总用户数"),
            ("face_enabled", "启用人脸"),
            ("force_mfa", "强制MFA"),
            ("face_threshold", "人脸阈值")
        ]
        
        for key, label in stats_items:
            frame = tk.Frame(stats_frame)
            frame.pack(pady=5)
            
            tk.Label(
                frame,
                text=f"{label}:",
                width=15,
                anchor='e',
                font=("Arial", 11)
            ).pack(side=tk.LEFT, padx=10)
            
            value_label = tk.Label(
                frame,
                text="--",
                width=20,
                anchor='w',
                font=("Arial", 11, "bold"),
                fg="#2196F3"
            )
            value_label.pack(side=tk.LEFT, padx=10)
            
            self.stats_labels[key] = value_label
        
        # 刷新按钮
        tk.Button(
            stats_frame,
            text="刷新统计",
            command=self._refresh_statistics,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10)
        ).pack(pady=20)
    
    def _refresh_user_list(self):
        """刷新用户列表"""
        if not self.is_logged_in:
            return
        
        # 清空现有项
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # 获取用户列表
        users = list_users()
        
        # 填充数据
        for user in users:
            face_status = "✓ 已启用" if user['face_enabled'] else "✗ 未启用"
            self.user_tree.insert(
                "",
                tk.END,
                values=(user['id'], user['username'], face_status)
            )
    
    def _refresh_logs(self):
        """刷新日志"""
        if not self.is_logged_in:
            return
        
        try:
            count = int(self.log_count_var.get())
        except:
            count = 50
        
        logs = view_auth_logs(count)
        
        self.log_text.delete(1.0, tk.END)
        for log in logs:
            self.log_text.insert(tk.END, log)
        
        # 滚动到底部
        self.log_text.see(tk.END)
    
    def _refresh_statistics(self):
        """刷新统计信息"""
        if not self.is_logged_in:
            return
        
        stats = get_system_statistics()
        
        self.stats_labels['total_users'].config(text=str(stats.get('total_users', 0)))
        self.stats_labels['face_enabled'].config(text=str(stats.get('face_enabled_users', 0)))
        self.stats_labels['force_mfa'].config(
            text="启用" if stats.get('force_mfa', False) else "禁用"
        )
        self.stats_labels['face_threshold'].config(text=str(stats.get('face_threshold', 0.5)))
    
    def _reset_user_face(self):
        """重置用户人脸"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个用户")
            return
        
        item = self.user_tree.item(selection[0])
        username = item['values'][1]
        
        result = messagebox.askyesno(
            "确认",
            f"确定要重置用户 '{username}' 的人脸数据吗？\n重置后该用户需要重新录入人脸。"
        )
        
        if result:
            success = reset_user_face(username)
            if success:
                messagebox.showinfo("成功", f"已重置用户 '{username}' 的人脸数据")
                self._refresh_user_list()
            else:
                messagebox.showerror("失败", "重置失败，请查看日志")
    
    def _delete_user(self):
        """删除用户"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个用户")
            return
        
        item = self.user_tree.item(selection[0])
        username = item['values'][1]
        
        result = messagebox.askyesno(
            "危险操作",
            f"确定要删除用户 '{username}' 吗？\n此操作不可恢复！",
            icon='warning'
        )
        
        if result:
            success = delete_user(username)
            if success:
                messagebox.showinfo("成功", f"已删除用户 '{username}'")
                self._refresh_user_list()
                self._refresh_statistics()
            else:
                messagebox.showerror("失败", "删除失败，请查看日志")
    
    def _logout(self):
        """退出登录"""
        self.is_logged_in = False
        self.admin_frame.pack_forget()
        self.login_frame.pack(expand=True, fill='both')


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
    root.title("管理员界面测试")
    root.geometry("700x600")
    
    admin_view = AdminView(root)
    admin_view.pack(fill='both', expand=True)
    
    root.mainloop()
