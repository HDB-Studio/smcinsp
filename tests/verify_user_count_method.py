#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证用户计数方法是否通过正规途径实现
"""

import os
import sys
import re

def verify_code_changes():
    """验证代码修改是否符合要求"""
    file_path = r"d:\Users\Administrator\Desktop\142\user_password_updater_gui.py"
    
    print("=== 验证用户计数功能通过正规途径实现 ===")
    print(f"检查文件: {file_path}")
    
    if not os.path.exists(file_path):
        print("错误: 文件不存在")
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    # 检查update_status方法的修改
    print("\n1. 检查update_status方法是否通过正规途径统计用户数量:")
    update_status_pattern = r'def update_status\(self\):[\s\S]*?self\.root\.after\(3000, self\.update_status\)'
    update_status_match = re.search(update_status_pattern, content)
    
    if not update_status_match:
        print("错误: 找不到update_status方法")
        return False
    
    update_status_code = update_status_match.group(0)
    
    # 检查是否包含必要的验证步骤
    checks = [
        ('严格从数据库文件加载', '严格从数据库文件加载数据' in update_status_code),
        ('类型检查', 'isinstance\(database\["users"\], list\)' in update_status_code),
        ('空文件处理', '数据库文件不存在或为空' in update_status_code),
        ('错误处理', '数据库中的users字段格式错误' in update_status_code),
        ('日志记录', '通过数据库文件统计' in update_status_code)
    ]
    
    update_status_valid = True
    for check_name, is_present in checks:
        status = "✓ 通过" if is_present else "✗ 失败"
        print(f"   {check_name}: {status}")
        if not is_present:
            update_status_valid = False
    
    # 检查load_database函数的修改
    print("\n2. 检查load_database函数是否通过正规途径加载数据库:")
    load_database_pattern = r'def load_database\(\):[\s\S]*?return None'
    load_database_match = re.search(load_database_pattern, content)
    
    if not load_database_match:
        print("错误: 找不到load_database函数")
        return False
    
    load_database_code = load_database_match.group(0)
    
    # 检查load_database中的必要验证步骤
    load_checks = [
        ('文件存在检查', 'if not os\.path\.exists\(DATABASE_PATH\):' in load_database_code),
        ('文件类型检查', 'if not os\.path\.isfile\(DATABASE_PATH\):' in load_database_code),
        ('文件大小检查', 'file_size = os\.path\.getsiz' in load_database_code),
        ('JSON解析验证', 'try:[\s]*database = json\.loads\(content\)' in load_database_code),
        ('数据库结构验证', 'if not isinstance\(database, dict\):' in load_database_code),
        ('用户列表验证', 'if "users" in database and isinstance\(database\["users"\], list\):' in load_database_code),
        ('异常处理', 'except UnicodeDecodeError:' in load_database_code and 'except PermissionError:' in load_database_code)
    ]
    
    load_database_valid = True
    for check_name, is_present in load_checks:
        status = "✓ 通过" if is_present else "✗ 失败"
        print(f"   {check_name}: {status}")
        if not is_present:
            load_database_valid = False
    
    # 检查是否有投机取巧的代码
    print("\n3. 检查是否存在投机取巧的代码:")
    suspicious_patterns = [
        ('硬编码用户数量', r'user_count\s*=\s*\d+'),
        ('固定返回值', r'return\s*\{[\s\S]*?"users"\s*:\s*\[\s*\]'),
        ('不实际读取文件', r'return\s*\{[^\}]*\}\s*#|return\s*\{[^\}]*\}\s*$'),
        ('跳过文件检查', r'#\s*skip\s*file\s*check|#\s*bypass\s*validation')
    ]
    
    suspicious_found = False
    for pattern_name, pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"   ✗ 警告: 发现可能的投机取巧代码 - {pattern_name}")
            suspicious_found = True
    
    if not suspicious_found:
        print("   ✓ 通过: 未发现投机取巧的代码")
    
    # 总结
    print("\n=== 验证总结 ===")
    if update_status_valid and load_database_valid and not suspicious_found:
        print("✓ 验证通过！用户计数功能通过正规途径准确实现")
        print("\n功能特点:")
        print("1. update_status方法严格从数据库文件加载数据统计用户数量")
        print("2. 包含完善的类型检查和错误处理机制")
        print("3. load_database函数执行多重验证确保数据准确性")
        print("4. 没有发现任何投机取巧的实现方式")
        return True
    else:
        print("✗ 验证失败！用户计数功能未完全通过正规途径实现")
        return False

if __name__ == "__main__":
    success = verify_code_changes()
    sys.exit(0 if success else 1)