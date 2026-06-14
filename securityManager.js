// 安全管理器 - 实现登录验证、访问控制和权限检查功能

class SecurityManager {
    constructor() {
        // 允许访问的页面（未登录状态下）
        this.publicRoutes = [
            'index.html'
        ];
        this.protectedAPIs = [
            'data/database.json'
        ];
        this.adminOnlyRoutes = [
            'superAdminDashboard.html'
        ];
        this.initialize();
    }

    /**
     * 初始化安全管理器
     */
    initialize() {
        // 检查当前页面是否需要登录保护
        this.checkPageAccess();
        
        // 拦截API请求
        this.interceptAPIRequests();
    }

    /**
     * 获取当前登录用户
     */
    getCurrentUser() {
        const userStr = localStorage.getItem('currentUser');
        if (userStr) {
            try {
                return JSON.parse(userStr);
            } catch (e) {
                console.error('解析用户信息失败:', e);
                return null;
            }
        }
        return null;
    }

    /**
     * 检查用户是否已登录
     */
    isLoggedIn() {
        return !!this.getCurrentUser();
    }

    /**
     * 检查用户是否为管理员
     */
    isAdmin() {
        const user = this.getCurrentUser();
        return user && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN');
    }

    /**
     * 检查用户是否为超级管理员
     */
    isSuperAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'SUPER_ADMIN';
    }

    /**
     * 检查页面访问权限
     */
    checkPageAccess() {
        const currentPath = window.location.pathname;
        const currentPage = currentPath.split('/').pop();

        // 如果不是公开页面，需要登录
        if (!this.publicRoutes.includes(currentPage)) {
            if (!this.isLoggedIn()) {
                // 未登录，重定向到登录页
                window.location.href = 'index.html';
                return false;
            }

            // 检查是否需要管理员权限
            if (this.adminOnlyRoutes.includes(currentPage)) {
                // 特殊处理superAdminDashboard.html，只允许超级管理员访问
                if (currentPage === 'superAdminDashboard.html') {
                    if (!this.isSuperAdmin()) {
                        // 权限不足，重定向到普通用户仪表盘
                        window.location.href = 'dashboard.html';
                        return false;
                    }
                } else {
                    // 其他管理员页面，允许管理员和超级管理员访问
                    if (!this.isAdmin()) {
                        // 权限不足，重定向到普通用户仪表盘
                        window.location.href = 'dashboard.html';
                        return false;
                    }
                }
            }
        }

        return true;
    }

    /**
     * 拦截API请求，添加安全检查
     */
    interceptAPIRequests() {
        // 保存原始fetch方法
        const originalFetch = window.fetch;

        // 重写fetch方法
        window.fetch = async (url, options) => {
            // 检查是否为受保护的API
            for (const protectedAPI of this.protectedAPIs) {
                if (url.includes(protectedAPI)) {
                    // 检查登录状态
                    if (!this.isLoggedIn()) {
                        console.error('未授权访问: 请先登录');
                        // 重定向到登录页
                        window.location.href = 'index.html';
                        return Promise.reject(new Error('未授权访问'));
                    }

                    // 对于数据库访问，需要管理员权限
                    if (url.includes('database.json')) {
                        if (!this.isAdmin()) {
                            console.error('权限不足: 需要管理员权限');
                            // 可以在这里返回一个错误响应
                            return new Response(JSON.stringify({ error: '权限不足' }), {
                                status: 403,
                                headers: { 'Content-Type': 'application/json' }
                            });
                        }
                    }
                    break;
                }
            }

            // 调用原始fetch方法
            return originalFetch(url, options);
        };

        // 监控XHR请求
        const originalXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            // 检查是否为受保护的API
            for (const protectedAPI of SecurityManager.instance.protectedAPIs) {
                if (url.includes(protectedAPI)) {
                    // 检查登录状态
                    if (!SecurityManager.instance.isLoggedIn()) {
                        console.error('未授权访问: 请先登录');
                        // 重定向到登录页
                        window.location.href = 'index.html';
                        // 阻止请求
                        return;
                    }

                    // 对于数据库访问，需要管理员权限
                    if (url.includes('database.json')) {
                        if (!SecurityManager.instance.isAdmin()) {
                            console.error('权限不足: 需要管理员权限');
                            // 阻止请求
                            return;
                        }
                    }
                    break;
                }
            }

            // 调用原始open方法
            return originalXHROpen.call(this, method, url, ...args);
        };
    }

    /**
     * 验证用户权限
     * @param {string} requiredPermission - 所需权限级别 ('user', 'admin', 'superadmin')
     */
    checkPermission(requiredPermission) {
        const user = this.getCurrentUser();
        if (!user) {
            return false;
        }

        switch(requiredPermission) {
            case 'user':
                return true; // 任何登录用户都有用户权限
            case 'admin':
                return this.isAdmin();
            case 'superadmin':
                return this.isSuperAdmin();
            default:
                return false;
        }
    }

    /**
     * 处理权限不足的情况
     */
    handlePermissionDenied() {
        alert('权限不足，无法执行此操作');
    }

    /**
     * 强制用户登出
     */
    logout() {
        localStorage.removeItem('currentUser');
        localStorage.removeItem('rememberLogin');
        window.location.href = 'index.html';
    }

    /**
     * 单例模式获取实例
     */
    static getInstance() {
        if (!SecurityManager.instance) {
            SecurityManager.instance = new SecurityManager();
        }
        return SecurityManager.instance;
    }
}

// 创建设置实例
SecurityManager.instance = null;

// 暴露到全局
window.SecurityManager = SecurityManager;
window.securityManager = SecurityManager.getInstance();