// 用户管理和权限控制系统
// 使用数据库管理器处理数据存储

class UserManager {
    constructor() {
        this.superAdminRole = 'SUPER_ADMIN';
        this.adminRole = 'ADMIN';
        this.memberRole = 'MEMBER';
        this.passwordExpiry = 30 * 60 * 1000; // 30分钟
        // 引用数据库管理器
        this.dbManager = window.databaseManager;
        this.initialize();
    }

    /**
     * 初始化用户管理系统
     */
    initialize() {
        // 使用databaseManager进行初始化
        // databaseManager已经在构造函数中初始化了默认数据
        console.log('用户管理系统已初始化');
    }

    /**
     * 从数据库获取用户列表
     */
    getUsers() {
        // 使用databaseManager获取用户数据
        return window.databaseManager ? window.databaseManager.getUsers() : [];
    }

    /**
     * 保存用户列表到数据库
     */
    saveUsers(users) {
        // 使用databaseManager保存用户数据
        return window.databaseManager ? window.databaseManager.saveUsers(users) : false;
    }

    /**
     * 登录验证
     */
    async login(username, password) {
        const users = this.getUsers();
        // 同时支持通过email或username登录
        const user = users.find(u => u.email === username || u.username === username);
        
        if (!user) {
            return { success: false, message: '用户不存在' };
        }

        // 检查密码是否过期（非管理员且密码已存在超过30分钟）
        const isExpired = (user.role !== this.adminRole && user.role !== this.superAdminRole) && 
                        user.lastPasswordChange && 
                        Date.now() - user.lastPasswordChange > this.passwordExpiry;

        // 验证密码
        const isPasswordValid = password === user.password;
        
        if (!isPasswordValid) {
            return { success: false, message: '密码错误' };
        }

        // 登录成功，更新lastLogin字段
        user.lastLogin = Date.now();
        this.saveUsers(users);
        
        // 记录用户信息
        this.setCurrentUser(user);
        
        return {
            success: true,
            user: user,
            isPasswordExpired: isExpired,
            needsConfirmation: !user.confirmed
        };
    }

    /**
     * 设置当前登录用户
     */
    setCurrentUser(user) {
        // 保持session数据在localStorage中
        localStorage.setItem('currentUser', JSON.stringify(user));
    }

