// API客户端工具 - 处理所有HTTP请求和认证

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

// 认证相关类型
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_info: {
    id: number
    username: string
    email: string
    role: 'user' | 'admin'
    is_active: boolean
    created_at: string
    full_name?: string
  }
}

// 通知相关类型
export interface Notification {
  id: string
  type: 'success' | 'info' | 'warning' | 'error'
  message: string
  title?: string
  created_at: string
  read: boolean
  user_id: string
}

export interface CreateNotificationRequest {
  type: 'success' | 'info' | 'warning' | 'error'
  message: string
  title?: string
}

// 任务相关类型
export interface CreateTaskRequest {
  name: string
  description: string
  language: string
  framework: string
  database: string
  features: string[]
}

export interface Task {
  id: string
  title: string  // 改为title以匹配后端
  name?: string  // 兼容字段
  description: string
  status: 'pending' | 'in-progress' | 'completed' | 'failed' | 'testing'
  progress?: number  // 可选字段
  language?: string
  framework?: string
  database?: string
  features?: string[]
  logs?: any[]
  error_message?: string
  input_params?: {
    language?: string
    framework?: string
    database?: string
    features?: string[]
  }
  output_params?: any
  created_at: string
  updated_at: string
  user_id: string
  generated_code?: string
  branch_name?: string
  test_cases?: string
  test_result_image?: string
  test_url?: string
  admin_comment?: string
  user?: any
}

// API测试相关类型
export interface APITestRequest {
  method: string
  url: string
  headers?: Record<string, string>
  body?: string
}

export interface APITestResponse {
  status: number
  statusText: string
  headers: Record<string, string>
  data: any
  responseTime: number
}

// 用户管理类型
export interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
  full_name?: string
}

// API客户端类
class APIClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
    // 从localStorage获取token
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token')
    }
  }

  // 设置认证token
  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token)
    }
  }

  // 清除认证token
  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
  }

  // 获取认证头
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    
    return headers
  }

  // 通用请求方法
  protected async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const config: RequestInit = {
      headers: this.getAuthHeaders(),
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: '网络错误' }))
        throw new Error(errorData.message || `HTTP错误! 状态: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // 认证相关API
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '登录失败' }))
      throw new Error(errorData.detail || '登录失败')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '注册失败' }))
      throw new Error(errorData.detail || '注册失败')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async logout(): Promise<void> {
    try {
      await this.request('/api/auth/logout', { method: 'POST' })
    } finally {
      this.clearToken()
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/auth/me')
  }

  // 任务相关API
  async createTask(taskData: CreateTaskRequest): Promise<Task> {
    return this.request<Task>('/api/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData),
    })
  }

  async getTasks(): Promise<Task[]> {
    const response = await this.request<{tasks: Task[], total: number, page: number, size: number}>('/api/tasks/')
    return response.tasks || []
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}`)
  }

  async deleteTask(taskId: string): Promise<void> {
    return this.request<void>(`/api/tasks/${taskId}`, {
      method: 'DELETE',
    })
  }

  // API测试相关
  async testAPI(testData: APITestRequest): Promise<APITestResponse> {
    return this.request<APITestResponse>('/api/testing/api', {
      method: 'POST',
      body: JSON.stringify(testData),
    })
  }

  async getTestEndpoints(): Promise<any> {
    return this.request<any>('/api/testing/endpoints')
  }

  async getSampleTestData(): Promise<any> {
    return this.request<any>('/api/testing/sample-data')
  }

  // 管理员相关API
  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/api/admin/users')
  }

  async updateUser(userId: string, userData: Partial<User>): Promise<User> {
    return this.request<User>(`/api/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    })
  }

  async deleteUser(userId: string): Promise<void> {
    return this.request<void>(`/api/admin/users/${userId}`, {
      method: 'DELETE',
    })
  }

  async getSystemStats(): Promise<any> {
    return this.request<any>('/api/admin/stats')
  }

  // 文件下载
  async downloadTaskCode(taskId: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/tasks/${taskId}/download`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error('下载失败')
    }
    
    return response.blob()
  }

  // 通知相关方法
  async getNotifications(): Promise<Notification[]> {
    return this.request<Notification[]>('/api/notifications')
  }

  async markNotificationAsRead(notificationId: string): Promise<void> {
    return this.request<void>(`/api/notifications/${notificationId}/read`, {
      method: 'PUT',
    })
  }

  async markAllNotificationsAsRead(): Promise<void> {
    return this.request<void>('/api/notifications/read-all', {
      method: 'PUT',
    })
  }

  async deleteNotification(notificationId: string): Promise<void> {
    return this.request<void>(`/api/notifications/${notificationId}`, {
      method: 'DELETE',
    })
  }
}

