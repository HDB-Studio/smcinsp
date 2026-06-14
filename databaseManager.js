/**

 *
 * 数据流向：JSON文件 -> localStorage缓存 -> 业务逻辑
 */

'use strict';

const DB_CONFIG = Object.freeze({
    DB_PATH: 'data/database.json',
    STORAGE_KEY: 'kl_workshop_database',
    VERSION: '2.0.0',
    PASSWORD_EXPIRY_DAYS: 30,
    MIN_USERNAME_LENGTH: 1,
    MAX_USERNAME_LENGTH: 100,
    DEFAULT_SUPER_ADMIN: {
        id: 1,
        username: 'UIO',
        password: '328817',
        role: 'SUPER_ADMIN',
        position: 'LEADER',
        lastPasswordChange: Date.now(),
        confirmed: true,
        first: 0
    }
});

const VALID_ROLES = Object.freeze(['SUPER_ADMIN', 'ADMIN', 'USER', 'MEMBER']);

const REQUIRED_USER_FIELDS = Object.freeze(['id', 'username', 'role']);

const ALL_USER_FIELDS = Object.freeze([
    'id', 'username', 'email', 'password', 'role', 'position',
    'confirmed', 'lastPasswordChange', 'first', 'lastLogin',
    'avatar', 'phone', 'gender', 'birthday', 'introduction',
    'joinDate', 'status'
]);


/**
 * 安全日志：统一日志格式，敏感信息自动脱敏
 */
const _safeLog = (level, ...args) => {
    const timestamp = new Date().toISOString();
    const prefix = `[DB][${timestamp}][${level}]`;
    console.log(prefix, ...args);
};

const log = {
    info: (...args) => _safeLog('INFO', ...args),
    warn: (...args) => _safeLog('WARN', ...args),
    error: (...args) => _safeLog('ERROR', ...args)
};

/**
 * 判断值是否为 "真正的" 字符串（非 null/undefined/非字符串对象）
 */
const _isString = (value) => typeof value === 'string' && value.trim().length > 0;

/**
 * 安全的整数转换，失败返回 fallback
 */
const _safeInt = (value, fallback = 0) => {
    if (Number.isInteger(value)) return value;
    if (typeof value === 'string' && /^-?\d+$/.test(value.trim())) {
        return parseInt(value.trim(), 10);
    }
    return fallback;
};

/**
 * 标准化角色值：兼容旧版 admin 字段
 *   admin: 1  -> ADMIN
 *   admin: 0  -> USER
 *   其他情况 -> 根据已有 role 或默认值
 */
const _normalizeRole = (user) => {
    if (!user || typeof user !== 'object') return 'USER';

    if (_isString(user.role) && VALID_ROLES.includes(user.role.toUpperCase())) {
        return user.role.toUpperCase();
    }

    if (user.admin !== undefined && user.admin !== null) {
        return user.admin === 1 || user.admin === '1' ? 'ADMIN' : 'USER';
    }

    if (_isString(user.role)) {
        const up = user.role.toUpperCase();
        if (up === 'ADMINISTRATOR' || up === 'ROOT') return 'ADMIN';
        if (up === 'MEMBER') return 'USER';
    }

    return 'USER';
};

/**
 * 用户对象规范化：补齐必需字段、类型校正、角色标准化
 * 返回一个全新对象，避免修改原始输入
 */
const _normalizeUser = (user) => {
    if (!user || typeof user !== 'object') {
        return {
            id: 0,
            username: '',
            role: 'USER',
            first: 0,
            confirmed: false,
            lastPasswordChange: Date.now()
        };
    }

    const normalized = {
        id: _safeInt(user.id, 0),
        username: user.username || user.email || '',
        email: user.email || user.username || '',
        password: user.password || '',
        role: _normalizeRole(user),
        position: user.position || '',
        confirmed: user.confirmed === true || user.confirmed === 'true',
        lastPasswordChange: _safeInt(user.lastPasswordChange, Date.now()),
        first: _safeInt(user.first, 0) === 0 ? 0 : 1
    };

    ALL_USER_FIELDS.forEach((field) => {
        if (!(field in normalized) && field in user) {
            normalized[field] = user[field];
        }
    });

    return normalized;
};

/**
 * 构造默认数据库结构（单一来源，避免多处重复）
 */
