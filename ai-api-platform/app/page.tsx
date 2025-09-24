"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Bot,
  Plus,
  Activity,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp,
  Zap,
  Code,
  Users,
  Bell,
  Settings,
  LogOut,
} from "lucide-react"
import { useAuth, ProtectedRoute } from "@/contexts/AuthContext"
import { tasks, admin, Task } from "@/lib/api"
import Link from "next/link"
import { getProgressFromStatus, getStatusIcon, getStatusBadgeProps, getStatusText, categorizeTasksByStatus } from '@/lib/task-status'

// Mock data for demonstration
const mockStats = {
  totalTasks: 24,
  completedTasks: 18,
  inProgress: 4,
  failed: 2,
  successRate: 75,
}

const mockRecentTasks = [
  {
    id: 1,
    name: "用户认证API",
    status: "completed",
    progress: 100,
    createdAt: "2小时前",
    description: "创建登录和注册端点",
  },
  {
    id: 2,
    name: "产品目录API",
    status: "in-progress",
    progress: 65,
    createdAt: "4小时前",
    description: "产品管理的CRUD操作",
  },
  {
    id: 3,
    name: "支付处理API",
    status: "in-progress",
    progress: 30,
    createdAt: "6小时前",
    description: "与支付网关集成",
  },
  {
    id: 4,
    name: "邮件通知API",
    status: "failed",
    progress: 0,
    createdAt: "1天前",
    description: "发送自动邮件通知",
  },
]

const mockNotifications = [
  {
    id: 1,
    type: "success",
    message: "用户认证API部署成功",
    time: "10分钟前",
  },
  {
    id: 2,
    type: "info",
    message: "产品目录API已准备好测试",
    time: "1小时前",
  },
  {
    id: 3,
    type: "warning",
    message: "支付处理API需要审查",
    time: "2小时前",
  },
]

function DashboardContent() {
  const { user, logout } = useAuth()
  const [userTasks, setUserTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (user) {
      loadTasks()
    }
  }, [user])

  const loadTasks = async () => {
    try {
      let tasksData
      // 根据用户角色调用不同的API
      if (user?.role === 'admin') {
        tasksData = await admin.getTasks()
      } else {
        tasksData = await tasks.getAll()
      }
      
      // 处理返回的数据格式，并为每个任务添加progress字段
      const tasksList = tasksData?.tasks || tasksData || []
      const tasksWithProgress = Array.isArray(tasksList) ? tasksList.map(task => ({
        ...task,
        progress: getProgressFromStatus(task.status)
      })) : []
      setUserTasks(tasksWithProgress)
    } catch (error) {
      console.error('Failed to load tasks:', error)
      // 出错时设置为空数组
      setUserTasks([])
    } finally {
      setIsLoading(false)
    }
  }

  // 根据状态分类任务
  const { completed, inProgress, pending, failed } = categorizeTasksByStatus(userTasks)

  const stats = {
    totalTasks: userTasks.length,
    completedTasks: completed.length,
    inProgress: inProgress.length,
    failed: failed.length,
    successRate: userTasks.length > 0 ? Math.round((completed.length / userTasks.length) * 100) : 0,
  }

  const recentTasks = userTasks.slice(0, 4)







  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">AI API 开发平台</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm">
              <Bell className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">欢迎，</span>
              <span className="font-medium text-foreground">{user?.full_name || user?.username || user?.email}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="p-6 space-y-6">
        {/* Welcome Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">控制台</h1>
            <p className="text-muted-foreground mt-1">监控您的API开发进度并管理任务</p>
          </div>
          <Link href="/tasks/create">
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
              <Plus className="h-4 w-4 mr-2" />
              创建新API
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">总任务数</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stats.totalTasks}</div>
              <p className="text-xs text-muted-foreground">您的所有API任务</p>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">已完成</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stats.completedTasks}</div>
              <p className="text-xs text-muted-foreground">成功完成的任务</p>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">进行中</CardTitle>
              <Clock className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stats.inProgress}</div>
              <p className="text-xs text-muted-foreground">正在处理的任务</p>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">成功率</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stats.successRate}%</div>
              <p className="text-xs text-muted-foreground">任务完成成功率</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Tasks */}
          <div className="lg:col-span-2">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-foreground">最近任务</CardTitle>
                <CardDescription>您最新的API开发任务及其进度</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : recentTasks.length > 0 ? (
                  recentTasks.map((task) => (
                    <Link key={task.id} href={`/tasks/${task.id}`}>
                      <div className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors cursor-pointer">
                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            {getStatusIcon(task.status)}
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-foreground truncate">{task.name || task.title}</h4>
                              <p className="text-sm text-muted-foreground truncate">{task.description}</p>
                            </div>
                          </div>
                          <div className="flex-shrink-0">
                            <Badge {...getStatusBadgeProps(task.status)} />
                          </div>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2 flex-1">
                            <Progress value={task.progress || getProgressFromStatus(task.status)} className="flex-1 max-w-[120px]" />
                            <span className="text-xs text-muted-foreground whitespace-nowrap">{task.progress || getProgressFromStatus(task.status)}%</span>
                          </div>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {task.created_at ? new Date(task.created_at).toLocaleDateString('zh-CN') : '未知时间'}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">还没有任务</p>
                    <Link href="/tasks/create">
                      <Button className="mt-4">
                        <Plus className="h-4 w-4 mr-2" />
                        创建第一个API
                      </Button>
                    </Link>
                  </div>
                )}
                <div className="pt-4">
                  <Link href="/tasks">
                    <Button variant="outline" className="w-full bg-transparent">
                      查看所有任务
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions & Notifications */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-foreground">快速操作</CardTitle>
                <CardDescription>常用任务和快捷方式</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link href="/tasks/create">
                  <Button variant="outline" className="w-full justify-start bg-transparent">
                    <Plus className="h-4 w-4 mr-2" />
                    创建新API
                  </Button>
                </Link>
                <Link href="/testing">
                  <Button variant="outline" className="w-full justify-start bg-transparent">
                    <Zap className="h-4 w-4 mr-2" />
                    测试API
                  </Button>
                </Link>
                <Link href="/environments">
                  <Button variant="outline" className="w-full justify-start bg-transparent">
                    <Code className="h-4 w-4 mr-2" />
                    管理环境
                  </Button>
                </Link>
                <Link href="/admin">
                  <Button variant="outline" className="w-full justify-start bg-transparent">
                    <Users className="h-4 w-4 mr-2" />
                    管理面板
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Recent Notifications */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-foreground">通知</CardTitle>
                <CardDescription>最新更新和提醒</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockNotifications.map((notification) => (
                  <div key={notification.id} className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                    <div
                      className={`p-1 rounded-full ${
                        notification.type === "success"
                          ? "bg-green-100"
                          : notification.type === "warning"
                            ? "bg-yellow-100"
                            : "bg-blue-100"
                      }`}
                    >
                      {notification.type === "success" && <CheckCircle className="h-3 w-3 text-green-600" />}
                      {notification.type === "warning" && <AlertCircle className="h-3 w-3 text-yellow-600" />}
                      {notification.type === "info" && <Activity className="h-3 w-3 text-blue-600" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">{notification.time}</p>
                    </div>
                  </div>
                ))}
                <Link href="/notifications">
                  <Button variant="outline" className="w-full bg-transparent">
                    查看所有通知
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}
