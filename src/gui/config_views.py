"""
安全配置界面
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.security_config import (
    get_force_mfa,
    set_force_mfa,
    get_face_threshold,
    set_face_threshold,
    get_face_enabled_users_count,
    get_all_security_config
)
from src.config.app_config import PBKDF2_ITERATIONS
from src.storage.file_repository import get_repository
from src.gui.ui_theme import (
    ModernTheme, StyleManager,
    create_modern_label, create_modern_button, create_card_frame
)


class SecurityConfigView(tk.Frame):
    """安全配置界面"""

    def __init__(self, parent):
        super().__init__(parent)
        self.theme = ModernTheme()
        self._init_ui()
        self._load_config()

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

        # 标题区域
        title_frame = tk.Frame(title_card, bg=self.theme.COLORS['bg_card'])
        title_frame.pack(fill='x')

        create_modern_label(
            title_frame,
            text="⚙️ 安全配置中心",
            style='title',
            fg=self.theme.COLORS['primary']
        ).pack(side='left', pady=self.theme.SIZES['padding_small'])

        # 刷新按钮
        refresh_btn = create_modern_button(
            title_frame,
            text="🔄 刷新配置",
            command=self._load_config,
            style='Primary'
        )
        refresh_btn.pack(side='right', padx=self.theme.SIZES['padding_small'])

        # 创建滚动区域
        self._create_scrollable_area(main_container)

    def _create_scrollable_area(self, parent):
        """创建可滚动区域"""
        # 创建Canvas和Scrollbar
        canvas_frame = tk.Frame(parent, bg=self.theme.COLORS['bg_main'])
        canvas_frame.pack(fill='both', expand=True)

        # 创建Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.theme.COLORS['bg_main'],
            highlightthickness=0
        )
        self.canvas.pack(side='left', fill='both', expand=True)

        # 创建垂直滚动条
        v_scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient='vertical',
            command=self.canvas.yview
        )
        v_scrollbar.pack(side='right', fill='y')

        # 配置Canvas滚动
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        # 创建内容框架
        self.content_frame = tk.Frame(
            self.canvas,
            bg=self.theme.COLORS['bg_main']
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor='nw'
        )

        # 绑定事件
        self.content_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)  # Linux
        self.canvas.bind('<Button-5>', self._on_mousewheel)  # Linux

        # 创建各个配置区域
        self._create_auth_mode_section()
        self._create_face_threshold_section()
        self._create_algorithm_info_section()
        self._create_statistics_section()

    def _on_frame_configure(self, event):
        """内容框架配置变化时更新滚动区域"""
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # 限制最小宽度以填满Canvas
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:  # 确保Canvas已经渲染
            self.canvas.itemconfig(
                self.canvas_window,
                width=canvas_width
            )

    def _on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        # Windows和macOS
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        # Linux
        elif event.num == 4:
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5:
            self.canvas.yview_scroll(1, 'units')
    
    def _create_auth_mode_section(self):
        """创建认证模式配置区域"""
        # 配置卡片
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill='x', pady=self.theme.SIZES['padding_medium'])

        # 区域标题
        create_modern_label(
            section_card,
            text="🔐 认证模式配置",
            style='subtitle',
            fg=self.theme.COLORS['primary']
        ).pack(pady=(0, self.theme.SIZES['padding_medium']))

        # 说明文字
        create_modern_label(
            section_card,
            text="选择系统的身份验证模式：",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, self.theme.SIZES['padding_medium']))

        # 强制MFA开关
        self.force_mfa_var = tk.BooleanVar()

        # 复选框框架
        checkbox_frame = tk.Frame(section_card, bg=self.theme.COLORS['bg_card'])
        checkbox_frame.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        force_mfa_check = tk.Checkbutton(
            checkbox_frame,
            text="🛡️ 强制双因素认证 (密码 + 人脸)",
            variable=self.force_mfa_var,
            command=self._on_force_mfa_changed,
            bg=self.theme.COLORS['bg_card'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            selectcolor=self.theme.COLORS['bg_card'],
            activebackground=self.theme.COLORS['bg_card'],
            activeforeground=self.theme.COLORS['primary']
        )
        force_mfa_check.pack(anchor='w')

        # 提示信息
        create_modern_label(
            section_card,
            text="💡 注意：关闭后，未启用人脸的用户可以仅使用密码登录",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        ).pack(anchor='w', pady=(self.theme.SIZES['padding_small'], 0))
    
    def _create_face_threshold_section(self):
        """创建人脸阈值配置区域"""
        # 配置卡片
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill='x', pady=self.theme.SIZES['padding_medium'])

        # 区域标题
        create_modern_label(
            section_card,
            text="📸 人脸识别阈值配置",
            style='subtitle',
            fg=self.theme.COLORS['primary']
        ).pack(pady=(0, self.theme.SIZES['padding_medium']))

        # 说明文字
        create_modern_label(
            section_card,
            text="调整人脸识别的欧氏距离阈值（越小越严格）：",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, self.theme.SIZES['padding_medium']))

        # 阈值滑块框架
        slider_frame = tk.Frame(section_card, bg=self.theme.COLORS['bg_card'])
        slider_frame.pack(fill='x', pady=self.theme.SIZES['padding_small'])

        # 滑块标签
        create_modern_label(
            slider_frame,
            text="宽松",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        ).pack(side='left', padx=(0, self.theme.SIZES['padding_medium']))

        # 滑块
        self.threshold_var = tk.DoubleVar()
        self.threshold_scale = tk.Scale(
            slider_frame,
            from_=0.3,
            to=0.7,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self._on_threshold_changing,
            showvalue=False,
            length=300,
            bg=self.theme.COLORS['bg_card'],
            fg=self.theme.COLORS['text_primary'],
            troughcolor=self.theme.COLORS['border_light'],
            activebackground=self.theme.COLORS['secondary'],
            highlightthickness=0
        )
        self.threshold_scale.pack(side='left', padx=self.theme.SIZES['padding_small'])

        create_modern_label(
            slider_frame,
            text="严格",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        ).pack(side='left', padx=(self.theme.SIZES['padding_medium'], 0))

        # 当前值显示框架
        value_frame = tk.Frame(section_card, bg=self.theme.COLORS['bg_card'])
        value_frame.pack(fill='x', pady=(self.theme.SIZES['padding_medium'], 0))

        create_modern_label(
            value_frame,
            text="🎯 当前阈值:",
            style='body'
        ).pack(side='left')

        self.threshold_label = create_modern_label(
            value_frame,
            text="0.50",
            style='heading',
            fg=self.theme.COLORS['secondary']
        )
        self.threshold_label.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 应用按钮
        apply_btn = create_modern_button(
            value_frame,
            text="✅ 应用更改",
            command=self._apply_threshold,
            style='Success'
        )
        apply_btn.pack(side='left', padx=self.theme.SIZES['padding_medium'])

        # 建议值说明
        create_modern_label(
            section_card,
            text="💡 建议值: 0.5 (平衡准确率) | 0.4 (高安全) | 0.6 (便利性)",
            style='caption',
            fg=self.theme.COLORS['text_muted']
        ).pack(anchor='w', pady=(self.theme.SIZES['padding_small'], 0))
    
    def _create_algorithm_info_section(self):
        """创建算法信息区域"""
        # 配置卡片
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill='x', pady=self.theme.SIZES['padding_medium'])

        # 区域标题
        create_modern_label(
            section_card,
            text="🔐 当前加密算法",
            style='subtitle',
            fg=self.theme.COLORS['primary']
        ).pack(pady=(0, self.theme.SIZES['padding_medium']))

        # 算法信息列表
        algorithms = [
            ("🔑 密码哈希", "PBKDF2-HMAC-SHA256"),
            ("🔒 加密算法", "AES-256-GCM"),
            ("🔄 迭代次数", f"{PBKDF2_ITERATIONS:,} 次"),
            ("🧪 盐值长度", "32 字节 (256 位)"),
            ("🔐 密钥长度", "32 字节 (256 位)")
        ]

        for icon_label, value in algorithms:
            # 信息项框架
            item_frame = tk.Frame(section_card, bg=self.theme.COLORS['bg_card'])
            item_frame.pack(fill='x', pady=self.theme.SIZES['padding_small'])

            # 标签
            create_modern_label(
                item_frame,
                text=f"{icon_label}:",
                style='body',
                fg=self.theme.COLORS['text_secondary']
            ).pack(side='left')

            # 值
            create_modern_label(
                item_frame,
                text=value,
                style='body',
                fg=self.theme.COLORS['text_primary']
            ).pack(side='left', padx=self.theme.SIZES['padding_small'])

            # 添加分割线
            if algorithms.index((icon_label, value)) < len(algorithms) - 1:
                separator = ttk.Separator(item_frame, orient='horizontal')
                separator.pack(fill='x', pady=(self.theme.SIZES['padding_small'], 0))
    
    def _create_statistics_section(self):
        """创建统计信息区域"""
        # 配置卡片
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill='x', pady=self.theme.SIZES['padding_medium'])

        # 区域标题
        create_modern_label(
            section_card,
            text="📊 用户统计信息",
            style='subtitle',
            fg=self.theme.COLORS['primary']
        ).pack(pady=(0, self.theme.SIZES['padding_medium']))

        # 统计信息框架
        stats_frame = tk.Frame(section_card, bg=self.theme.COLORS['bg_card'])
        stats_frame.pack(fill='x')

        # 启用人脸的用户统计
        face_frame = tk.Frame(stats_frame, bg=self.theme.COLORS['bg_card'])
        face_frame.pack(fill='x', pady=self.theme.SIZES['padding_medium'])

        create_modern_label(
            face_frame,
            text="👥 启用人脸验证的用户:",
            style='body',
            fg=self.theme.COLORS['text_secondary']
        ).pack(side='left')

        self.face_users_label = create_modern_label(
            face_frame,
            text="0 / 0",
            style='heading',
            fg=self.theme.COLORS['success']
        )
        self.face_users_label.pack(side='left', padx=self.theme.SIZES['padding_small'])

        # 添加一些空白的底部空间以确保滚动
        tk.Frame(section_card, bg=self.theme.COLORS['bg_card'], height=50).pack(fill='x')
    
    def _on_force_mfa_changed(self):
        """强制MFA开关变化"""
        new_value = self.force_mfa_var.get()
        
        # 确认操作
        if new_value:
            message = "启用强制双因素认证后，所有用户必须使用密码+人脸登录。\n未启用人脸的用户将无法登录。\n\n确定要启用吗？"
        else:
            message = "关闭强制双因素认证后，未启用人脸的用户可以仅使用密码登录。\n\n确定要关闭吗？"
        
        result = messagebox.askyesno("确认更改", message)
        
        if result:
            success = set_force_mfa(new_value)
            if success:
                mode = "强制双因素认证" if new_value else "仅密码模式"
                messagebox.showinfo("成功", f"已切换到 {mode}")
            else:
                messagebox.showerror("失败", "设置失败，请查看日志")
                # 恢复原值
                self.force_mfa_var.set(not new_value)
        else:
            # 取消操作，恢复原值
            self.force_mfa_var.set(not new_value)
    
    def _on_threshold_changing(self, value):
        """阈值滑块变化"""
        threshold_value = float(value)
        self.threshold_label.config(text=f"{threshold_value:.2f}")

        # 根据阈值改变颜色
        if threshold_value <= 0.4:
            color = self.theme.COLORS['success']  # 高安全 - 绿色
        elif threshold_value >= 0.6:
            color = self.theme.COLORS['warning']  # 便利性 - 橙色
        else:
            color = self.theme.COLORS['secondary']  # 平衡 - 蓝色

        self.threshold_label.config(fg=color)
    
    def _apply_threshold(self):
        """应用阈值更改"""
        new_threshold = self.threshold_var.get()
        
        result = messagebox.askyesno(
            "确认更改",
            f"将人脸识别阈值设置为 {new_threshold:.2f}？\n\n"
            "较小的值会提高安全性但可能增加误拒率(FRR)。"
        )
        
        if result:
            success = set_face_threshold(new_threshold)
            if success:
                messagebox.showinfo("成功", f"人脸识别阈值已设置为 {new_threshold:.2f}")
            else:
                messagebox.showerror("失败", "设置失败，请查看日志")
    
    def _load_config(self):
        """加载当前配置"""
        try:
            # 加载所有配置
            config = get_all_security_config()
            
            # 更新UI
            self.force_mfa_var.set(config.get('force_mfa', True))
            
            threshold = config.get('face_threshold', 0.5)
            self.threshold_var.set(threshold)
            self.threshold_label.config(text=f"{threshold:.2f}")
            
            # 更新统计
            face_count = get_face_enabled_users_count()
            try:
                repo = get_repository()
                total_users = len(repo.get_all_users())
            except:
                total_users = 0
            
            self.face_users_label.config(text=f"{face_count} / {total_users}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败：{str(e)}")


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
    root.title("安全配置测试")
    root.geometry("600x700")
    
    config_view = SecurityConfigView(root)
    config_view.pack(fill='both', expand=True)
    
    root.mainloop()
