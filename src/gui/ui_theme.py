"""
现代化UI主题配置
提供统一的颜色、字体和样式定义
"""
import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """现代化主题配置"""

    # 颜色配置
    COLORS = {
        # 主色调 - 深蓝色系
        'primary': '#2C3E50',        # 深蓝灰
        'primary_light': '#34495E',  # 浅一点的蓝灰
        'primary_dark': '#1A252F',   # 更深的蓝灰

        # 辅助色
        'secondary': '#3498DB',      # 蓝色
        'accent': '#E74C3C',         # 红色（警告/错误）
        'success': '#27AE60',        # 绿色（成功）
        'warning': '#F39C12',        # 橙色（警告）
        'info': '#9B59B6',           # 紫色（信息）

        # 背景色
        'bg_main': '#F8F9FA',        # 主背景
        'bg_card': '#FFFFFF',        # 卡片背景
        'bg_input': '#FFFFFF',       # 输入框背景
        'bg_button': '#3498DB',      # 按钮背景
        'bg_button_hover': '#2980B9', # 按钮悬停

        # 文字颜色
        'text_primary': '#2C3E50',   # 主文字
        'text_secondary': '#7F8C8D', # 次要文字
        'text_white': '#FFFFFF',     # 白色文字
        'text_muted': '#BDC3C7',     # 弱化文字

        # 边框和分割线
        'border': '#DDE6E9',         # 边框色
        'border_light': '#ECF0F1',   # 浅边框
        'shadow': 'rgba(0, 0, 0, 0.1)', # 阴影

        # 状态颜色
        'online': '#27AE60',          # 在线
        'offline': '#95A5A6',        # 离线
        'error': '#E74C3C',          # 错误
        'pending': '#F39C12',        # 待处理
    }

    # 字体配置
    FONTS = {
        'title': ('Microsoft YaHei UI', 18, 'bold'),
        'subtitle': ('Microsoft YaHei UI', 14, 'bold'),
        'heading': ('Microsoft YaHei UI', 12, 'bold'),
        'body': ('Microsoft YaHei UI', 10),
        'caption': ('Microsoft YaHei UI', 9),
        'button': ('Microsoft YaHei UI', 10, 'bold'),
        'input': ('Microsoft YaHei UI', 10),
        'code': ('Consolas', 9),
    }

    # 尺寸配置
    SIZES = {
        'border_radius': 8,
        'padding_small': 8,
        'padding_medium': 16,
        'padding_large': 24,
        'margin_small': 4,
        'margin_medium': 8,
        'margin_large': 16,
        'button_height': 36,
        'input_height': 36,
        'card_shadow': 2,
    }

    # 动画配置
    ANIMATIONS = {
        'duration': 200,  # 毫秒
        'easing': 'ease-in-out',
    }


class StyleManager:
    """样式管理器"""

    def __init__(self, root=None):
        self.root = root
        self.theme = ModernTheme()
        if root:
            self.setup_styles()

    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()

        # 设置主题
        style.theme_use('clam')

        # 配置各种控件的样式
        self._configure_buttons(style)
        self._configure_entries(style)
        self._configure_frames(style)
        self._configure_notebook(style)

    def _configure_buttons(self, style):
        """配置按钮样式"""
        # 主要按钮
        style.configure(
            'Primary.TButton',
            background=self.theme.COLORS['bg_button'],
            foreground=self.theme.COLORS['text_white'],
            borderwidth=0,
            focuscolor='none',
            padding=(16, 8),
            font=self.theme.FONTS['button']
        )
        style.map(
            'Primary.TButton',
            background=[('active', self.theme.COLORS['bg_button_hover'])]
        )

        # 成功按钮
        style.configure(
            'Success.TButton',
            background=self.theme.COLORS['success'],
            foreground=self.theme.COLORS['text_white'],
            borderwidth=0,
            focuscolor='none',
            padding=(16, 8),
            font=self.theme.FONTS['button']
        )
        style.map(
            'Success.TButton',
            background=[('active', '#229954')]
        )

        # 警告按钮
        style.configure(
            'Warning.TButton',
            background=self.theme.COLORS['warning'],
            foreground=self.theme.COLORS['text_white'],
            borderwidth=0,
            focuscolor='none',
            padding=(16, 8),
            font=self.theme.FONTS['button']
        )
        style.map(
            'Warning.TButton',
            background=[('active', '#E67E22')]
        )

        # 危险按钮
        style.configure(
            'Danger.TButton',
            background=self.theme.COLORS['accent'],
            foreground=self.theme.COLORS['text_white'],
            borderwidth=0,
            focuscolor='none',
            padding=(16, 8),
            font=self.theme.FONTS['button']
        )
        style.map(
            'Danger.TButton',
            background=[('active', '#C0392B')]
        )

    def _configure_entries(self, style):
        """配置输入框样式"""
        style.configure(
            'Modern.TEntry',
            fieldbackground=self.theme.COLORS['bg_input'],
            borderwidth=1,
            relief='solid',
            padding=(12, 8),
            font=self.theme.FONTS['input'],
            insertcolor=self.theme.COLORS['secondary']
        )
        style.map(
            'Modern.TEntry',
            bordercolor=[('focus', self.theme.COLORS['secondary'])]
        )

    def _configure_frames(self, style):
        """配置框架样式"""
        style.configure(
            'Card.TFrame',
            background=self.theme.COLORS['bg_card'],
            relief='flat',
            borderwidth=1
        )

        style.configure(
            'Modern.TFrame',
            background=self.theme.COLORS['bg_main'],
            relief='flat'
        )

    def _configure_notebook(self, style):
        """配置选项卡样式"""
        style.configure(
            'Modern.TNotebook',
            background=self.theme.COLORS['bg_main'],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0]
        )

        style.configure(
            'Modern.TNotebook.Tab',
            background=self.theme.COLORS['bg_card'],
            foreground=self.theme.COLORS['text_secondary'],
            padding=[24, 12],
            font=self.theme.FONTS['body']
        )

        style.map(
            'Modern.TNotebook.Tab',
            background=[('selected', self.theme.COLORS['bg_card'])],
            foreground=[('selected', self.theme.COLORS['primary'])]
        )


def create_modern_label(parent, text, style='body', **kwargs):
    """创建现代化标签"""
    theme = ModernTheme()
    label = tk.Label(
        parent,
        text=text,
        font=theme.FONTS.get(style, theme.FONTS['body']),
        bg=kwargs.pop('bg', theme.COLORS['bg_main']),
        fg=kwargs.pop('fg', theme.COLORS['text_primary']),
        **kwargs
    )
    return label


def create_modern_button(parent, text, command=None, style='Primary', **kwargs):
    """创建现代化按钮"""
    theme = ModernTheme()
    btn = ttk.Button(
        parent,
        text=text,
        command=command,
        style=f'{style}.TButton',
        **kwargs
    )
    return btn


def create_modern_entry(parent, **kwargs):
    """创建现代化输入框"""
    entry = ttk.Entry(parent, style='Modern.TEntry', **kwargs)
    return entry


def create_card_frame(parent, **kwargs):
    """创建卡片框架"""
    theme = ModernTheme()
    frame = ttk.Frame(
        parent,
        style='Card.TFrame',
        padding=theme.SIZES['padding_medium'],
        **kwargs
    )
    return frame


def add_separator(parent, orient='horizontal', **kwargs):
    """添加分割线"""
    theme = ModernTheme()
    separator = ttk.Separator(
        parent,
        orient=orient,
        **kwargs
    )
    return separator