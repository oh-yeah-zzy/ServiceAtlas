import { getBasePath } from '@/utils/basePath'

// 自动从 URL 推导网关前缀
const BASE_URL = getBasePath()

// 通用请求函数
async function request(url, options = {}) {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    credentials: 'same-origin',
    ...options
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

// 服务相关 API
export const servicesApi = {
  // 获取所有服务（返回 services 数组）
  getAll: async () => {
    const data = await request('/api/v1/services')
    return data.services || []
  },

  // 获取单个服务
  getById: (id) => request(`/api/v1/services/${id}`),

  // 注册服务（POST /api/v1/services）
  register: (data) => request('/api/v1/services', {
    method: 'POST',
    body: JSON.stringify(data)
  }),

  // 更新服务
  update: (id, data) => request(`/api/v1/services/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),

  // 删除服务
  delete: (id) => request(`/api/v1/services/${id}`, {
    method: 'DELETE'
  })
}

// 监控相关 API
export const monitorApi = {
  // 获取统计数据（后端端点是 /monitor/overview）
  getStats: () => request('/api/v1/monitor/overview'),

  // 触发健康检查
  triggerHealthCheck: () => request('/api/v1/monitor/health-check', {
    method: 'POST'
  })
}

// 依赖关系 API
export const dependenciesApi = {
  // 获取所有依赖
  getAll: () => request('/api/v1/dependencies'),

  // 获取服务的依赖
  getByService: (serviceId) => request(`/api/v1/dependencies/service/${serviceId}`)
}
