#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户密码更新器 - GUI版本
功能：1. 通过API抓取用户信息 2. 更新FIRST项为0的用户密码 3. 提供图形界面
"""

import json
import os
import random
import string
import requests
import threading
import time
import sys
from datetime import datetime

# 配置信息
API_URL = "https://api.codemao.cn"  # 主API地址
DEFAULT_WORKSHOP_ID = 25294  # 默认工作室ID
DATABASE_PATH = os.path.join("data", "database.json")  # 数据库文件路径
LOG_FILE = "user_password_updater.log"  # 日志文件

# 模拟API的基本认证信息（实际环境中应使用更安全的认证方式）
API_USERNAME = "UIO"  # 超级管理员用户名
API_PASSWORD = "328817"  # 超级管理员密码

# 全局变量用于存储设置
settings = {
    "user_fetch_interval": 5 * 60,  # 每5分钟抓取一次用户信息
    "password_update_interval": 15 * 60,  # 每15分钟更新一次密码
    "workshop_id": DEFAULT_WORKSHOP_ID,
    "api_username": API_USERNAME,
    "api_password": API_PASSWORD
}

# 全局变量，用于存储GUI日志文本框引用
gui_log_text = None

# 尝试导入GUI相关模块
tk_available = False
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    tk_available = True
    print("GUI模块导入成功")
except ImportError:
    print("警告: GUI模块导入失败，将以命令行模式运行")
    from datetime import datetime  # 即使没有GUI，也需要datetime

def log_message(message, level="INFO"):
    """记录消息到日志文件和控制台，并更新GUI界面"""
    # 确保导入datetime
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # 输出到控制台
    print(log_entry)
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"写入日志失败: {e}")
    
    # 安全地更新GUI日志文本框（如果存在）
    if tk_available and gui_log_text:
        # 使用after方法确保在主线程中更新GUI
        try:
            # 尝试获取root窗口引用
            root = None
            if hasattr(gui_log_text, 'master'):
                root = gui_log_text.master
                while root and hasattr(root, 'master') and root.master:
                    root = root.master
            
            # 如果找到了root窗口，使用after方法更新GUI
            if root and hasattr(root, 'after'):
                def update_gui():
                    try:
                        if gui_log_text and gui_log_text.winfo_exists():
                            gui_log_text.config(state=tk.NORMAL)
                            gui_log_text.insert(tk.END, log_entry + "\n")
                            gui_log_text.see(tk.END)
                            gui_log_text.config(state=tk.DISABLED)
                    except Exception as e:
                        # 如果GUI更新失败，只记录到文件
                        print(f"GUI日志更新失败: {str(e)}")
                
                root.after(0, update_gui)
        except Exception as e:
            # 如果无法更新GUI，只记录到文件
            print(f"GUI日志更新失败: {str(e)}")

def load_database():
    """加载数据库文件 - 通过正规途径准确加载数据库数据"""
    log_message(f"开始加载数据库文件: {DATABASE_PATH}")
    
    # 严格检查文件是否存在
    if not os.path.exists(DATABASE_PATH):
        log_message(f"数据库文件不存在: {DATABASE_PATH}", "INFO")
        return None
    
    # 严格检查文件是否为常规文件（非目录）
    if not os.path.isfile(DATABASE_PATH):
        log_message(f"路径不是有效文件: {DATABASE_PATH}", "ERROR")
        return None
    
    try:
        # 检查文件大小
        file_size = os.path.getsize(DATABASE_PATH)
        log_message(f"数据库文件大小: {file_size} 字节")
        
        # 读取文件内容
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
            # 检查文件内容是否为空
            if not content:
                log_message("数据库文件内容为空", "WARNING")
                return None
            
            # 尝试解析JSON
            try:
                database = json.loads(content)
                
                # 验证数据库结构
                if not isinstance(database, dict):
                    log_message("数据库内容格式错误，根节点必须是对象类型", "ERROR")
                    return None
                
                # 记录数据库基本信息
                if "users" in database and isinstance(database["users"], list):
                    # 统计不重复的用户ID数量
                    unique_user_ids = set()
                    total_records = len(database['users'])
                    
                    for user in database['users']:
                        if isinstance(user, dict) and "id" in user:
                            user_id = str(user["id"])
                            unique_user_ids.add(user_id)
                    
                    unique_user_count = len(unique_user_ids)
                    log_message(f"数据库加载成功，总记录数: {total_records}，不重复用户数量: {unique_user_count}")
                else:
                    log_message("数据库加载成功，但users字段不存在或格式不正确", "WARNING")
                
                return database
                
            except json.JSONDecodeError as e:
                log_message(f"数据库文件JSON格式错误: {str(e)}", "ERROR")
                # 提供更详细的错误信息
                error_pos = e.pos
                context = content[max(0, error_pos-20):min(len(content), error_pos+20)]
                log_message(f"JSON错误位置上下文: '{context}'", "ERROR")
                return None
                
    except UnicodeDecodeError:
        log_message("数据库文件编码错误，无法使用UTF-8解码", "ERROR")
        return None
    except PermissionError:
        log_message(f"没有权限读取数据库文件: {DATABASE_PATH}", "ERROR")
        return None
    except Exception as e:
        log_message(f"加载数据库文件时发生未预期错误: {str(e)}", "ERROR")
        # 记录异常类型以帮助调试
        log_message(f"异常类型: {type(e).__name__}", "ERROR")
        return None

def save_database(database):
    """保存数据库文件"""
    try:
        os.makedirs("data", exist_ok=True)
        with open(DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        log_message("数据库保存成功")
        return True
    except Exception as e:
        log_message(f"保存数据库文件失败: {str(e)}", "ERROR")
        return False

def generate_strong_password(length=12):
    """生成强密码"""
    # 包含大小写字母、数字和特殊字符
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    while True:
        password = ''.join(random.choice(characters) for _ in range(length))
        # 确保密码包含至少一个数字和一个特殊字符
        if (any(c.isdigit() for c in password) and 
            any(c in "!@#$%^&*()" for c in password)):
            return password

def fetch_users_from_api():
    """从API分页获取所有用户数据，每页15个"""
    workshop_id = settings.get("workshop_id", DEFAULT_WORKSHOP_ID)
    try:
        all_users = []
        page_size = 15  # 每页15个用户
        offset = 0  # 起始偏移量
        has_more = True
        page = 1
        
        log_message(f"开始分页获取所有用户数据（每页{page_size}个），工作室ID: {workshop_id}")
        
        while has_more:
            # 构建分页API请求
            api_endpoint = f"{API_URL}/web/shops/{workshop_id}/users"
            params = {
                "offset": offset,
                "limit": page_size
            }
            
            # 使用管理员凭据进行认证
            headers = {
                "User-Agent": "PasswordManager/1.0"
            }
            auth = (settings["api_username"], settings["api_password"])  # 基本认证
            
            log_message(f"正在调用API（第{page}页）: {api_endpoint}?offset={offset}&limit={page_size}")
            
            # 发送请求
            response = requests.get(
                api_endpoint,
                params=params,
                auth=auth,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            page_users = data.get('items', [])
            
            log_message(f"第{page}页获取成功，返回{len(page_users)}个用户")
            
            # 添加到总用户列表
            all_users.extend(page_users)
            
            # 检查是否还有更多数据
            total = data.get('total', 0)
            if len(all_users) >= total or len(page_users) < page_size:
                has_more = False
            else:
                offset += page_size
                page += 1
        
        log_message(f"分页获取完成，共获取到 {len(all_users)} 个用户")
        return all_users
    
    except requests.exceptions.RequestException as e:
        log_message(f"API请求错误: {str(e)}", "ERROR")
        # 如果API调用失败，尝试直接从文件读取
        log_message("尝试直接从文件读取用户数据")
        database = load_database()
        if database:
            return database.get("users", [])
        return []

def update_first_login_passwords(users):
    """更新FIRST项为0的用户密码"""
    log_message("开始更新FIRST项为0的用户密码")
    updated_count = 0
    
    for user in users:
        # 检查FIRST项是否为0
        if user.get("first") == 0:
            # 生成新密码
            new_password = generate_strong_password()
            user["password"] = new_password
            user["lastPasswordChange"] = int(datetime.now().timestamp() * 1000)
            # 根据需求，first字段必须始终保持为0，不再将其设置为1
            # 只更新密码，不修改first字段的值
            updated_count += 1
            log_message(f"已更新用户 {user.get('username', '未知用户')} 的密码，保持first=0")
    
    log_message(f"密码更新完成，共更新了 {updated_count} 个用户")
    return updated_count

def create_default_users():
    """创建默认用户列表"""
    # 创建默认用户数据
    default_users = [
        {
            "id": 999999,
            "username": "admin",
            "password": "328817",
            "role": "ADMIN",
            "position": "DEPUTYLEADER",
            "lastPasswordChange": int(datetime.now().timestamp() * 1000),
            "confirmed": True,
            "first": 0
        },
        {
            "id": 2,
            "username": "UIO",
            "password": "328817",
            "role": "ADMIN",
            "position": "DEPUTYLEADER",
            "lastPasswordChange": int(datetime.now().timestamp() * 1000),
            "confirmed": True,
            "first": 0
        }
    ]
    log_message(f"创建了 {len(default_users)} 个默认用户")
    return default_users

def ensure_user_data_complete(user):
    """确保用户数据包含所有必要字段"""
    # 确保导入datetime
    from datetime import datetime
    # 确保存在所有必要字段
    required_fields = {
        'id': '',
        'username': '',
        'email': '',
        'password': '',
        'role': 'MEMBER',
        'position': '',
        'confirmed': True,
        'lastPasswordChange': int(datetime.now().timestamp() * 1000),
        'first': 0  # 新用户的first字段默认值为0
    }
    
    # 补全缺失字段
    for field, default_value in required_fields.items():
        if field not in user:
            if field == 'password' and 'first' in user and user['first'] == 0:
                # 对于首次登录用户，生成强密码
                user[field] = generate_strong_password()
            elif field == 'email' and 'username' in user:
                # 使用username作为email以兼容旧数据
                user[field] = user['username']
            else:
                # 特别注意：first字段只在不存在时才设置为0，不会覆盖已有值
                # 确保first字段的默认值始终为0
                user[field] = default_value
        elif field == 'first':
            # 确保first字段的值始终保持为0，除非通过密码更新流程主动设置为1
            # 但根据需求，我们应该确保它保持为0，这里不进行修改
            pass
    
    return user

def update_users_in_database():
    """更新数据库中的用户信息（只添加新用户）"""
    log_message("开始更新数据库中的用户信息")
    
    # 加载数据库
    database = load_database()
    
    # 从API抓取用户信息
    users = fetch_users_from_api()
    
    # 如果API和数据库都没有数据，创建默认用户
    if not database and not users:
        log_message("未获取到用户数据，创建默认用户", "WARNING")
        users = create_default_users()
    
    if not users:
        log_message("未获取到用户数据，操作终止", "ERROR")
        return False
    
    if not database:
        # 如果数据库不存在，创建新的
        log_message("本地数据库不存在，创建新数据库")
        database = {
            "users": users,
            "applications": [],
            "settings": {
                "systemName": "KL工作室人员管理系统",
                "version": "1.0.0",
                "passwordExpiryDays": 30,
                "cookieExpiryDays": 1
            }
        }
    else:
        # 只添加新用户，不更新已有用户
        # 使用集合存储已有用户的ID、用户名和邮箱，提高查找效率
        existing_ids = {str(user.get('id')) for user in database.get('users', []) if user.get('id')}
        existing_usernames = {user.get('username') for user in database.get('users', []) if user.get('username')}
        existing_emails = {user.get('email') for user in database.get('users', []) if user.get('email')}
        
        added_count = 0
        skipped_count = 0
        
        for user in users:
            user_id = user.get('id')
            username = user.get('username')
            email = user.get('email')
            
            # 优先通过ID检查用户是否已存在（确保ID类型一致）
            if user_id and str(user_id) in existing_ids:
                skipped_count += 1
                # 避免过多日志，只记录重要信息
                if skipped_count <= 10 or skipped_count % 50 == 0:
                    log_message(f"用户ID {user_id} 已存在，跳过添加")
                continue
            
            # 然后通过用户名检查
            if username and username in existing_usernames:
                skipped_count += 1
                # 避免过多日志，只记录重要信息
                if skipped_count <= 10 or skipped_count % 50 == 0:
                    log_message(f"用户 {username} 已存在，跳过添加")
                continue
            
            # 最后通过邮箱检查
            if email and email in existing_emails:
                skipped_count += 1
                # 避免过多日志，只记录重要信息
                if skipped_count <= 10 or skipped_count % 50 == 0:
                    log_message(f"用户邮箱 {email} 已存在，跳过添加")
                continue
                
            # 添加新用户
            database['users'].append(user)
            added_count += 1
            
            # 更新已存在集合，避免重复添加
            if user_id:
                existing_ids.add(user_id)
            if username:
                existing_usernames.add(username)
            if email:
                existing_emails.add(email)
                
            log_message(f"已添加新用户: {username or email or f'ID:{user_id}'}")
        
        log_message(f"用户数据处理完成，新增了 {added_count} 个用户，跳过了 {skipped_count} 个已存在的用户")
    
    # 检查并补全数据库中所有用户的字段
    for i, db_user in enumerate(database["users"]):
        database["users"][i] = ensure_user_data_complete(db_user)
    
    # 保存更新后的数据库
    if save_database(database):
        log_message("用户数据已成功保存到数据库")
        # 记录更新完成，可以触发用户数量更新
        log_message("用户数据更新完成，准备更新用户数量统计")
        return True
    else:
        log_message("保存数据库失败", "ERROR")
        return False

def update_passwords_for_first_zero():
    """更新FIRST项为0的用户密码"""
    log_message("开始检查并更新密码")
    
    # 加载数据库
    database = load_database()
    if not database:
        log_message("无法加载数据库，操作终止", "ERROR")
        return
    
    db_users = database.get("users", [])
    
    # 检查并补全所有用户数据
    for i, db_user in enumerate(db_users):
        db_users[i] = ensure_user_data_complete(db_user)
    
    # 更新first=0用户的密码
    updated_count = update_first_login_passwords(db_users)
    
    # 如果有更新，保存数据库
    if updated_count > 0:
        if save_database(database):
            log_message(f"成功保存数据库，共更新了 {updated_count} 个用户密码")
        else:
            log_message("保存数据库失败", "ERROR")
    else:
        log_message("没有用户需要更新密码")

if tk_available:
    class PasswordUpdaterGUI:
        """密码更新器GUI类"""
        
        def __init__(self, root):
            self.root = root
            self.root.title("KL工作室用户密码更新系统")
            self.root.geometry("800x600")
            self.root.minsize(800, 600)
            
            # 设置中文字体
            self.setup_fonts()
            
            # 创建主框架
            self.create_main_frame()
            
            # 启动后台任务线程
            self.stop_event = threading.Event()
            self.background_thread = threading.Thread(target=self.background_task)
            self.background_thread.daemon = True
            self.background_thread.start()
            
            # 设置窗口关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        def setup_fonts(self):
            """设置中文字体"""
            # 在Windows上使用系统默认中文字体
            self.font_config = {
                'title': ('SimHei', 16, 'bold'),
                'subtitle': ('SimHei', 12, 'bold'),
                'normal': ('SimHei', 10),
                'log': ('SimHei', 9)
            }
        
        def create_main_frame(self):
            """创建主界面框架"""
            # 创建顶部按钮区域
            top_frame = tk.Frame(self.root, padx=10, pady=10)
            top_frame.pack(fill=tk.X)
            
            # 创建操作按钮
            self.fetch_button = tk.Button(
                top_frame, 
                text="立即抓取用户", 
                font=self.font_config['normal'],
                command=self.manual_fetch_users,
                width=15
            )
            self.fetch_button.pack(side=tk.LEFT, padx=5)
            
            self.update_button = tk.Button(
                top_frame, 
                text="立即更新密码", 
                font=self.font_config['normal'],
                command=self.manual_update_passwords,
                width=15
            )
            self.update_button.pack(side=tk.LEFT, padx=5)
            
            self.settings_button = tk.Button(
                top_frame, 
                text="设置", 
                font=self.font_config['normal'],
                command=self.open_settings,
                width=10
            )
            self.settings_button.pack(side=tk.LEFT, padx=5)
            
            # 创建状态显示标签
            self.status_frame = tk.Frame(self.root, padx=10, pady=5)
            self.status_frame.pack(fill=tk.X)
            
            self.status_label = tk.Label(
                self.status_frame,
                text="系统状态: 运行中",
                font=self.font_config['normal'],
                fg="green"
            )
            self.status_label.pack(anchor=tk.W)
            
            # 创建时间统计标签
            self.time_stats_label = tk.Label(
                self.status_frame,
                text="下次抓取用户: --:--:--  下次更新密码: --:--:--",
                font=self.font_config['normal']
            )
            self.time_stats_label.pack(anchor=tk.W)
            
            # 创建日志区域
            log_frame = tk.LabelFrame(self.root, text="运行日志", font=self.font_config['subtitle'])
            log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 创建日志文本框和滚动条
            log_scrollbar = tk.Scrollbar(log_frame)
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            global gui_log_text
            gui_log_text = tk.Text(
                log_frame,
                wrap=tk.WORD,
                yscrollcommand=log_scrollbar.set,
                font=self.font_config['log'],
                bg="#f0f0f0"
            )
            gui_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            gui_log_text.config(state=tk.DISABLED)
            
            log_scrollbar.config(command=gui_log_text.yview)
            
            # 创建底部信息栏
            bottom_frame = tk.Frame(self.root, padx=10, pady=5)
            bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            self.info_label = tk.Label(
                bottom_frame,
                text="KL工作室用户密码更新系统 - 版本 1.0.0",
                font=self.font_config['normal']
            )
            self.info_label.pack(side=tk.LEFT)
            
            self.user_count_label = tk.Label(
                bottom_frame,
                text="当前用户数: 0",
                font=self.font_config['normal']
            )
            self.user_count_label.pack(side=tk.RIGHT)
        
        def manual_fetch_users(self):
            """手动触发用户抓取"""
            threading.Thread(target=update_users_in_database).start()
        
        def manual_update_passwords(self):
            """手动触发密码更新"""
            threading.Thread(target=update_passwords_for_first_zero).start()
        
        def open_settings(self):
            """打开设置对话框"""
            # 获取当前设置值
            fetch_interval = settings["user_fetch_interval"] // 60
            update_interval = settings["password_update_interval"] // 60
            workshop_id = settings["workshop_id"]
            api_username = settings["api_username"]
            api_password = settings["api_password"]
            
            # 创建设置窗口
            settings_window = tk.Toplevel(self.root)
            settings_window.title("系统设置")
            settings_window.geometry("500x400")
            settings_window.resizable(False, False)
            settings_window.transient(self.root)
            settings_window.grab_set()
            
            # 创建设置界面
            frame = tk.Frame(settings_window, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # 工作室ID设置
            workshop_id_frame = tk.Frame(frame)
            workshop_id_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                workshop_id_frame,
                text="工作室ID:",
                font=self.font_config['normal'],
                width=25
            ).pack(side=tk.LEFT)
            
            workshop_id_var = tk.StringVar(value=str(workshop_id))
            workshop_id_entry = tk.Entry(
                workshop_id_frame,
                textvariable=workshop_id_var,
                font=self.font_config['normal'],
                width=30
            )
            workshop_id_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # API用户名设置
            username_frame = tk.Frame(frame)
            username_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                username_frame,
                text="API用户名:",
                font=self.font_config['normal'],
                width=25
            ).pack(side=tk.LEFT)
            
            username_var = tk.StringVar(value=api_username)
            username_entry = tk.Entry(
                username_frame,
                textvariable=username_var,
                font=self.font_config['normal'],
                width=20
            )
            username_entry.pack(side=tk.LEFT, padx=5)
            
            # API密码设置
            password_frame = tk.Frame(frame)
            password_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                password_frame,
                text="API密码:",
                font=self.font_config['normal'],
                width=25
            ).pack(side=tk.LEFT)
            
            password_var = tk.StringVar(value=api_password)
            password_entry = tk.Entry(
                password_frame,
                textvariable=password_var,
                font=self.font_config['normal'],
                width=20,
                show="*"
            )
            password_entry.pack(side=tk.LEFT, padx=5)
            
            # 用户抓取时间间隔设置
            fetch_frame = tk.Frame(frame)
            fetch_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                fetch_frame,
                text="抓取成员信息时间间隔 (分钟):",
                font=self.font_config['normal'],
                width=25
            ).pack(side=tk.LEFT)
            
            fetch_var = tk.StringVar(value=str(fetch_interval))
            fetch_entry = tk.Entry(
                fetch_frame,
                textvariable=fetch_var,
                font=self.font_config['normal'],
                width=10
            )
            fetch_entry.pack(side=tk.LEFT, padx=5)
            
            # 密码更新时间间隔设置
            update_frame = tk.Frame(frame)
            update_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                update_frame,
                text="更新first=0用户密码时间间隔 (分钟):",
                font=self.font_config['normal'],
                width=25
            ).pack(side=tk.LEFT)
            
            update_var = tk.StringVar(value=str(update_interval))
            update_entry = tk.Entry(
                update_frame,
                textvariable=update_var,
                font=self.font_config['normal'],
                width=10
            )
            update_entry.pack(side=tk.LEFT, padx=5)
            
            # 按钮区域
            button_frame = tk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=20)
            
            def save_settings():
                try:
                    new_fetch = int(fetch_var.get())
                    new_update = int(update_var.get())
                    new_workshop_id = int(workshop_id_var.get().strip())
                    new_api_username = username_var.get().strip()
                    new_api_password = password_var.get()
                    
                    if new_fetch < 1 or new_update < 1:
                        messagebox.showerror("错误", "时间间隔必须大于0分钟")
                        return
                    
                    if not new_api_username:
                        messagebox.showerror("错误", "API用户名不能为空")
                        return
                    
                    # 更新设置
                    settings["user_fetch_interval"] = new_fetch * 60
                    settings["password_update_interval"] = new_update * 60
                    settings["workshop_id"] = new_workshop_id
                    settings["api_username"] = new_api_username
                    settings["api_password"] = new_api_password
                    
                    log_message(f"系统设置已更新: 用户抓取间隔={new_fetch}分钟, 密码更新间隔={new_update}分钟, 工作室ID={new_workshop_id}")
                    messagebox.showinfo("成功", "设置已保存")
                    settings_window.destroy()
                    
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字")
            
            tk.Button(
                button_frame,
                text="保存",
                font=self.font_config['normal'],
                command=save_settings,
                width=10
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                button_frame,
                text="取消",
                font=self.font_config['normal'],
                command=settings_window.destroy,
                width=10
            ).pack(side=tk.LEFT, padx=5)
        
        def update_status(self):
            """更新状态显示 - 通过逐个检查ID来统计不重复的用户数量（被动触发模式）"""
            # 严格从数据库文件加载数据，确保统计准确的用户数量
            database = load_database()
            if database and "users" in database:
                # 确保users是列表类型
                if isinstance(database["users"], list):
                    # 创建一个集合来存储不重复的用户ID
                    unique_user_ids = set()
                    total_records = len(database["users"])
                    
                    # 逐个检查用户ID，统计不重复的用户数量
                    for user in database["users"]:
                        if isinstance(user, dict) and "id" in user:
                            # 将ID转换为字符串以确保正确比较
                            user_id = str(user["id"])
                            unique_user_ids.add(user_id)
                    
                    # 计算不重复的用户数量
                    unique_user_count = len(unique_user_ids)
                    
                    # 记录用户数量信息到日志
                    log_message(f"通过逐个检查ID统计，当前系统总记录数: {total_records}，不重复用户数量: {unique_user_count}")
                    user_count = unique_user_count
                else:
                    # 如果users不是列表，记录错误并设为0
                    log_message("数据库中的users字段格式错误，不是有效列表", "ERROR")
                    user_count = 0
            else:
                # 如果数据库不存在或没有users字段
                if database is None:
                    log_message("数据库文件不存在或为空，当前用户数量为0", "INFO")
                else:
                    log_message("数据库中没有users字段，当前用户数量为0", "WARNING")
                user_count = 0
            
            # 更新界面显示
            self.user_count_label.config(text=f"当前用户数: {user_count}")
            
            # 更新状态标签
            if self.background_thread.is_alive():
                self.status_label.config(text="系统状态: 运行中", fg="green")
            else:
                self.status_label.config(text="系统状态: 已停止", fg="red")
            
            # 移除自动循环调用，改为被动触发模式
        
        def background_task(self):
            """后台定时任务"""
            log_message("用户密码更新系统已启动")
            log_message(f"初始设置: 用户抓取间隔={settings['user_fetch_interval']//60}分钟, 密码更新间隔={settings['password_update_interval']//60}分钟")
            log_message(f"工作室ID: {settings['workshop_id']}")
            
            # 系统启动时等待一分钟
            log_message("系统启动中，正在等待10秒...")
            for i in range(10):  # 减少等待时间为10秒以便快速测试
                if self.stop_event.is_set():
                    return
                time.sleep(1)
            log_message("启动等待完成，开始执行任务")
            
            # 确保数据目录存在
            os.makedirs("data", exist_ok=True)
            
            # 初始化最后执行时间
            last_fetch_time = 0
            last_update_time = 0
            
            # 执行一次用户抓取
            if update_users_in_database():
                # 初始用户抓取完成后，更新用户数量
                log_message("初始用户数据抓取完成，触发用户数量统计")
                if self.root.winfo_exists():
                    self.root.after(0, self.update_status)
            last_fetch_time = time.time()
            
            # 主循环
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # 计算下次执行时间
                next_fetch = last_fetch_time + settings["user_fetch_interval"]
                next_update = last_update_time + settings["password_update_interval"]
                
                # 格式化时间显示
                from datetime import datetime
                fetch_time_str = datetime.fromtimestamp(next_fetch).strftime("%H:%M:%S")
                update_time_str = datetime.fromtimestamp(next_update).strftime("%H:%M:%S")
                
                # 更新GUI时间统计
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.time_stats_label.config(
                        text=f"下次抓取用户: {fetch_time_str}  下次更新密码: {update_time_str}"
                    ))
                
                # 检查是否需要抓取用户
                if current_time - last_fetch_time >= settings["user_fetch_interval"]:
                    # 执行用户抓取并检查是否成功
                    if update_users_in_database():
                        # 用户数据更新成功后，通过GUI线程安全的方式更新用户数量
                        log_message("用户数据更新完成，触发用户数量重新统计")
                        if self.root.winfo_exists():
                            self.root.after(0, self.update_status)
                    last_fetch_time = current_time
                
                # 检查是否需要更新密码
                if current_time - last_update_time >= settings["password_update_interval"]:
                    update_passwords_for_first_zero()
                    last_update_time = current_time
                
                # 短暂休眠，避免占用过多CPU
                time.sleep(10)  # 每10秒检查一次
        
        def on_closing(self):
            """窗口关闭处理"""
            if messagebox.askyesno("确认关闭", "确定要关闭系统吗？"):
                log_message("用户密码更新系统正在关闭...")
                self.stop_event.set()
                self.root.after(1000, self.root.destroy)

def main():
    """主函数"""
    print("=== KL工作室用户密码更新系统启动 ===")
    
    # 检查是否以命令行模式运行
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("\n=== 命令行模式运行 ===")
        print("正在执行用户数据更新...")
        update_users_in_database()
        print("\n正在执行密码更新...")
        update_passwords_for_first_zero()
        print("\n=== 命令行操作完成 ===")
        return
    
    # 尝试GUI模式
    if tk_available:
        print("正在初始化GUI环境...")
        try:
            root = tk.Tk()
            print("GUI环境初始化成功")
            
            app = PasswordUpdaterGUI(root)
            # 初始显示时更新一次状态
            app.update_status()
            # 设置定时器定期更新状态标签（仅状态，不重新统计用户数量）
            def update_status_periodically():
                if not app.stop_event.is_set() and root.winfo_exists():
                    # 仅更新状态标签，不重新统计用户数量
                    if app.background_thread.is_alive():
                        app.status_label.config(text="系统状态: 运行中", fg="green")
                    else:
                        app.status_label.config(text="系统状态: 已停止", fg="red")
                    root.after(3000, update_status_periodically)
            # 启动定期更新状态标签的定时器
            root.after(3000, update_status_periodically)
            
            print("程序启动完成，进入主循环")
            print("按Ctrl+C终止程序")
            root.mainloop()
        except Exception as e:
            print(f"GUI启动失败: {str(e)}")
            print("将以命令行模式继续运行")
    else:
        print("GUI环境不可用")
    
    # 如果GUI模式失败，自动以命令行模式运行
    print("\n=== 命令行模式运行 ===")
    print("正在执行用户数据更新...")
    update_users_in_database()
    print("\n正在执行密码更新...")
    update_passwords_for_first_zero()
    print("\n=== 命令行操作完成 ===")
    print("提示: 可以使用 python user_password_updater_gui.py --cli 直接以命令行模式运行")

if __name__ == "__main__":
    main()