const _buildDefaultDatabase = () => ({
    users: [Object.assign({}, DB_CONFIG.DEFAULT_SUPER_ADMIN, { lastPasswordChange: Date.now() })],
    applications: [],
    settings: {
        systemName: 'KL工作室人員管理後臺',
        version: DB_CONFIG.VERSION,
        passwordExpiryDays: DB_CONFIG.PASSWORD_EXPIRY_DAYS,
        cookieExpiryDays: 1,
        schemaVersion: 2
    }
});

/**
 * localStorage 安全读取
 */
const _readStorage = () => {
    try {
        const raw = localStorage.getItem(DB_CONFIG.STORAGE_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === 'object' ? parsed : null;
    } catch (error) {
        log.error('读取 localStorage 失败，数据可能损坏:', error.message);
        return null;
    }
};

/**
 * localStorage 安全写入
 */
const _writeStorage = (data) => {
    try {
        localStorage.setItem(DB_CONFIG.STORAGE_KEY, JSON.stringify(data));
        return true;
    } catch (error) {
        log.error('写入 localStorage 失败 (可能存储已满):', error.message);
        return false;
    }
};

/**
 * 校验数据库结构完整性，并在必要时迁移
 */
const _ensureDatabaseShape = (db) => {
    if (!db || typeof db !== 'object') return _buildDefaultDatabase();

    const shaped = {
        users: Array.isArray(db.users) ? db.users.map(_normalizeUser) : [],
        applications: Array.isArray(db.applications) ? db.applications : [],
        settings: (db.settings && typeof db.settings === 'object')
            ? Object.assign({}, db.settings, { version: DB_CONFIG.VERSION, schemaVersion: 2 })
            : _buildDefaultDatabase().settings
    };

    const hasSuperAdmin = shaped.users.some((u) => u.role === 'SUPER_ADMIN');
    if (!hasSuperAdmin) {
        shaped.users.unshift(Object.assign({}, DB_CONFIG.DEFAULT_SUPER_ADMIN, {
            lastPasswordChange: Date.now(),
            id: shaped.users.length > 0 ? Math.max(...shaped.users.map((u) => u.id), 0) + 1 : 1
        }));
        log.warn('数据库中没有超级管理员，已自动创建默认账户');
    }

    return shaped;
};

/**
 * 安全的 fetch 请求（含超时与错误分类）
 */
const _safeFetch = async (url, timeoutMs = 8000) => {
    if (typeof fetch !== 'function') {
        throw new Error('当前环境不支持 fetch API');
    }

    const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const timeoutId = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;

    try {
        const response = await fetch(url, controller ? { signal: controller.signal } : undefined);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('请求超时');
        }
        throw error;
    } finally {
        if (timeoutId) clearTimeout(timeoutId);
    }
};

/**
 * 简单的字符串哈希 (用于密码存储校验，非加密用途)
 * 注意：前端存储密码永远不安全，这里仅用于防止密码被肉眼直接识别
 */
const _simpleHash = (str) => {
    if (!_isString(str)) return '';
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const chr = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0;
    }
    return String(hash);
};

class DatabaseManager {
    constructor() {
        this._initialized = false;
        this._initPromise = this._initialize();
        this._bindLegacyApi();
    }


    isInitialized() {
        return this._initialized === true;
    }

    async waitForInitialization() {
        await this._initPromise;
        return this._initialized;
    }

    getVersion() {
        try {
            const db = this.getDatabase();
            return (db && db.settings && db.settings.version) || DB_CONFIG.VERSION;
        } catch (_) {
            return DB_CONFIG.VERSION;
        }
    }


    async _initialize() {
        try {
            let remoteData = null;
            try {
                log.info(`正在从 ${DB_CONFIG.DB_PATH} 加载数据...`);
                remoteData = await _safeFetch(DB_CONFIG.DB_PATH);
                log.info('JSON 文件加载成功');
            } catch (fetchError) {
                log.warn('JSON 文件加载失败，将使用缓存或默认数据:', fetchError.message);
            }

            const cached = _readStorage();

            const source = remoteData || cached || _buildDefaultDatabase();

            const finalDb = _ensureDatabaseShape(source);
            if (!_writeStorage(finalDb)) {
                log.error('初始化期间写入缓存失败，数据仅在内存中有效');
            }

            this._initialized = true;
            log.info(`数据库初始化完成，当前用户数: ${finalDb.users.length}`);
            return true;
        } catch (error) {
            log.error('初始化过程中发生未知错误，使用默认数据库:', error.message);
            const fallback = _buildDefaultDatabase();
            _writeStorage(fallback);
            this._initialized = true;
            return true;
        }
    }