// 创建全局API客户端实例
class EnhancedAPIClient extends APIClient {
  // 任务相关API的增强版本
  tasks = {
    create: (taskData: CreateTaskRequest) => this.createTask(taskData),
    getAll: () => this.getTasks(),
    getById: (id: string) => this.getTask(id),
    delete: (id: string) => this.deleteTask(id),
    downloadCode: (id: string) => this.downloadTaskCode(id),
  }

  // 认证相关API
  auth = {
    login: (credentials: LoginRequest) => this.login(credentials),
    register: (userData: RegisterRequest) => this.register(userData),
    logout: () => this.logout(),
    getCurrentUser: () => this.getCurrentUser(),
  }

  // 测试相关API
  testing = {
    testAPI: (testData: APITestRequest) => this.testAPI(testData),
  }

  // 管理员相关API
  notifications = {
    getAll: () => this.getNotifications(),
    markAsRead: (id: string) => this.markNotificationAsRead(id),
    markAllAsRead: () => this.markAllNotificationsAsRead(),
    delete: (id: string) => this.deleteNotification(id),
  }

  admin = {
    getUsers: () => this.getUsers(),
    updateUser: (id: string, data: Partial<User>) => this.updateUser(id, data),
    deleteUser: (id: string) => this.deleteUser(id),
    getStats: () => this.getSystemStats(),
    getTasks: () => this.request<any>('/api/admin/tasks'),
    getTask: (taskId: string) => this.request<Task>(`/api/admin/tasks/${taskId}`),
    updateTaskStatus: (taskId: string, data: any) => this.request<any>(`/api/admin/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    updateUserStatus: (userId: string, isActive: boolean) => this.request<any>(`/api/admin/users/${userId}/status?is_active=${isActive}`, {
      method: 'PUT',
    }),
    sendNotification: (data: any) => this.request<any>('/api/admin/notifications', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  }
}

export const apiClient = new EnhancedAPIClient()

// 导出便捷方法（保持向后兼容）
export const auth = {
  login: (credentials: LoginRequest) => apiClient.login(credentials),
  register: (userData: RegisterRequest) => apiClient.register(userData),
  logout: () => apiClient.logout(),
  getCurrentUser: () => apiClient.getCurrentUser(),
}

export const tasks = {
  create: (taskData: CreateTaskRequest) => apiClient.createTask(taskData),
  getAll: () => apiClient.getTasks(),
  getById: (id: string) => apiClient.getTask(id),
  delete: (id: string) => apiClient.deleteTask(id),
  downloadCode: (id: string) => apiClient.downloadTaskCode(id),
}

export const testing = {
  testAPI: (testData: APITestRequest) => apiClient.testAPI(testData),
}

export const notifications = {
  getAll: () => apiClient.getNotifications(),
  markAsRead: (id: string) => apiClient.markNotificationAsRead(id),
  markAllAsRead: () => apiClient.markAllNotificationsAsRead(),
  delete: (id: string) => apiClient.deleteNotification(id),
}

export const admin = {
  getUsers: () => apiClient.getUsers(),
  updateUser: (id: string, data: Partial<User>) => apiClient.updateUser(id, data),
  deleteUser: (id: string) => apiClient.deleteUser(id),
  getStats: () => apiClient.getSystemStats(),
  getTasks: () => apiClient.admin.getTasks(),
  getTask: (taskId: string) => apiClient.admin.getTask(taskId),
  updateTaskStatus: (taskId: string, data: any) => apiClient.admin.updateTaskStatus(taskId, data),
}

export default apiClient