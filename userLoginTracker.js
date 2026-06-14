// 用户登录状态跟踪器
// 用于在用户登录时更新其first字段为1

class UserLoginTracker {
    constructor() {
        this.pythonScriptPath = 'user_password_manager.py';
    }

    /**
     * 记录用户登录，将first字段设置为1
     * @param {string} username - 登录的用户名
     */
    async trackUserLogin(username) {
        console.log(`[登录跟踪] 开始处理用户 ${username} 的登录记录`);
        
        try {
            // 在浏览器环境中，我们无法直接执行Python脚本
            // 这里我们直接更新localStorage中的用户数据
            // 在实际部署环境中，应该通过后端API调用Python脚本或直接操作数据库
            
            // 从localStorage获取数据库
            const localStorageKey = 'kl_workshop_database';
            const dbData = localStorage.getItem(localStorageKey);
            
            if (!dbData) {
                console.warn('[登录跟踪] 数据库未找到');
                return false;
            }
            
            // 解析数据库
            const database = JSON.parse(dbData);
            const users = database.users || [];
            
            // 查找并更新用户
            let updated = false;
            for (let user of users) {
                if (user.email === username) {
                    user.first = 1;
                    updated = true;
                    console.log(`[登录跟踪] 已将用户 ${username} 的first字段设置为1`);
                    break;
                }
            }
            
            // 如果用户不存在但数据库管理器可用，尝试通过数据库管理器添加用户
            if (!updated && window.databaseManager) {
                console.log(`[登录跟踪] 用户 ${username} 未在数据库中找到，尝试通过databaseManager添加`);
                const userExists = window.databaseManager.findUserByEmail(username);
                if (userExists) {
                    window.databaseManager.updateUser(username, { first: 1 });
                    console.log(`[登录跟踪] 已通过databaseManager将用户 ${username} 的first字段设置为1`);
                    updated = true;
                }
            }
            
            // 保存更新后的数据库
            if (updated) {
                database.users = users;
                localStorage.setItem(localStorageKey, JSON.stringify(database));
                console.log(`[登录跟踪] 用户 ${username} 登录记录已保存`);
                return true;
            } else {
                console.warn(`[登录跟踪] 用户 ${username} 未找到，无法更新登录状态`);
                return false;
            }
        } catch (error) {
            console.error(`[登录跟踪] 更新用户登录状态时出错: ${error.message}`);
            return false;
        }
    }

    /**
     * 检查Python脚本是否在运行
     * 这只是一个模拟方法，在实际环境中应该通过后端API检查
     */
    checkPythonScriptRunning() {
        console.log('[登录跟踪] 检查Python脚本运行状态...');
        // 在浏览器环境中无法直接检查Python脚本运行状态
        // 返回模拟状态
        return true;
    }

    /**
     * 获取登录状态跟踪器实例
     */
    static getInstance() {
        if (!UserLoginTracker.instance) {
            UserLoginTracker.instance = new UserLoginTracker();
        }
        return UserLoginTracker.instance;
    }
}

// 在浏览器环境中，将UserLoginTracker暴露到window对象上
if (window) {
    window.UserLoginTracker = UserLoginTracker;
    window.userLoginTracker = UserLoginTracker.getInstance();
    console.log('用户登录状态跟踪器已加载');
}

// 添加到UserManager中，以便在登录时自动调用
document.addEventListener('DOMContentLoaded', function() {
    // 等待userManager加载完成
    const checkUserManager = setInterval(() => {
        if (window.userManager) {
            clearInterval(checkUserManager);
            
            // 保存原始登录方法
            const originalLogin = window.userManager.login || function() {};
            
            // 重写登录方法
            window.userManager.login = function(email, password) {
                // 调用原始登录方法
                const result = originalLogin.call(this, email, password);
                
                // 如果登录成功，记录登录状态
                if (result && result.success) {
                    console.log(`[登录拦截] 用户 ${email} 登录成功，正在记录登录状态`);
                    window.userLoginTracker.trackUserLogin(email);
                }
                
                return result;
            };
            
            console.log('已成功扩展userManager.login方法，添加登录状态跟踪功能');
        }
    }, 100);
    
    // 10秒后停止检查，避免无限循环
    setTimeout(() => {
        clearInterval(checkUserManager);
    }, 10000);
});

// 为了兼容性，只在Node.js环境中进行模块导出
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = UserLoginTracker;
}