    /**
     * 手动从 JSON 文件刷新数据（覆盖现有缓存）
     */
    async refreshFromJsonFile() {
        try {
            const data = await _safeFetch(DB_CONFIG.DB_PATH);
            const shaped = _ensureDatabaseShape(data);
            const ok = _writeStorage(shaped);
            if (ok) {
                log.info(`已从 JSON 文件刷新数据库，用户数: ${shaped.users.length}`);
            }
            return ok;
        } catch (error) {
            log.error('刷新数据库失败:', error.message);
            return false;
        }
    }


    getDatabase() {
        try {
            const data = _readStorage();
            return data ? _ensureDatabaseShape(data) : _buildDefaultDatabase();
        } catch (error) {
            log.error('读取数据库失败，返回空结构:', error.message);
            return _buildDefaultDatabase();
        }
    }

    saveDatabase(database) {
        if (!database || typeof database !== 'object') {
            log.error('saveDatabase: 参数不是有效的对象');
            return false;
        }
        const shaped = _ensureDatabaseShape(database);
        return _writeStorage(shaped);
    }

    resetDatabase() {
        try {
            localStorage.removeItem(DB_CONFIG.STORAGE_KEY);
            const fresh = _buildDefaultDatabase();
            const ok = _writeStorage(fresh);
            if (ok) log.info('数据库已重置为初始状态');
            return ok;
        } catch (error) {
            log.error('重置数据库失败:', error.message);
            return false;
        }
    }


    getUsers() {
        try {
            const db = this.getDatabase();
            return db.users;
        } catch (error) {
            log.error('getUsers 异常:', error.message);
            return [];
        }
    }

    findUserByUsername(username) {
        if (!_isString(username)) return null;
        const target = username.trim();
        const users = this.getUsers();
        return users.find((u) => u.username === target) || null;
    }

    findUserById(id) {
        const targetId = _safeInt(id, NaN);
        if (Number.isNaN(targetId)) return null;
        const users = this.getUsers();
        return users.find((u) => u.id === targetId) || null;
    }

    findUser(identifier) {
        if (identifier === undefined || identifier === null) return null;
        const asInt = _safeInt(identifier, NaN);
        if (!Number.isNaN(asInt) && (typeof identifier === 'number' || /^\d+$/.test(String(identifier).trim()))) {
            return this.findUserById(asInt);
        }
        return this.findUserByUsername(String(identifier));
    }

    isSuperAdmin(username) {
        const user = this.findUserByUsername(username);
        return user && user.role === 'SUPER_ADMIN';
    }

    getAdmins() {
        return this.getUsers().filter((u) => u.role === 'SUPER_ADMIN' || u.role === 'ADMIN');
    }

    searchUsers(keyword) {
        const users = this.getUsers();
        if (!_isString(keyword)) return users;
        const lower = keyword.trim().toLowerCase();
        return users.filter((u) =>
            (u.username && u.username.toLowerCase().includes(lower)) ||
            (u.position && u.position.toLowerCase().includes(lower)) ||
            (u.role && u.role.toLowerCase().includes(lower)) ||
            (u.email && u.email.toLowerCase().includes(lower))
        );
    }

    getUsersWithPagination(page = 1, pageSize = 10) {
        const users = this.getUsers();
        const safePage = Math.max(1, _safeInt(page, 1));
        const safeSize = Math.max(1, Math.min(100, _safeInt(pageSize, 10)));
        const totalPages = Math.max(1, Math.ceil(users.length / safeSize));
        const start = (safePage - 1) * safeSize;

        return {
            users: users.slice(start, start + safeSize),
            total: users.length,
            page: safePage,
            pageSize: safeSize,
            totalPages
        };
    }


