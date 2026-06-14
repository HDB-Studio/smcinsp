// 数据库管理器 - 模拟JSON文件数据库操作
// 由于浏览器环境限制，实际使用localStorage存储，但提供类似文件数据库的接口

class DatabaseManager {
    constructor() {
        this.dbPath = 'data/database.json';
        this.localStorageKey = 'kl_workshop_database';
        this.initializeDatabase();
    }

    /**
     * 初始化数据库
     */
    initializeDatabase() {
        // 检查localStorage中是否已有数据库
        if (!localStorage.getItem(this.localStorageKey)) {
            // 首次初始化，使用默认数据结构
            const defaultDatabase = {
                users: [
                    {
                        id: 1,
                        email: "UIO",
                        password: "328817",
                        role: "SUPER_ADMIN",
                        lastPasswordChange: Date.now(),
                        confirmed: true,
                        position: "LEADER",
                        first: 0,
                        username: "超级管理员",
                        avatar: "",
                        phone: "",
                        gender: "",
                        birthday: "",
                        introduction: "",
                        joinDate: new Date().toISOString(),
                        lastLogin: null,
                        status: "ACTIVE"
                    },
                    {
                        id: 2,
                        email: "KL_工作室创始人",
                        password: "initial123",
                        role: "ADMIN",
                        position: "LEADER",
                        lastPasswordChange: Date.now(),
                        confirmed: true,
                        first: 0,
                        username: "KL_工作室创始人",
                        avatar: "",
                        phone: "",
                        gender: "",
                        birthday: "",
                        introduction: "",
                        joinDate: new Date().toISOString(),
                        lastLogin: null,
                        status: "ACTIVE"
                    },
                    {
                        id: 3,
                        email: "KL_副室长",
                        password: "initial123",
                        role: "MEMBER",
                        position: "DEPUTYLEADER",
                        lastPasswordChange: Date.now(),
                        confirmed: true,
                        first: 0,
                        username: "KL_副室长",
                        avatar: "",
                        phone: "",
                        gender: "",
                        birthday: "",
                        introduction: "",
                        joinDate: new Date().toISOString(),
                        lastLogin: null,
                        status: "ACTIVE"
                    },
                    {
                        id: 4,
                        email: "KL_核心成员",
                        password: "initial123",
                        role: "MEMBER",
                        position: "STAFF",
                        lastPasswordChange: Date.now(),
                        confirmed: true,
                        first: 0,
                        username: "KL_核心成员",
                        avatar: "",
                        phone: "",
                        gender: "",
                        birthday: "",
                        introduction: "",
                        joinDate: new Date().toISOString(),
                        lastLogin: null,
                        status: "ACTIVE"
                    }
                ],
                applications: [],
                settings: {
                    systemName: "KL工作室人员管理系统",
                    version: "1.0.0",
                    passwordExpiryDays: 30,
                    cookieExpiryDays: 1
                }
            };
            
            localStorage.setItem(this.localStorageKey, JSON.stringify(defaultDatabase));
            console.log('数据库已初始化，包含超级管理员和个人信息字段');
        } else {
            // 确保现有用户数据中包含所需字段
            this.ensureUserFieldsExist();
        }
    }
    
    /**
     * 确保所有用户都有必要的字段
     */
    ensureUserFieldsExist() {
        const users = this.getUsers();
        let updated = false;
        const requiredFields = {
            first: 0,
            username: '',
            avatar: '',
            phone: '',
            gender: '',
            birthday: '',
            introduction: '',
            joinDate: new Date().toISOString(),
            lastLogin: null,
            status: 'ACTIVE'
        };
        
        for (let user of users) {
            // 检查每个必需字段
            for (let [field, defaultValue] of Object.entries(requiredFields)) {
                if (typeof user[field] === 'undefined') {
                    user[field] = defaultValue;
                    updated = true;
                }
            }
        }
        
        if (updated) {
            this.saveUsers(users);
            console.log('已为所有用户添加必要的个人信息字段');
        }
    }
    
    /**
     * 获取完整数据库
     */
    getDatabase() {
        const dbData = localStorage.getItem(this.localStorageKey);
        return dbData ? JSON.parse(dbData) : null;
    }

    /**
     * 保存数据库
     */
    saveDatabase(database) {
        localStorage.setItem(this.localStorageKey, JSON.stringify(database));
        return true;
    }

    /**
     * 获取用户列表
     */
    getUsers() {
        const db = this.getDatabase();
        return db ? db.users : [];
    }

    /**
     * 保存用户列表
     */
    saveUsers(users) {
        const db = this.getDatabase();
        if (!db) return false;
        
        db.users = users;
        return this.saveDatabase(db);
    }

    /**
     * 获取申请列表
     */
    getApplications() {
        const db = this.getDatabase();
        return db ? db.applications : [];
    }

    /**
     * 保存申请列表
     */
    saveApplications(applications) {
        const db = this.getDatabase();
        if (!db) return false;
        
        db.applications = applications;
        return this.saveDatabase(db);
    }

