// 编程猫API验证工具
class CodemaoAPIValidator {
    constructor() {
        this.workshopId = 25294;
        this.apiUrl = `https://api.codemao.cn`;
        this.cache = {};
        this.cacheExpiry = 3600000; // 缓存1小时
        this.cookieName = 'kl_workshop_user'; // Cookie名称
        this.validationLogs = []; // 存储验证日志
    }
    
    /**
     * 添加日志
     * @param {string} message - 日志消息
     * @param {string} type - 日志类型 (info, success, error)
     */
    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleString('zh-CN');
        const logEntry = {
            timestamp: timestamp,
            message: message,
            type: type
        };
        this.validationLogs.push(logEntry);
        console.log(`[${timestamp}] [${type.toUpperCase()}] ${message}`);
    }
    
    /**
     * 显示日志弹窗（带动画效果）
     */
    showLogPopup() {
        // 检查是否已存在弹窗元素，如果有则移除
        const existingPopup = document.getElementById('validation-log-popup');
        if (existingPopup) {
            existingPopup.remove();
        }
        
        // 创建弹窗容器
        const popupContainer = document.createElement('div');
        popupContainer.id = 'validation-log-popup';
        popupContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        `;
        
        // 创建弹窗内容
        const popupContent = document.createElement('div');
        popupContent.style.cssText = `
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transform: scale(0.9);
            transition: transform 0.3s ease;
        `;
        
        // 创建弹窗头部
        const popupHeader = document.createElement('div');
        popupHeader.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        `;
        
        // 添加标题
        const popupTitle = document.createElement('h3');
        popupTitle.textContent = '验证过程日志';
        popupTitle.style.margin = '0';
        popupTitle.style.color = '#333';
        
        // 添加关闭按钮
        const closeButton = document.createElement('button');
        closeButton.textContent = '×';
        closeButton.style.cssText = `
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
            width: 30px;
            height: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            border-radius: 50%;
            transition: background-color 0.2s ease, color 0.2s ease;
        `;
        
        closeButton.addEventListener('mouseover', () => {
            closeButton.style.backgroundColor = '#f0f0f0';
            closeButton.style.color = '#333';
        });
        
        closeButton.addEventListener('mouseout', () => {
            closeButton.style.backgroundColor = 'transparent';
            closeButton.style.color = '#666';
        });
        
        closeButton.addEventListener('click', () => {
            popupContainer.style.opacity = '0';
            popupContainer.style.visibility = 'hidden';
            popupContent.style.transform = 'scale(0.9)';
            setTimeout(() => {
                popupContainer.remove();
            }, 300);
        });
        
        // 创建日志内容区域
        const logContent = document.createElement('div');
        logContent.style.cssText = `
            font-family: monospace;
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            line-height: 1.5;
        `;
        
        // 添加每条日志
        this.validationLogs.forEach(log => {
            const logItem = document.createElement('div');
            logItem.style.marginBottom = '8px';
            
            let color = '#333';
            let bgColor = 'transparent';
            let padding = '5px';
            
            if (log.type === 'success') {
                color = '#27ae60';
                bgColor = '#ecf0f1';
            } else if (log.type === 'error') {
                color = '#e74c3c';
                bgColor = '#ecf0f1';
            }
            
            logItem.style.cssText = `
                color: ${color};
                background-color: ${bgColor};
                padding: ${padding};
                border-radius: 3px;
                border-left: 3px solid ${color};
                animation: fadeIn 0.5s ease;
            `;
            
            logItem.innerHTML = `<strong>${log.timestamp}</strong> [${log.type.toUpperCase()}] ${log.message}`;
            logContent.appendChild(logItem);
        });
        
        // 组装弹窗
        popupHeader.appendChild(popupTitle);
        popupHeader.appendChild(closeButton);
        popupContent.appendChild(popupHeader);
        popupContent.appendChild(logContent);
        popupContainer.appendChild(popupContent);
        
        // 添加CSS动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; transform: translateX(-10px); }
                to { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
        
        // 添加到文档
        document.body.appendChild(popupContainer);
        
        // 触发动画
        setTimeout(() => {
            popupContainer.style.opacity = '1';
            popupContainer.style.visibility = 'visible';
            popupContent.style.transform = 'scale(1)';
        }, 10);
        
        // 点击弹窗外部关闭
        popupContainer.addEventListener('click', (e) => {
            if (e.target === popupContainer) {
                closeButton.click();
            }
        });
        
        // 清空日志
        this.validationLogs = [];
    }

    /**
     * 验证用户名是否存在于工作室中
     * @param {string} username - 要验证的用户名
     * @returns {Promise<Object>} - 验证结果对象
     */
    async validateUser(username) {
        this.addLog(`开始验证用户: ${username}`);
        
        // 检查缓存
        if (this.cache[username] && (Date.now() - this.cache[username].timestamp < this.cacheExpiry)) {
            this.addLog(`用户 ${username} 命中缓存`);
            return this.cache[username].result;
        }

        try {
            // 调用API获取工作室成员列表
            const response = await this.fetchWorkshopMembers();
            
            // 查找用户
            const user = response.items.find(item => 
                item.name.toLowerCase() === username.toLowerCase()
            );

            // 构建结果
            let result;
            if (user) {
                const positionTitle = this.getPositionTitle(user.position);
                result = {
                    valid: !!user,
                    user: user || null,
                    message: `${username} 是KL工作室的${positionTitle}`
                };
                this.addLog(`用户 ${username} 验证成功，职位: ${positionTitle}`, 'success');
            } else {
                result = {
                    valid: !!user,
                    user: user || null,
                    message: `${username} 不是KL工作室的成员`
                };
                this.addLog(`用户 ${username} 验证失败：不是工作室成员`, 'error');
            }

            // 缓存结果
            this.cache[username] = {
                result,
                timestamp: Date.now()
            };

            return result;
        } catch (error) {
            this.addLog(`验证服务出错: ${error.message}`, 'error');
            return {
                valid: false,
                user: null,
                message: '验证服务暂时不可用，请稍后重试',
                error: error.message
            };
        }
    }

    /**
     * 设置用户Cookie
     * @param {string} username - 用户名
     */
    setUserCookie(username) {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 1); // Cookie有效期1天
        document.cookie = `${this.cookieName}=${encodeURIComponent(username)};expires=${expiry.toUTCString()};path=/`;
    }

    /**
     * 获取用户Cookie
     * @returns {string|null} - 解码后的用户名或null
     */
    getUserCookie() {
        this.addLog(`获取Cookie: ${this.cookieName}`);
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith(`${this.cookieName}=`))
            ?.split('=')[1];
        const result = cookieValue ? decodeURIComponent(cookieValue) : null;
        this.addLog(`Cookie值: ${result || '未找到'}`);
        return result;
    }

    /**
     * 验证Cookie中的用户名是否与输入的用户名匹配
     * @param {string} username - 输入的用户名
     * @returns {boolean} - 是否匹配
     */
    validateCookie(username) {
        this.addLog(`开始验证Cookie，当前用户名: ${username}`);
        const cookieUsername = this.getUserCookie();
        const isMatch = cookieUsername === username;
        
        if (isMatch) {
            this.addLog(`Cookie验证成功: ${username} 匹配`, 'success');
        } else {
            this.addLog(`Cookie验证失败: 输入用户=${username}, Cookie用户=${cookieUsername}`, 'error');
        }
        
        // 显示日志弹窗
        this.showLogPopup();
        
        return isMatch;
    }

    /**
     * 获取工作室成员列表
     * @returns {Promise<Object>} - API返回的数据
     */
    async fetchWorkshopMembers() {
        try {
            // 由于跨域问题，这里使用模拟数据
            // 实际环境中应该使用后端代理或支持CORS的API
            console.log('调用API获取工作室成员:', this.apiUrl);
            
            // 模拟API响应数据
            // 实际项目中应该替换为真实的fetch请求
            // const response = await fetch(`${this.apiUrl}?workshop_id=${this.workshopId}`);
            // if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            // return await response.json();
            
            // 返回模拟数据
            return {
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
                ],
                offset: 0,
                limit: 20,
                total: 3,
                counted: true
            };
        } catch (error) {
            console.error('获取工作室成员失败:', error);
            throw error;
        }
    }

    /**
     * 将职位代码转换为中文职位名称
     * @param {string} positionCode - 职位代码
     * @returns {string} - 中文职位名称
     */
    getPositionTitle(positionCode) {
        const positions = {
            'LEADER': '室长',
            'DEPUTYLEADER': '副室长',
            'STAFF': '室员'
        };
        return positions[positionCode] || '成员';
    }

    /**
     * 清空缓存
     */
    clearCache() {
        this.cache = {};
        console.log('缓存已清空');
    }
}

// 创建单例实例
const codemaoValidator = new CodemaoAPIValidator();

// 在浏览器环境中，将函数暴露到window对象上
window.validateUsername = async (username) => {
    return codemaoValidator.validateUser(username);
};

window.validateUserWithCookie = (username) => {
    return codemaoValidator.validateCookie(username);
};

window.setUserCookie = (username) => {
    return codemaoValidator.setUserCookie(username);
};

window.clearValidationCache = () => {
    return codemaoValidator.clearCache();
};

// 也将实例暴露出去，以便直接访问
window.codemaoValidator = codemaoValidator;