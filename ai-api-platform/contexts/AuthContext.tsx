'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { auth, User, apiClient } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth 必须在 AuthProvider 内使用')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user

  // 初始化时检查用户状态
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const storedToken = localStorage.getItem('access_token')
      if (storedToken) {
        setToken(storedToken)
        // 将token设置到API客户端中
        apiClient.setToken(storedToken)
        const currentUser = await auth.getCurrentUser()
        setUser(currentUser)
      }
    } catch (error) {
      console.error('认证检查失败:', error)
      // 清除无效token
      localStorage.removeItem('access_token')
      setToken(null)
      apiClient.clearToken()
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await auth.login({ username, password })
      setToken(response.access_token)
      // 将token设置到API客户端中
      apiClient.setToken(response.access_token)
      setUser(response.user_info)
      toast.success('登录成功！')
      router.push('/')
    } catch (error) {
      const message = error instanceof Error ? error.message : '登录失败'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (email: string, password: string, fullName: string) => {
    try {
      setIsLoading(true)
      const response = await auth.register({
        email,
        password,
        full_name: fullName,
      })
      setToken(response.access_token)
      // 将token设置到API客户端中
      apiClient.setToken(response.access_token)
      setUser(response.user_info)
      toast.success('注册成功！')
      router.push('/')
    } catch (error) {
      const message = error instanceof Error ? error.message : '注册失败'
      toast.error(message)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await auth.logout()
    } catch (error) {
      console.error('登出错误:', error)
    } finally {
      setUser(null)
      setToken(null)
      // 清除API客户端中的token
      apiClient.clearToken()
      toast.success('已退出登录')
      router.push('/auth/login')
    }
  }

  const refreshUser = async () => {
    try {
      const currentUser = await auth.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      // 如果刷新失败，可能token已过期
      setUser(null)
      setToken(null)
      localStorage.removeItem('access_token')
    }
  }

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// 路由保护组件
interface ProtectedRouteProps {
  children: ReactNode
  requireAdmin?: boolean
}

export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/auth/login')
        return
      }
      
      if (requireAdmin && user?.role !== 'admin') {
        toast.error('需要管理员权限')
        router.push('/')
        return
      }
    }
  }, [isLoading, isAuthenticated, user, requireAdmin, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  if (requireAdmin && user?.role !== 'admin') {
    return null
  }

  return <>{children}</>
}