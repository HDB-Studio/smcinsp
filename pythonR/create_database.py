#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认数据库文件
"""

import json
import os
from datetime import datetime

# 数据库文件路径
DATABASE_PATH = os.path.join("data", "database.json")

# 创建默认数据库数据
default_database = {
    "users": [
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
    ],
    "applications": [],
    "settings": {
        "systemName": "KL工作室人员管理系统",
        "version": "1.0.0",
        "passwordExpiryDays": 30,
        "cookieExpiryDays": 1
    }
}

# 确保目录存在
os.makedirs("data", exist_ok=True)

# 写入数据库文件
try:
    with open(DATABASE_PATH, "w", encoding="utf-8") as f:
        json.dump(default_database, f, ensure_ascii=False, indent=2)
    print(f"成功创建数据库文件: {DATABASE_PATH}")
    print(f"创建了 {len(default_database['users'])} 个用户")
except Exception as e:
    print(f"创建数据库文件失败: {e}")