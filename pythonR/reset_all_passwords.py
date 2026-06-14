import json
import time

# 数据库文件路径
DATABASE_PATH = "d:\\Users\\Administrator\\Desktop\\142\\data\\database.json"

# 设置的统一初始密码
UNIFIED_PASSWORD = "initial123"

def reset_all_user_passwords():
    try:
        # 读取数据库文件
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            database = json.load(f)
        
        # 获取用户列表
        users = database.get('users', [])
        
        # 为所有用户设置统一密码
        updated_count = 0
        for user in users:
            old_password = user.get('password', '')
            user['password'] = UNIFIED_PASSWORD
            user['lastPasswordChange'] = int(time.time() * 1000)
            updated_count += 1
            print(f"已重置用户 '{user.get('username', 'Unknown')}' 的密码")
        
        # 保存更新后的数据库
        with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        
        print(f"\n密码重置完成！共更新了 {updated_count} 个用户的密码")
        print(f"所有用户现在可以使用统一密码登录: {UNIFIED_PASSWORD}")
        
    except Exception as e:
        print(f"重置密码时出错: {str(e)}")

if __name__ == "__main__":
    print("正在重置所有用户密码...")
    reset_all_user_passwords()