    /**
     * 获取当前登录用户
     */
    getCurrentUser() {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * 登出
     */
    logout() {
        localStorage.removeItem('currentUser');
    }

    /**
     * 检查是否为管理员
     */
    isAdmin() {
        const user = this.getCurrentUser();
        return user && (user.role === this.adminRole || user.role === this.superAdminRole);
    }
    
    /**
     * 检查是否为超级管理员
     * @param {Object} user - 可选，要检查的用户对象，如果不提供则使用当前登录用户
     */
    isSuperAdmin(user = null) {
        const targetUser = user || this.getCurrentUser();
        return targetUser && targetUser.role === this.superAdminRole;
    }

    /**
     * 获取工作室成员列表并自动注册账户
     */
    async autoRegisterMembers() {
        try {
            // 模拟工作室成员数据（由于浏览器环境限制，直接使用模拟数据）
            const members = {
                items: [
                    {
                        id: 1,
                        name: 'KL_工作室创始人',
                        user_id: 1001,
                        position: 'LEADER',
                        role: 1,
                        status: 1,
                        avatar_url: 'https://example.com/avatar1.png'
                    },
                    {
                        id: 2,
                        name: 'KL_副室长',
                        user_id: 1002,
                        position: 'DEPUTYLEADER',
                        role: 2,
                        status: 1,
                        avatar_url: 'https://example.com/avatar2.png'
                    },
                    {
                        id: 3,
                        name: 'KL_核心成员',
                        user_id: 1003,
                        position: 'STAFF',
                        role: 3,
                        status: 1,
                        avatar_url: 'https://example.com/avatar3.png'
                    }
                ]
            };
            
            let users = this.getUsers();
            const newUsers = [];
            
            // 为每个成员创建账户
            members.items.forEach(member => {
                // 检查是否已存在
                if (!users.some(u => u.email === member.name)) {
                    const randomPassword = this.generateRandomPassword();
                    const newUser = {
                        email: member.name,
                        password: randomPassword,
                        role: this.memberRole,
                        position: member.position,
                        lastPasswordChange: Date.now(),
                        confirmed: false,
                        originalPassword: randomPassword
                    };
                    
                    users.push(newUser);
                    newUsers.push(newUser);
                    console.log(`已为 ${member.name} 创建账户，初始密码: ${randomPassword}`);
                }
            });
            
            // 保存更新后的用户列表
            this.saveUsers(users);
            
            return { success: true, newUsers: newUsers };
        } catch (error) {
            console.error('自动注册成员失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 生成随机密码
     */
    generateRandomPassword() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
        let password = '';
        for (let i = 0; i < 8; i++) {
            password += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return password;
    }

    /**
     * 更新用户密码
     */
    updatePassword(email, newPassword, isSuperAdminAction = false) {
        const users = this.getUsers();
        const userIndex = users.findIndex(u => u.email === email || u.username === email);
        
        if (userIndex === -1) {
            return { success: false, message: '用户不存在' };
        }
        
        const user = users[userIndex];
        const oldPassword = user.password;
        
        // 更新密码和时间戳
        user.password = newPassword;
        user.lastPasswordChange = Date.now();
        
        // 如果是首次确认，更新状态
        if (!user.confirmed) {
            user.confirmed = true;
        }
        
        // 如果是首次登录后修改密码，更新first字段
        if (!isSuperAdminAction && user.first === 0) {
            user.first = 1;
        }
        
        this.saveUsers(users);
        
        // 更新当前用户信息
        const currentUser = this.getCurrentUser();
        if (currentUser && (currentUser.email === email || currentUser.username === email)) {
            currentUser.password = newPassword;
            currentUser.lastPasswordChange = Date.now();
            currentUser.confirmed = user.confirmed;
            if (user.first === 1) {
                currentUser.first = 1;
            }
            this.setCurrentUser(currentUser);
        }
        
        // 记录密码更改日志，根据first字段显示不同信息
        const firstLogin = user.first === 0;
        console.log(`${firstLogin ? '首次登录用户' : '用户'} ${user.email || user.username} 的密码已${isSuperAdminAction ? '由超级管理员' : ''}更新`);
        
        return { success: true };
    }

    /**
     * 确认注册（用于首次登录）
     */
    confirmRegistration(email) {
        const users = this.getUsers();
        const userIndex = users.findIndex(u => u.email === email);
        
        if (userIndex === -1) {
            return { success: false, message: '用户不存在' };
        }
        
        users[userIndex].confirmed = true;
        this.saveUsers(users);
        
        // 更新当前用户信息
        const currentUser = this.getCurrentUser();
        if (currentUser && currentUser.email === email) {
            currentUser.confirmed = true;
            this.setCurrentUser(currentUser);
        }
        
        return { success: true };
    }

    /**
     * 重置过期密码
     */
    resetExpiredPasswords() {
        const users = this.getUsers();
        let hasChanges = false;
        
        users.forEach(user => {
            if (user.role !== this.adminRole && 
                user.role !== this.superAdminRole &&
                !user.confirmed && 
                Date.now() - user.lastPasswordChange > this.passwordExpiry) {
                
                user.password = this.generateRandomPassword();
                user.lastPasswordChange = Date.now();
                hasChanges = true;
                console.log(`已重置用户 ${user.email || user.username} 的密码: ${user.password}`);
            }
        });
        
        if (hasChanges) {
            this.saveUsers(users);
        }
    }

    /**
     * 审批申请
     */
    approveApplication(applicationId, status) {
        if (!this.isAdmin()) {
            return { success: false, message: '需要管理员权限' };
        }
        
        if (window.databaseManager) {
            const currentUser = this.getCurrentUser();
            const success = window.databaseManager.updateApplicationStatus(
                applicationId, 
                status, 
                currentUser.email || currentUser.username
            );
            return { success: success, message: success ? '审批成功' : '申请不存在' };
        } else {
            // 备用方案：直接使用localStorage
            const applications = JSON.parse(localStorage.getItem('workApplications') || '[]');
            const appIndex = applications.findIndex(app => app.id === applicationId);
            
            if (appIndex === -1) {
                return { success: false, message: '申请不存在' };
            }
            
            applications[appIndex].status = status;
            applications[appIndex].approvedBy = this.getCurrentUser().email || this.getCurrentUser().username;
            applications[appIndex].approvedTime = new Date().toLocaleString('zh-CN');
            
            localStorage.setItem('workApplications', JSON.stringify(applications));
            return { success: true };
        }
    }
    
    /**
     * 超级管理员专用：获取所有用户信息（包括密码）
     */
    getAllUsersWithPasswords() {
        const currentUser = this.getCurrentUser();
        if (!this.isSuperAdmin(currentUser)) {
            return { success: false, message: '需要超级管理员权限' };
        }
        
        const users = this.getUsers();
        return { success: true, users: users };
    }
    
    /**
     * 超级管理员专用：更新用户信息
     */
    updateUserInfo(email, updates) {
        const currentUser = this.getCurrentUser();
        if (!this.isSuperAdmin(currentUser)) {
            return { success: false, message: '需要超级管理员权限' };
        }
        
        const users = this.getUsers();
        const userIndex = users.findIndex(u => u.email === email || u.username === email);
        
        if (userIndex === -1) {
            return { success: false, message: '用户不存在' };
        }
        
        // 更新用户信息
        Object.assign(users[userIndex], updates);
        
        // 如果更新了密码，设置时间戳并标记为超级管理员操作
        if (updates.password) {
            users[userIndex].lastPasswordChange = Date.now();
            console.log(`超级管理员已更新用户 ${users[userIndex].email || users[userIndex].username} 的密码`);
        }
        
        this.saveUsers(users);
        
        return { success: true };
    }
    
    /**
     * 搜索用户
     */
    searchUsers(keyword) {
        const currentUser = this.getCurrentUser();
        if (!this.isSuperAdmin(currentUser)) {
            return { success: false, message: '需要超级管理员权限' };
        }
        
        const users = this.getUsers();
        const searchKeyword = keyword.toLowerCase();
        const results = users.filter(user => 
            (user.email && user.email.toLowerCase().includes(searchKeyword)) ||
            (user.username && user.username.toLowerCase().includes(searchKeyword)) ||
            (user.position && user.position.toLowerCase().includes(searchKeyword))
        );
        
        return { success: true, users: results };
    }

    /**
     * 导出数据库
     */
    exportDatabase() {
        try {
            const currentUser = this.getCurrentUser();
            if (!currentUser || !this.isSuperAdmin(currentUser)) {
                throw new Error('只有超级管理员可以导出数据库');
            }
            
            // 确保数据库管理器可用
            const dbManager = window.databaseManager || this.dbManager;
            if (!dbManager) {
                throw new Error('数据库管理器未初始化');
            }
            
            // 获取数据库内容
            const dbData = dbManager.getDatabase();
            if (!dbData) {
                throw new Error('无法获取数据库内容');
            }
            
            const dbContent = JSON.stringify(dbData, null, 2);
            const blob = new Blob([dbContent], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `database_backup_${new Date().toISOString().replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            console.log('数据库导出成功');
            return { success: true, message: '数据库导出成功' };
        } catch (error) {
            console.error('数据库导出失败:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * 导入数据库
     */
    importDatabase(file) {
        return new Promise((resolve) => {
            try {
                const currentUser = this.getCurrentUser();
                if (!currentUser || !this.isSuperAdmin(currentUser)) {
                    throw new Error('只有超级管理员可以导入数据库');
                }
                
                // 确保数据库管理器可用
                const dbManager = window.databaseManager || this.dbManager;
                if (!dbManager) {
                    throw new Error('数据库管理器未初始化');
                }
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const jsonString = e.target.result;
                        const database = JSON.parse(jsonString);
                        
                        // 验证数据库结构
                        if (!database.users || !Array.isArray(database.applications)) {
                            throw new Error('无效的数据库格式');
                        }
                        
                        // 保存数据库
                        if (dbManager.saveDatabase) {
                            const success = dbManager.saveDatabase(database);
                            if (success) {
                                console.log('数据库导入成功');
                                // 重新加载当前用户信息
                                this.setCurrentUser(this.getCurrentUser());
                                resolve({ success: true, message: '数据库导入成功' });
                            } else {
                                throw new Error('数据库保存失败');
                            }
                        } else {
                            throw new Error('数据库管理器缺少必要的方法');
                        }
                    } catch (error) {
                        console.error('数据库导入失败:', error);
                        resolve({ success: false, message: error.message });
                    }
                };
                reader.readAsText(file);
            } catch (error) {
                console.error('数据库导入失败:', error);
                resolve({ success: false, message: error.message });
            }
        });
    }

    /**
     * 重置数据库
     */
    resetDatabase() {
        try {
            const currentUser = this.getCurrentUser();
            if (!currentUser || !this.isSuperAdmin(currentUser)) {
                throw new Error('只有超级管理员可以重置数据库');
            }
            
            // 确保数据库管理器可用
            const dbManager = window.databaseManager || this.dbManager;
            if (!dbManager) {
                throw new Error('数据库管理器未初始化');
            }
            
            if (!confirm('警告：此操作将重置数据库到初始状态，所有数据将丢失！确定要继续吗？')) {
                throw new Error('操作已取消');
            }
            
            // 重置数据库
            if (dbManager.resetDatabase) {
                const success = dbManager.resetDatabase();
                if (success) {
                    console.log('数据库已重置到初始状态');
                    // 重新加载当前用户信息
                    this.setCurrentUser(this.getCurrentUser());
                    return { success: true, message: '数据库已重置到初始状态' };
                } else {
                    throw new Error('数据库重置失败');
                }
            } else {
                // 手动重置数据库到初始状态
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
                
                if (dbManager.saveDatabase) {
                    const success = dbManager.saveDatabase(defaultDatabase);
                    if (success) {
                        console.log('数据库已重置到初始状态');
                        this.setCurrentUser(this.getCurrentUser());
                        return { success: true, message: '数据库已重置到初始状态' };
                    } else {
                        throw new Error('数据库重置失败');
                    }
                }
                
                throw new Error('数据库管理器缺少必要的方法');
            }
        } catch (error) {
            console.error('数据库重置失败:', error);
            return { success: false, message: error.message };
        }
    }
}

// 创建单例实例
const userManager = new UserManager();

// 定期检查并重置过期密码
setInterval(() => {
    // 检查resetExpiredPasswords方法是否存在
    if (userManager.resetExpiredPasswords) {
        userManager.resetExpiredPasswords();
    }
}, 5 * 60 * 1000); // 每5分钟检查一次

// 在浏览器环境中，将userManager暴露到window对象上
// 确保在DOM加载完成后再执行
if (window) {
    // 确保UserManager类已定义
    window.UserManager = UserManager;
    
    // 创建并暴露单例实例
    const userManagerInstance = new UserManager();
    window.userManager = userManagerInstance;
    
    console.log('用户管理模块已成功加载并暴露到window对象');
}