    /**
     * 添加申请
     */
    addApplication(application) {
        try {
            const applications = this.getApplications();
            application.id = Math.max(...applications.map(a => a.id || 0), 0) + 1;
            application.submitTime = new Date().toISOString();
            application.status = 'PENDING';
            
            applications.push(application);
            this.saveApplications(applications);
            return application;
        } catch (error) {
            console.error('添加申请失败:', error);
            return null;
        }
    }

    /**
     * 更新申请状态
     */
    updateApplicationStatus(applicationId, status, comment) {
        try {
            const applications = this.getApplications();
            const application = applications.find(a => a.id === applicationId);
            
            if (!application) return false;
            
            application.status = status;
            application.processTime = new Date().toISOString();
            application.comment = comment;
            
            this.saveApplications(applications);
            return true;
        } catch (error) {
            console.error('更新申请状态失败:', error);
            return false;
        }
    }

    /**
     * 根据邮箱查找用户
     */
    findUserByEmail(email) {
        const users = this.getUsers();
        return users.find(user => user.email === email);
    }
    
    /**
     * 根据ID查找用户
     */
    findUserById(id) {
        const users = this.getUsers();
        return users.find(user => user.id === id);
    }
    
    /**
     * 检查用户是否为超级管理员
     */
    isSuperAdmin(email) {
        const user = this.findUserByEmail(email);
        return user && user.role === 'SUPER_ADMIN';
    }
    
    /**
     * 获取所有管理员（包括超级管理员和普通管理员）
     */
    getAdmins() {
        const users = this.getUsers();
        return users.filter(user => user.role === 'SUPER_ADMIN' || user.role === 'ADMIN');
    }

    /**
     * 添加新用户
     */
    addUser(user) {
        try {
            const users = this.getUsers();
            
            // 检查邮箱是否已存在
            const existingUser = users.find(u => u.email === user.email);
            if (existingUser) {
                console.warn(`用户邮箱已存在: ${user.email}`);
                return false;
            }
            
            // 生成唯一ID
            user.id = Math.max(...users.map(u => u.id), 0) + 1;
            
            // 设置默认值
            user.lastPasswordChange = Date.now();
            user.confirmed = true;
            user.first = 0;
            
            // 添加用户
            users.push(user);
            this.saveUsers(users);
            return true;
        } catch (error) {
            console.error('添加用户失败:', error);
            return false;
        }
    }

    /**
     * 更新用户信息
     */
    updateUser(email, updates) {
        try {
            const users = this.getUsers();
            const userIndex = users.findIndex(u => u.email === email);
            
            if (userIndex === -1) return false;
            
            // 合并更新
            users[userIndex] = { ...users[userIndex], ...updates };
            this.saveUsers(users);
            return true;
        } catch (error) {
            console.error('更新用户信息失败:', error);
            return false;
        }
    }

    /**
     * 删除用户
     */
    deleteUser(email) {
        try {
            const users = this.getUsers();
            const filteredUsers = users.filter(u => u.email !== email);
            
            if (filteredUsers.length === users.length) return false;
            
            this.saveUsers(filteredUsers);
            return true;
        } catch (error) {
            console.error('删除用户失败:', error);
            return false;
        }
    }

    /**
     * 更改用户密码
     */
    changePassword(email, newPassword) {
        return this.updateUser(email, {
            password: newPassword,
            lastPasswordChange: Date.now()
        });
    }

    /**
     * 获取系统设置
     */
    getSettings() {
        const db = this.getDatabase();
        return db ? db.settings : null;
    }

    /**
     * 更新系统设置
     */
    updateSettings(settings) {
        const db = this.getDatabase();
        if (!db) return false;
        
        db.settings = { ...db.settings, ...settings };
        return this.saveDatabase(db);
    }

    /**
     * 获取系统版本
     */
    getVersion() {
        const settings = this.getSettings();
        return settings ? settings.version : '1.0.0';
    }

    /**
     * 重置数据库到默认状态
     */
    resetDatabase() {
        try {
            localStorage.removeItem(this.localStorageKey);
            this.initializeDatabase();
            return true;
        } catch (error) {
            console.error('重置数据库失败:', error);
            return false;
        }
    }

    /**
     * 导出数据库（返回JSON字符串）
     */
    exportDatabase() {
        try {
            const db = this.getDatabase();
            return db ? JSON.stringify(db, null, 2) : null;
        } catch (error) {
            console.error('导出数据库失败:', error);
            return null;
        }
    }

    /**
     * 导入数据库（从JSON字符串）
     */
    importDatabase(jsonData) {
        try {
            const database = JSON.parse(jsonData);
            // 验证数据库结构
            if (!database.users || !Array.isArray(database.users)) {
                throw new Error('无效的数据库结构');
            }
            
            this.saveDatabase(database);
            return true;
        } catch (error) {
            console.error('导入数据库失败:', error);
            return false;
        }
    }
}

// 创建单例实例
const databaseManager = new DatabaseManager();

// 在浏览器环境中，将databaseManager暴露到window对象上
if (window) {
    window.databaseManager = databaseManager;
    console.log('数据库管理器已成功加载并暴露到window对象');
    console.log(`当前数据库版本: ${databaseManager.getVersion()}`);
}

// 为了兼容性，确保模块导出不会在浏览器环境中导致语法错误
if (typeof module !== 'undefined' && module.exports) {
    module.exports = databaseManager;
}