"use client"

import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bot, Plus, Settings, User } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('登出失败:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-card p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary rounded-lg">
              <Bot className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">AI API 开发平台</h1>
              <p className="text-muted-foreground">欢迎回来，{user?.username}！</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <User className="h-4 w-4 mr-2" />
              个人资料
            </Button>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              退出登录
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5 text-primary" />
                创建新任务
              </CardTitle>
              <CardDescription>
                使用AI生成新的API接口
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/tasks/create">
                <Button className="w-full">
                  开始创建
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-primary" />
                我的任务
              </CardTitle>
              <CardDescription>
                查看和管理已创建的任务
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/tasks">
                <Button variant="outline" className="w-full">
                  查看任务
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                API 测试
              </CardTitle>
              <CardDescription>
                测试生成的API接口
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/testing">
                <Button variant="outline" className="w-full">
                  开始测试
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* User Info */}
        <Card>
          <CardHeader>
            <CardTitle>账户信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">用户名</p>
                <p className="font-medium">{user?.username}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">邮箱</p>
                <p className="font-medium">{user?.email}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">角色</p>
                <p className="font-medium">{user?.role === 'admin' ? '管理员' : '用户'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">状态</p>
                <p className="font-medium">{user?.is_active ? '已激活' : '未激活'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}