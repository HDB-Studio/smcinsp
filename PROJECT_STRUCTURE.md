# 项目结构说明

## 主要文件

- **user_password_updater_gui.py**: 主程序文件，包含密码更新的GUI界面和核心逻辑
- **user_password_updater.py**: 命令行版本的密码更新工具
- **user_password_manager.py**: 密码管理器核心功能
- **create_database.py**: 数据库创建脚本
- **migrate_database.py**: 数据库迁移工具
- **reset_all_passwords.py**: 重置所有用户密码的工具

## 测试目录

所有测试和验证相关的脚本都集中在 `tests/` 目录下：

- **tests/analyze_user_count.py**: 用户数量分析工具
- **tests/fix_first_field.py**: first字段修复工具
- **tests/test_fix.py**: 修复功能测试
- **tests/test_first_zero_update.py**: first=0密码更新逻辑测试
- **tests/test_password_manager.py**: 密码管理器测试
- **tests/verify_changes.py**: 变更验证工具
- **tests/verify_database_and_security.py**: 数据库和安全验证
- **tests/verify_first_field.py**: first字段验证工具

## 前端文件

- **index.html**: 主页面
- **dashboard.html**: 仪表盘页面
- **firstPage.html**: 第一页
- **secondPage.html**: 第二页
- **superAdminDashboard.html**: 超级管理员仪表盘
- **test_database_manager.html**: 数据库管理器测试页面

## JavaScript文件

- **apiValidator.js**: API验证器
- **databaseManager.js**: 数据库管理器
- **databaseManager_clean.js**: 清理版数据库管理器
- **securityManager.js**: 安全管理器
- **test_fixes.js**: 修复测试脚本
- **userLoginTracker.js**: 用户登录跟踪器
- **userManagement.js**: 用户管理模块

## 资源目录

- **css/**: 样式文件目录
- **data/**: 数据存储目录
- **fonts/**: 字体文件目录
- **img/**: 图片资源目录

## 说明文档

- **README.md**: 项目说明文档
- **PASSWORD_MANAGER_README.md**: 密码管理器说明文档
- **PROJECT_STRUCTURE.md**: 项目结构说明（当前文件）

## 注意事项

1. 所有测试脚本已经统一整理到tests目录，便于管理和维护
2. 不再需要的日志文件已清理，减少磁盘占用
3. 主程序文件保持在根目录，确保直接运行时能够正确加载依赖
4. 用户计数功能已修复，确保通过用户ID（转换为字符串类型）进行唯一性检查，避免重复添加用户