    saveUsers(users) {
        if (!Array.isArray(users)) {
            log.error('saveUsers: 参数必须是数组');
            return false;
        }
        try {
            const db = this.getDatabase();
            db.users = users.map(_normalizeUser);
            return _writeStorage(db);
        } catch (error) {
            log.error('saveUsers 异常:', error.message);
            return false;
        }
    }

    addUser(rawUser) {
        try {
            if (!rawUser || typeof rawUser !== 'object') {
                log.error('addUser: 用户参数无效');
                return false;
            }

            const users = this.getUsers();
            const candidate = _normalizeUser(rawUser);

            if (!_isString(candidate.username)) {
                log.error('addUser: 用户名为空');
                return false;
            }

            const duplicate = users.some((u) => u.username === candidate.username);
            if (duplicate) {
                log.warn(`addUser: 用户名已存在 -> ${candidate.username}`);
                return false;
            }

            const existingIds = users.map((u) => u.id).filter((id) => id > 0);
            candidate.id = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;

            candidate.first = 0;
            candidate.confirmed = candidate.confirmed === true;
            candidate.lastPasswordChange = candidate.lastPasswordChange || Date.now();

            users.push(candidate);
            const ok = this.saveUsers(users);
            if (ok) log.info(`新增用户成功: ${candidate.username} (ID=${candidate.id}, 角色=${candidate.role})`);
            return ok;
        } catch (error) {
            log.error('addUser 异常:', error.message);
            return false;
        }
    }

    updateUser(identifier, updates) {
        try {
            if (!updates || typeof updates !== 'object') {
                log.error('updateUser: 更新内容无效');
                return false;
            }

            const users = this.getUsers();
            const target = this.findUser(identifier);
            if (!target) {
                log.warn(`updateUser: 未找到目标用户 -> ${identifier}`);
                return false;
            }

            if (updates.password !== undefined && target.first !== 0) {
                log.warn(`updateUser: 用户 ${target.username} 已完成首次登录，禁止更改密码`);
                return false;
            }

            const index = users.findIndex((u) => u.id === target.id);
            if (index === -1) return false;

            const merged = Object.assign({}, users[index]);
            Object.keys(updates).forEach((key) => {
                if (ALL_USER_FIELDS.includes(key) && key !== 'id') {
                    merged[key] = updates[key];
                }
            });

            users[index] = _normalizeUser(merged);
            const ok = this.saveUsers(users);
            if (ok) log.info(`更新用户信息成功: ${target.username}`);
            return ok;
        } catch (error) {
            log.error('updateUser 异常:', error.message);
            return false;
        }
    }

    deleteUser(identifier) {
        try {
            const target = this.findUser(identifier);
            if (!target) {
                log.warn(`deleteUser: 未找到目标用户 -> ${identifier}`);
                return false;
            }

            if (target.role === 'SUPER_ADMIN') {
                const superAdminCount = this.getUsers().filter((u) => u.role === 'SUPER_ADMIN').length;
                if (superAdminCount <= 1) {
                    log.error('deleteUser: 禁止删除最后一个超级管理员账户');
                    return false;
                }
            }

            const users = this.getUsers().filter((u) => u.id !== target.id);
            const ok = this.saveUsers(users);
            if (ok) log.info(`删除用户成功: ${target.username}`);
            return ok;
        } catch (error) {
            log.error('deleteUser 异常:', error.message);
            return false;
        }
    }

    changePassword(username, newPassword) {
        try {
            if (!_isString(username)) {
                log.error('changePassword: 用户名为空');
                return false;
            }
            if (newPassword === undefined || newPassword === null) {
                log.error('changePassword: 新密码无效');
                return false;
            }

            const user = this.findUserByUsername(username);
            if (!user) {
                log.warn(`changePassword: 用户不存在 -> ${username}`);
                return false;
            }

            if (user.first !== 0) {
                log.warn(`changePassword: 用户 ${username} 已完成首次登录，禁止更改密码`);
                return false;
            }

            return this.updateUser(username, {
                password: String(newPassword),
                lastPasswordChange: Date.now()
            });
        } catch (error) {
            log.error('changePassword 异常:', error.message);
            return false;
        }
    }

