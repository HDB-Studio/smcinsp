#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户密码更新器
功能：1. 通过API抓取用户信息 2. 更新FIRST项为0的用户密码
"""

import json
import os
import random
import string
import requests
from datetime import datetime

# 配置信息
API_URL = "http://localhost:8000/data/database.json"  # 本地API地址
DATABASE_PATH = os.path.join("data", "database.json")  # 数据库文件路径
LOG_FILE = "user_password_updater.log"  # 日志文件

# 模拟API的基本认证信息（实际环境中应使用更安全的认证方式）
API_USERNAME = "UIO"  # 超级管理员用户名
API_PASSWORD = "328817"  # 超级管理员密码

def log_message(message, level="INFO"):
    """记录消息到日志文件和控制台"""
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

def load_database():
    """加载数据库文件"""
    try:
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                log_message("数据库文件为空，创建默认数据", "WARNING")
                return None
            return json.loads(content)
    except json.JSONDecodeError:
        log_message("数据库文件格式错误，创建默认数据", "WARNING")
        return None
    except Exception as e:
        log_message(f"加载数据库文件失败: {str(e)}", "ERROR")
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
    """通过API抓取用户信息"""
    log_message("开始从API抓取用户信息")
    
    try:
        # 使用管理员凭据进行认证
        # 在实际环境中，应该使用更安全的认证方式
        headers = {
            "User-Agent": "PasswordManager/1.0"
        }
        auth = (API_USERNAME, API_PASSWORD)  # 基本认证
        
        response = requests.get(
            API_URL,
            auth=auth,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            log_message(f"成功从API获取到 {len(users)} 个用户")
            return users
        elif response.status_code == 401:
            log_message("API认证失败，检查管理员凭据", "ERROR")
            # 尝试直接从文件读取
            log_message("尝试直接从文件读取用户数据")
            database = load_database()
            if database:
                return database.get("users", [])
            return []
        elif response.status_code == 403:
            log_message("API访问被拒绝，权限不足", "ERROR")
            # 尝试直接从文件读取
            log_message("尝试直接从文件读取用户数据")
            database = load_database()
            if database:
                return database.get("users", [])
            return []
        else:
            log_message(f"API请求失败，状态码: {response.status_code}", "ERROR")
            # 如果API访问失败，尝试直接从文件读取
            log_message("尝试直接从文件读取用户数据")
            database = load_database()
            if database:
                return database.get("users", [])
            return []
    
    except requests.exceptions.RequestException as e:
        log_message(f"API请求异常: {str(e)}", "ERROR")
        # 如果API访问失败，尝试直接从文件读取
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
            user["first"] = 1  # 标记为已完成首次登录密码更新
            updated_count += 1
            log_message(f"已更新用户 {user.get('username', '未知用户')} 的密码并设置first=1")
    
    log_message(f"密码更新完成，共更新了 {updated_count} 个用户")
    return updated_count

def create_default_users():
    """创建默认用户列表"""
    # 创建默认用户数据
    default_users = [
        {
            "id": 1,
            "username": "UIO",
            "password": "328817",
            "role": "SUPER_ADMIN",
            "position": "LEADER",
            "lastPasswordChange": int(datetime.now().timestamp() * 1000),
            "confirmed": True,
            "first": 1
        },
        {
            "id": 2,
            "username": "admin1",
            "password": "admin123",
            "role": "ADMIN",
            "position": "DEPUTYLEADER",
            "lastPasswordChange": int(datetime.now().timestamp() * 1000),
            "confirmed": True,
            "first": 0
        },
        {
            "id": 3,
            "username": "user1",
            "password": "user123",
            "role": "MEMBER",
            "position": "STAFF",
            "lastPasswordChange": int(datetime.now().timestamp() * 1000),
            "confirmed": True,
            "first": 0
        }
    ]
    log_message(f"创建了 {len(default_users)} 个默认用户")
    return default_users

def main():
    """主函数"""
    log_message("====================================")
    log_message("用户密码更新器启动")
    log_message("====================================")
    
    # 1. 加载本地数据库
    log_message("步骤1: 加载本地数据库")
    database = load_database()
    
    # 2. 从API抓取用户信息
    log_message("步骤2: 从API抓取用户信息")
    users = fetch_users_from_api()
    
    # 如果API和数据库都没有数据，创建默认用户
    if not database and not users:
        log_message("未获取到用户数据，创建默认用户", "WARNING")
        users = create_default_users()
    
    if not users:
        log_message("未获取到用户数据，程序退出", "ERROR")
        return
    
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
        existing_usernames = {user.get('username') for user in database.get('users', []) if user.get('username')}
        existing_emails = {user.get('email') for user in database.get('users', []) if user.get('email')}
        
        added_count = 0
        for user in users:
            username = user.get('username')
            email = user.get('email')
            
            # 检查用户是否已存在（通过用户名或邮箱）
            if username and username in existing_usernames:
                log_message(f"用户 {username} 已存在，跳过添加")
                continue
            if email and email in existing_emails:
                log_message(f"用户邮箱 {email} 已存在，跳过添加")
                continue
                
            # 添加新用户
            database['users'].append(user)
            added_count += 1
            log_message(f"已添加新用户: {username or email}")
        
        log_message(f"用户数据处理完成，新增了 {added_count} 个用户")
    
    # 3. 更新FIRST项为0的用户密码
    log_message("步骤3: 更新FIRST项为0的用户密码")
    updated_count = update_first_login_passwords(database["users"])
    
    # 4. 保存更新后的数据库
    if updated_count > 0:
        log_message("步骤4: 保存更新后的数据库")
        if save_database(database):
            log_message(f"成功保存数据库，共更新了 {updated_count} 个用户密码")
        else:
            log_message("保存数据库失败", "ERROR")
    else:
        log_message("没有用户需要更新密码")
    
    # 5. 显示统计信息
    log_message("====================================")
    log_message("执行统计:")
    log_message(f"- 总用户数: {len(users)}")
    log_message(f"- 更新密码用户数: {updated_count}")
    log_message(f"- 剩余待更新用户数: {sum(1 for u in users if u.get('first') == 0)}")
    log_message("====================================")
    log_message("用户密码更新器执行完成")


if __name__ == "__main__":
    main()