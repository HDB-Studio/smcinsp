# 用户密码自动管理器使用说明

本文档详细介绍了用户密码自动管理系统的功能、配置和使用方法。

## 功能概述

该系统实现了以下核心功能：

1. **定期用户数据抓取**：每10分钟从API抓取一次用户名信息
2. **自动密码更新**：每30分钟检查一次，自动为`first`字段值为0的用户更新为8位复杂密码
3. **登录状态跟踪**：用户首次登录后，自动将其`first`字段设置为1，不再自动更新密码
4. **数据持久化**：用户数据存储在JSON文件中，确保数据安全

## 文件结构

```
142/
├── user_password_manager.py    # 主Python脚本，实现核心功能
├── test_password_manager.py    # 测试脚本，验证功能正确性
├── userLoginTracker.js         # 前端登录跟踪器
├── databaseManager.js          # 数据库管理器（已更新支持first字段）
├── index.html                  # 登录页面（已集成登录跟踪）
└── data/
    └── database.json           # 数据存储文件
```

## API配置说明

根据编程猫API文档，系统使用以下API端点：

- **基础URL**: `https://api.codemao.cn`
- **工作室成员API**: `/web/shops/<workshop_id>/users`

### 配置参数说明

在运行脚本前，请确保正确配置`user_password_manager.py`中的以下参数：

```python
# API配置 - 重要：请根据实际情况修改
API_URL = "https://api.codemao.cn"  # 基础API URL，不要修改
WORKSHOP_ID = 25294  # 请替换为您的工作室ID

# 数据库文件路径
DATABASE_PATH = "d:\\Users\\Administrator\\Desktop\\142\\data\\database.json"

# 时间间隔配置（秒）
USER_FETCH_INTERVAL = 10 * 60  # 每10分钟抓取一次用户名
PASSWORD_UPDATE_INTERVAL = 30 * 60  # 每30分钟检查并更新密码

# 日志文件路径
LOG_FILE = "d:\\Users\\Administrator\\Desktop\\142\\user_password_manager.log"
```

### API调用机制

- 系统会定期调用编程猫API获取工作室成员列表
- API返回的数据包含用户的姓名、职位、角色等信息
- 如果API调用失败，系统会自动切换到备用的模拟数据，确保程序继续运行
- 所有API操作都有详细的日志记录，便于排查问题

### API数据结构

API返回的数据格式如下：
```json
{
  "items": [
    {
      "id": 1,
      "name": "用户名",
      "user_id": 1001,
      "position": "LEADER",  // 职位：LEADER、DEPUTYLEADER、STAFF
      "role": 1,  // 角色ID
      "status": 1,
      "avatar_url": "头像URL"
    },
    ...
  ],
  "offset": 0,
  "limit": 20,
  "total": 3,
  "counted": true
}

## 运行方法

### 1. 首先测试脚本功能

在运行主脚本前，建议先运行测试脚本验证功能正确性：

```bash
python test_password_manager.py
```

### 2. 启动主程序

测试通过后，可以启动主程序：

```bash
python user_password_manager.py
```

程序将在后台持续运行，执行以下操作：
- 每10分钟抓取一次用户数据
- 每30分钟检查并更新密码
- 所有操作记录将写入日志文件

### 3. 前端集成

前端系统已自动集成了登录状态跟踪功能：
- 当用户登录成功时，`userLoginTracker.js`会自动将用户的`first`字段设置为1
- 已登录过的用户（`first=1`）不会再被自动更新密码

## 密码生成规则

系统生成的8位复杂密码满足以下条件：
- 长度固定为8位
- 包含至少一个数字
- 包含至少一个特殊字符（!@#$%^&*()）
- 包含大小写字母

## 日志记录

系统运行过程中的所有操作都会记录到日志文件中：
- 用户数据抓取记录
- 密码更新记录（包括更新的用户名和新密码）
- 错误信息和异常

可以通过查看日志文件监控系统运行状态。

## 常见问题

### 1. 数据库文件不存在

系统会自动创建必要的数据目录和数据库文件，无需手动创建。

### 2. API连接失败

如果无法连接到实际API，系统会使用模拟数据进行测试。在生产环境中，请确保API配置正确。

### 3. 如何手动更新用户状态

可以在Python脚本中调用以下函数：

```python
# 将指定用户标记为已登录
update_user_first_status("用户名")
```

### 4. 如何停止脚本

可以使用`Ctrl+C`组合键停止运行中的Python脚本。

## 安全注意事项

1. 日志文件中包含用户密码信息，请妥善保管
2. 建议定期备份数据库文件
3. 生产环境中应确保API连接使用安全的认证方式

## 维护说明

- 定期检查日志文件，确保系统正常运行
- 如需修改时间间隔，直接编辑配置参数即可
- 数据库文件可以手动编辑，但请确保格式正确