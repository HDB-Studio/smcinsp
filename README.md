# KL工作室人員管理後臺

这是KL工作室的人員管理後臺系统，包含登录页面、自动登录功能、控制面板和JSON数据库管理功能。

## 功能特性

- 登录页面带邮箱和密码输入
- 自动登录选项，保存用户邮箱
- 登录后的控制面板页面
- 侧边栏菜单交互
- JSON数据库实现（使用localStorage模拟）
- 数据库管理器提供完整的CRUD操作
- 作品申请提交和审批功能
- 身份验证和Cookie验证机制

## 文件结构

```
├── css/                 # 样式文件
│   ├── font-awesome.min.css
│   ├── main.css
│   └── util.css
├── data/                # 数据目录
│   └── database.json    # JSON数据库文件
├── fonts/               # 字体文件
├── img/                 # 图片资源
├── index.html           # 登录页面
├── dashboard.html       # 登录后的控制面板
├── databaseManager.js   # 数据库管理器
├── userManagement.js    # 用户管理模块
├── apiValidator.js      # API验证模块
├── testDatabase.html    # 数据库测试工具
└── README.md            # 项目说明
```

## 如何使用

### 1. 打开登录页面

直接在浏览器中打开 `index.html` 文件即可看到登录页面。

### 2. 登录功能

- 输入邮箱和密码
- 可选勾选"自动登录"选项，下次访问时会自动填充邮箱
- 点击"登录"按钮跳转到控制面板

### 3. 数据库设置

本项目使用JSON数据库实现数据持久化，通过以下方式管理：

### JSON数据库实现

#### 数据存储方式
- **主要存储**：使用浏览器的localStorage模拟数据库
- **数据文件**：`data/database.json`（可通过测试工具导出）
- **数据库管理器**：`databaseManager.js` 提供完整的数据操作接口

#### 数据结构

```json
{
  "users": [
    {
      "id": 1,
      "email": "EX",
      "password": "1234556",
      "role": "ADMIN",
      "position": "LEADER",
      "lastPasswordChange": 1700000000000,
      "confirmed": true
    }
  ],
  "applications": [],
  "settings": {
    "systemName": "KL工作室人员管理系统",
    "version": "1.0.0"
  }
}
```

#### 默认账户
系统自动创建以下默认账户：
- **管理员**: 邮箱 `UIO`，密码 `328817`
- **成员账户**: 邮箱 `KL_工作室创始人`、`KL_副室长`、`KL_核心成员`，密码均为 `initial123`

### 数据库测试工具

打开 `testDatabase.html` 可以测试以下功能：
- 数据库连接测试
- 用户CRUD操作
- 申请数据管理
- 数据库导出导入
- 数据库重置

### 使用示例

```javascript
// 获取数据库管理器实例
const dbManager = window.databaseManager;

// 添加新申请
dbManager.addApplication({
    title: "测试作品",
    category: "技术类",
    description: "作品描述",
    contactInfo: "联系方式",
    authorName: "作者名称",
    authorEmail: "author@example.com"
});

// 获取所有申请
const applications = dbManager.getApplications();

// 更新申请状态
dbManager.updateApplicationStatus(applicationId, "APPROVED", "admin@example.com");
```

## 开发说明

- **功能扩展**: 可以在 `dashboard.html` 中添加更多功能模块
- **数据库管理**: 通过 `databaseManager.js` 提供的API进行数据操作
- **数据导出**: 定期使用测试工具导出数据库进行备份
- **安全注意事项**:
  - 当前实现使用前端存储，仅适用于演示和学习
  - 密码以明文形式存储，实际应用需进行加密处理
  - 生产环境应使用后端数据库和服务器端验证

### 主要模块

1. **数据库管理器 (databaseManager.js)**
   - 提供完整的CRUD操作接口
   - 支持数据导入导出
   - 管理用户、申请和系统设置

2. **用户管理模块 (userManagement.js)**
   - 用户认证和权限控制
   - 密码管理
   - 申请审批处理

3. **API验证模块 (apiValidator.js)**
   - 用户身份验证
   - Cookie验证机制
   - 带动画效果的日志弹窗

## 浏览器兼容性

该系统使用了现代HTML5和CSS3技术，建议在以下浏览器中使用：
- Chrome 49+ 
- Firefox 45+ 
- Safari 9+ 
- Edge 12+