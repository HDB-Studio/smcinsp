import json
import os

# 数据库文件路径
DATABASE_PATH = r"d:\Users\Administrator\Desktop\142\data\database.json"

def migrate_database():
    """迁移数据库：将所有用户的email字段重命名为username"""
    print("开始数据库迁移...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"错误：数据库文件 {DATABASE_PATH} 不存在")
        return False
    
    try:
        # 读取数据库
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            database = json.load(f)
        
        users = database.get("users", [])
        migrated_count = 0
        
        # 迁移每个用户的email字段为username
        for user in users:
            if "email" in user and "username" not in user:
                # 保留email字段的值到username
                user["username"] = user["email"]
                # 删除email字段
                del user["email"]
                migrated_count += 1
            elif "email" in user and "username" in user:
                # 如果两个字段都存在，保持username不变，删除email
                del user["email"]
                migrated_count += 1
        
        # 保存更新后的数据库
        with open(DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        
        print(f"数据库迁移完成！共迁移了 {migrated_count} 个用户记录")
        print("所有用户记录中的'email'字段已重命名为'username'字段")
        return True
        
    except Exception as e:
        print(f"数据库迁移失败：{str(e)}")
        return False

if __name__ == "__main__":
    migrate_database()