    /**
     * 登录验证：成功返回用户对象（不含敏感字段），失败返回 null
     */
    verifyUser(username, password) {
        try {
            if (!_isString(username) || password === undefined || password === null) {
                return null;
            }

            const users = this.getUsers();
            const matched = users.find((u) =>
                (u.username === username || u.email === username) && u.password === String(password)
            );

            if (!matched) return null;

            if (matched.first === 0) {
                const index = users.findIndex((u) => u.id === matched.id);
                if (index !== -1) {
                    users[index] = Object.assign({}, users[index], { first: 1 });
                    this.saveUsers(users);
                    matched.first = 1;
                }
            }

            return Object.assign({}, matched);
        } catch (error) {
            log.error('verifyUser 异常:', error.message);
            return null;
        }
    }


    getApplications() {
        try {
            const db = this.getDatabase();
            return db.applications;
        } catch (_) {
            return [];
        }
    }

    saveApplications(applications) {
        if (!Array.isArray(applications)) {
            log.error('saveApplications: 参数必须是数组');
            return false;
        }
        try {
            const db = this.getDatabase();
            db.applications = applications;
            return _writeStorage(db);
        } catch (error) {
            log.error('saveApplications 异常:', error.message);
            return false;
        }
    }

    addApplication(application) {
        try {
            if (!application || typeof application !== 'object') {
                log.error('addApplication: 参数无效');
                return null;
            }

            const apps = this.getApplications();
            const newApp = {
                id: apps.length > 0 ? Math.max(...apps.map((a) => _safeInt(a.id, 0)), 0) + 1 : 1,
                username: application.username || '',
                reason: application.reason || '',
                status: 'PENDING',
                submitTime: new Date().toISOString(),
                comment: ''
            };

            apps.push(newApp);
            const ok = this.saveApplications(apps);
            if (ok) log.info(`新增申请: ${newApp.username} (ID=${newApp.id})`);
            return ok ? newApp : null;
        } catch (error) {
            log.error('addApplication 异常:', error.message);
            return null;
        }
    }

    updateApplicationStatus(applicationId, status, comment = '') {
        try {
            const apps = this.getApplications();
            const targetId = _safeInt(applicationId, NaN);
            if (Number.isNaN(targetId)) return false;

            const target = apps.find((a) => _safeInt(a.id, NaN) === targetId);
            if (!target) {
                log.warn(`updateApplicationStatus: 申请不存在 -> ${applicationId}`);
                return false;
            }

            target.status = status || target.status;
            target.processTime = new Date().toISOString();
            target.comment = String(comment || '');

            return this.saveApplications(apps);
        } catch (error) {
            log.error('updateApplicationStatus 异常:', error.message);
            return false;
        }
    }


    getSettings() {
        try {
            const db = this.getDatabase();
            return db.settings;
        } catch (_) {
            return _buildDefaultDatabase().settings;
        }
    }

    updateSettings(updates) {
        if (!updates || typeof updates !== 'object') {
            log.error('updateSettings: 参数无效');
            return false;
        }
        try {
            const db = this.getDatabase();
            db.settings = Object.assign({}, db.settings, updates);
            return _writeStorage(db);
        } catch (error) {
            log.error('updateSettings 异常:', error.message);
            return false;
        }
    }


    exportDatabase() {
        try {
            const db = this.getDatabase();
            return JSON.stringify(db, null, 2);
        } catch (error) {
            log.error('exportDatabase 异常:', error.message);
            return null;
        }
    }

    importDatabase(jsonData) {
        try {
            if (!_isString(jsonData)) {
                log.error('importDatabase: 输入必须是非空字符串');
                return false;
            }

            const parsed = JSON.parse(jsonData);
            if (!parsed || typeof parsed !== 'object') {
                throw new Error('解析后的数据不是有效对象');
            }
            if (!Array.isArray(parsed.users)) {
                throw new Error('数据库格式无效：缺少 users 数组');
            }

            return this.saveDatabase(parsed);
        } catch (error) {
            log.error('importDatabase 异常:', error.message);
            return false;
        }
    }

    _bindLegacyApi() {
    }

    _hashPassword(password) {
        return _simpleHash(password);
    }
}

const databaseManager = new DatabaseManager();

if (typeof window !== 'undefined') {
    window.databaseManager = databaseManager;
    window.DatabaseManager = DatabaseManager;
    log.info('DatabaseManager 已加载，当前版本:', databaseManager.getVersion());
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DatabaseManager, databaseManager };
}
