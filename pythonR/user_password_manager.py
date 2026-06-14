import requests
import json
import time
import random
import string
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

# API配置
API_URL = "https://api.codemao.cn"
DEFAULT_WORKSHOP_ID = 25294

# 数据库文件路径
DATABASE_PATH = ".\\data\\database.json"

# 日志文件路径
LOG_FILE = ".\\user_password_manager.log"

# 全局变量用于存储设置
settings = {
    "user_fetch_interval": 10 * 60,  # 每10分钟抓取一次用户名
    "password_update_interval": 30 * 60,  # 每30分钟检查并更新密码
    "workshop_id": DEFAULT_WORKSHOP_ID  # 默认使用当前工作室ID
}

# 全局变量，用于存储GUI日志文本框引用
gui_log_text = None

def log_message(message):
    """记录日志信息，并更新GUI界面"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    
    # 安全地更新GUI日志文本框（如果存在）
    if gui_log_text:
        # 使用after方法确保在主线程中更新GUI
        # 由于after方法本身需要在Tk实例存在的情况下调用，我们需要额外检查
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
                        with open(LOG_FILE, "a", encoding="utf-8") as f:
                            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GUI日志更新失败: {str(e)}\n")
                
                root.after(0, update_gui)
        except Exception as e:
            # 如果无法更新GUI，只记录到文件
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GUI日志更新失败: {str(e)}\n")

def generate_strong_password():
    """生成8位复杂密码"""
    # 包含大小写字母、数字和特殊字符
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    # 确保密码长度为8位且包含至少一个数字和一个特殊字符
    while True:
        password = ''.join(random.choice(all_chars) for _ in range(8))
        if (any(c.isdigit() for c in password) and 
            any(c in "!@#$%^&*()" for c in password)):
            return password

def ensure_database_exists():
    """确保数据库文件存在"""
    if not os.path.exists(DATABASE_PATH):
        # 创建数据目录（如果不存在）
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        # 创建默认数据库结构
        default_db = {
            "users": [],
            "applications": [],
            "settings": {
                "systemName": "KL工作室人员管理系统",
                "version": "1.0.0",
                "passwordExpiryDays": 30,
                "cookieExpiryDays": 1
            }
        }
        with open(DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(default_db, f, ensure_ascii=False, indent=2)
        log_message("数据库文件已创建")

def load_database():
    """加载数据库"""
    ensure_database_exists()
    try:
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        log_message("警告：数据库文件格式错误，使用默认结构")
        return {
            "users": [],
            "applications": [],
            "settings": {
                "systemName": "KL工作室人员管理系统",
                "version": "1.0.0",
                "passwordExpiryDays": 30,
                "cookieExpiryDays": 1
            }
        }

def save_database(database):
    """保存数据库"""
    ensure_database_exists()
    with open(DATABASE_PATH, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

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
            
            log_message(f"正在调用API（第{page}页）: {api_endpoint}?offset={offset}&limit={page_size}")
            
            # 发送请求
            response = requests.get(api_endpoint, params=params, timeout=30)
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
        
        # 返回整合后的结果
        return {
            "items": all_users,
            "offset": 0,
            "limit": len(all_users),
            "total": len(all_users),
            "counted": True
        }
    except requests.exceptions.RequestException as e:
        log_message(f"API请求错误: {str(e)}")
        # 如果API调用失败，使用模拟数据作为备用
        log_message("使用模拟数据作为备用")
        return {
            "items": [
                {
                    "id": 1,
                    "name": "admin",
                    "user_id": 1001,
                    "position": "LEADER",
                    "role": 1,
                    "status": 1,
                    "avatar_url": "https://example.com/avatar1.png"
                }
            ],
            "offset": 0,
            "limit": 15,
            "total": 3,
            "counted": True
        }
    except Exception as e:
        log_message(f"从API获取用户数据时发生未知错误: {str(e)}")
        return {"items": []}

def ensure_user_data_complete(user):
    """确保用户数据包含所有必要字段，补全缺失字段"""
    # 确保存在所有必要字段
    required_fields = {
        'id': '',
        'username': '',
        'email': '',
        'password': '',
        'role': 'MEMBER',
        'position': '',
        'confirmed': True,
        'lastPasswordChange': int(time.time() * 1000),
        'first': 0
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
                user[field] = default_value
    
    return user

def update_users_in_database():
    """更新数据库中的用户信息"""
    log_message("开始更新数据库中的用户信息")
    
    # 获取API用户数据
    api_response = fetch_users_from_api()
    api_users = api_response.get("items", [])
    
    # 加载数据库
    database = load_database()
    db_users = database.get("users", [])
    
    # 创建用户映射，用于快速查找（同时支持username和email字段）
    user_map = {}
    for user in db_users:
        if "username" in user:
            user_map[user["username"]] = user
        elif "email" in user:
            user_map[user["email"]] = user
    
    # 添加新用户（不再更新已存在的用户）
    added_count = 0
    
    for api_user in api_users:
        username = api_user["name"]
        
        # 创建用户副本并确保数据完整性
        api_user_processed = {
            "id": api_user["id"],
            "username": username,
            "email": username,  # 保留email字段以兼容旧数据
            "role": "ADMIN" if api_user["role"] == 1 else "MEMBER",
            "position": api_user["position"]
        }
        
        if username not in user_map:
            # 仅添加新用户，确保数据完整
            new_user = ensure_user_data_complete(api_user_processed)
            new_user["password"] = "initial123"  # 初始密码
            new_user["lastPasswordChange"] = int(time.time() * 1000)
            new_user["confirmed"] = True
            new_user["first"] = 0  # 初始值为0
            
            db_users.append(new_user)
            added_count += 1
            log_message(f"已添加新用户: {username}")
        else:
            # 跳过已存在的用户，保持其原有状态
            log_message(f"用户 {username} 已存在，保持原有状态不做修改")
    
    # 检查并补全数据库中所有用户的字段
    for i, db_user in enumerate(db_users):
        db_users[i] = ensure_user_data_complete(db_user)
    
    # 保存更新后的数据库
    database["users"] = db_users
    save_database(database)
    
    log_message(f"用户更新完成: 添加了{added_count}个新用户")

def update_passwords_for_first_zero():
    """为first=0的用户生成8位复杂密码，包含随机符号"""
    log_message("开始检查并更新密码")
    
    # 加载数据库
    database = load_database()
    db_users = database.get("users", [])
    
    # 检查并补全所有用户数据
    for i, db_user in enumerate(db_users):
        db_users[i] = ensure_user_data_complete(db_user)
    
    updated_count = 0
    
    for user in db_users:
        # 为first=0的用户生成8位复杂密码
        if user.get("first", 0) == 0:
            # 生成8位复杂密码
            complex_password = generate_strong_password()
            user["password"] = complex_password
            user["lastPasswordChange"] = int(time.time() * 1000)
            updated_count += 1
            # 使用username字段，如果不存在则使用email字段
            user_name = user.get("username", user.get("email", "未知用户"))
            log_message(f"已为用户 {user_name} (first=0) 设置新的8位复杂密码: {complex_password}")
    
    # 同时为没有密码的用户也设置密码
    for user in db_users:
        if not user.get("password", ""):
            complex_password = generate_strong_password()
            user["password"] = complex_password
            user["lastPasswordChange"] = int(time.time() * 1000)
            updated_count += 1
            user_name = user.get("username", user.get("email", "未知用户"))
            log_message(f"已为无密码用户 {user_name} 设置8位复杂密码: {complex_password}")
    
    # 保存更新后的数据库
    database["users"] = db_users
    save_database(database)
    
    log_message(f"密码更新完成: 为{updated_count}个用户设置了初始密码")

def update_user_first_status(username):
    """将用户的first字段设置为1（标记为已登录）"""
    # 加载数据库
    database = load_database()
    db_users = database.get("users", [])
    
    # 检查并补全所有用户数据
    for i, db_user in enumerate(db_users):
        db_users[i] = ensure_user_data_complete(db_user)
    
    for user in db_users:
        # 同时检查username和email字段
        if user.get("username") == username or user.get("email") == username:
            user["first"] = 1
            log_message(f"已将用户 {username} 的first字段设置为1（已登录）")
            # 确保同时有username字段
            if "username" not in user and "email" in user:
                user["username"] = user["email"]
            break
    
    # 保存更新后的数据库
    database["users"] = db_users
    save_database(database)

class PasswordManagerGUI:
    """密码管理器GUI类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("KL工作室用户密码管理系统")
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
            text="KL工作室用户密码管理系统 - 版本 1.0.0",
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
        workshop_id = settings.get("workshop_id", DEFAULT_WORKSHOP_ID)
        
        # 创建设置窗口
        settings_window = tk.Toplevel(self.root)
        settings_window.title("系统设置")
        settings_window.geometry("400x320")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 创建设置界面
        frame = tk.Frame(settings_window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 工作室ID设置
        workshop_frame = tk.Frame(frame)
        workshop_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            workshop_frame,
            text="工作室ID:",
            font=self.font_config['normal'],
            width=25
        ).pack(side=tk.LEFT)
        
        workshop_var = tk.StringVar(value=str(workshop_id))
        workshop_entry = tk.Entry(
            workshop_frame,
            textvariable=workshop_var,
            font=self.font_config['normal'],
            width=15
        )
        workshop_entry.pack(side=tk.LEFT, padx=5)
        
        # 用户抓取时间间隔设置
        fetch_frame = tk.Frame(frame)
        fetch_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            fetch_frame,
            text="用户抓取时间间隔 (分钟):",
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
            text="密码更新时间间隔 (分钟):",
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
                new_workshop_id = int(workshop_var.get())
                
                if new_fetch < 1 or new_update < 1:
                    messagebox.showerror("错误", "时间间隔必须大于0分钟")
                    return
                
                if new_workshop_id <= 0:
                    messagebox.showerror("错误", "工作室ID必须大于0")
                    return
                
                # 更新设置
                settings["user_fetch_interval"] = new_fetch * 60
                settings["password_update_interval"] = new_update * 60
                settings["workshop_id"] = new_workshop_id
                
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
        """更新状态显示"""
        # 获取当前数据库中的用户数量
        database = load_database()
        user_count = len(database.get("users", []))
        
        self.user_count_label.config(text=f"当前用户数: {user_count}")
        
        # 更新状态标签
        if self.background_thread.is_alive():
            self.status_label.config(text="系统状态: 运行中", fg="green")
        else:
            self.status_label.config(text="系统状态: 已停止", fg="red")
        
        # 3秒后再次更新
        if not self.stop_event.is_set():
            self.root.after(3000, self.update_status)
    
    def background_task(self):
        """后台定时任务"""
        log_message("用户密码管理系统已启动")
        log_message(f"初始设置: 用户抓取间隔={settings['user_fetch_interval']//60}分钟, 密码更新间隔={settings['password_update_interval']//60}分钟")
        log_message(f"当前工作室ID: {settings.get('workshop_id', DEFAULT_WORKSHOP_ID)}")
        
        # 系统启动时等待一分钟
        log_message("系统启动中，正在等待60秒...")
        for i in range(60):
            if self.stop_event.is_set():
                return
            time.sleep(1)
        log_message("启动等待完成，开始执行任务")
        
        # 确保数据库存在
        ensure_database_exists()
        
        # 初始化最后执行时间
        last_fetch_time = 0
        last_update_time = 0
        
        # 执行一次用户抓取
        update_users_in_database()
        last_fetch_time = time.time()
        
        # 主循环
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # 计算下次执行时间
            next_fetch = last_fetch_time + settings["user_fetch_interval"]
            next_update = last_update_time + settings["password_update_interval"]
            
            # 格式化时间显示
            fetch_time_str = datetime.fromtimestamp(next_fetch).strftime("%H:%M:%S")
            update_time_str = datetime.fromtimestamp(next_update).strftime("%H:%M:%S")
            
            # 更新GUI时间统计
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.time_stats_label.config(
                    text=f"下次抓取用户: {fetch_time_str}  下次更新密码: {update_time_str}"
                ))
            
            # 检查是否需要抓取用户
            if current_time - last_fetch_time >= settings["user_fetch_interval"]:
                update_users_in_database()
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
            log_message("用户密码管理系统正在关闭...")
            self.stop_event.set()
            self.root.after(1000, self.root.destroy)

def main():
    """主函数"""
    root = tk.Tk()
    app = PasswordManagerGUI(root)
    app.update_status()
    root.mainloop()

if __name__ == "__main__":
    main()