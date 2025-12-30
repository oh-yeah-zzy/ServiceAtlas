/* ServiceAtlas 前端脚本 */

// 获取 base path（从模板传递）
const BASE_PATH = window.BASE_PATH || '';

// 通用 API 请求函数
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    // 如果 URL 以 / 开头，添加 BASE_PATH 前缀
    const fullUrl = url.startsWith('/') ? BASE_PATH + url : url;

    const response = await fetch(fullUrl, { ...defaultOptions, ...options });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(error.detail || '请求失败');
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// 页面加载完成事件
document.addEventListener('DOMContentLoaded', () => {
    console.log('ServiceAtlas 前端已加载');
});
