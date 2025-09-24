"use client"

import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts/AuthContext"
import { admin, apiClient, Task } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  Bot,
  ArrowLeft,
  Users,
  Activity,
  Settings,
  MoreHorizontal,
  Search,
  Filter,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
} from "lucide-react"
import Link from "next/link"
import { ProtectedRoute } from "@/contexts/AuthContext"

// 状态显示辅助函数
const getStatusBadge = (status: string) => {
  const statusConfig = {
    active: { label: "活跃", variant: "default" as const },
    inactive: { label: "非活跃", variant: "secondary" as const },
    pending: { label: "待处理", variant: "outline" as const },
    completed: { label: "已完成", variant: "default" as const },
    "in-progress": { label: "进行中", variant: "secondary" as const },
    failed: { label: "失败", variant: "destructive" as const },
  }
  
  const config = statusConfig[status as keyof typeof statusConfig] || { label: status, variant: "outline" as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}

const getRoleBadge = (role: string) => {
  return role === "admin" ? (
    <Badge variant="destructive">管理员</Badge>
  ) : (
    <Badge variant="secondary">用户</Badge>
  )
}

export default function AdminPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [stats, setStats] = useState({
    total_users: 0,
    total_tasks: 0,
    completed_tasks: 0,
    pending_tasks: 0,
    success_rate: 0,
  })
  const [users, setUsers] = useState<any[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const mockSystemMetrics = [
    { name: "API生成成功率", value: "94.2%", trend: "up", color: "text-green-600" },
    { name: "平均响应时间", value: "1.2s", trend: "down", color: "text-green-600" },
    { name: "系统正常运行时间", value: "99.9%", trend: "stable", color: "text-green-600" },
    { name: "活跃环境数", value: "156", trend: "up", color: "text-blue-600" },
    { name: "存储使用率", value: "67%", trend: "up", color: "text-yellow-600" },
    { name: "错误率", value: "0.8%", trend: "down", color: "text-green-600" },
  ]
  const [userSearchTerm, setUserSearchTerm] = useState("")
  const [taskSearchTerm, setTaskSearchTerm] = useState("")
  const [userStatusFilter, setUserStatusFilter] = useState("all")
  const [taskStatusFilter, setTaskStatusFilter] = useState("all")

  useEffect(() => {
    loadAdminData()
  }, [])

  const loadAdminData = async () => {
    try {
      setIsLoading(true)
      // 加载统计数据
      const statsData = await admin.getStats()
      setStats(statsData)
      
      // 加载用户列表
      const usersData = await admin.getUsers()
      setUsers(usersData || [])
      
      // 加载任务列表
      const tasksResponse = await admin.getTasks()
      const tasksData = tasksResponse.tasks || tasksResponse || []
      setTasks(tasksData)
    } catch (error) {
      console.error('Failed to load admin data:', error)
      toast({
        title: "加载失败",
        description: "无法加载管理员数据，请稍后重试",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }



  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "high":
        return <Badge variant="destructive">高</Badge>
      case "medium":
        return <Badge variant="secondary">中</Badge>
      case "low":
        return <Badge variant="outline">低</Badge>
      default:
        return <Badge variant="outline">未知</Badge>
    }
  }

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
    const matchesStatus = userStatusFilter === "all" || user.status === userStatusFilter
    return matchesSearch && matchesStatus
  })

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      ((task.name || task.title) || '').toLowerCase().includes(taskSearchTerm.toLowerCase()) ||
      (task.description || '').toLowerCase().includes(taskSearchTerm.toLowerCase())
    const matchesStatus = taskStatusFilter === "all" || task.status === taskStatusFilter
    return matchesSearch && matchesStatus
  })

  // 处理用户状态更新
  const handleUserStatusUpdate = async (userId: string, isActive: boolean) => {
    try {
      await apiClient.admin.updateUserStatus(userId, isActive)
      toast({
        title: "更新成功",
        description: `用户状态已${isActive ? '启用' : '禁用'}`,
      })
      loadAdminData() // 重新加载数据
    } catch (error) {
      console.error('Failed to update user status:', error)
      toast({
        title: "更新失败",
        description: "无法更新用户状态，请稍后重试",
        variant: "destructive",
      })
    }
  }

  // 处理任务状态更新
  const handleTaskStatusUpdate = async (taskId: string, status: string, comment?: string) => {
    try {
      await apiClient.admin.updateTaskStatus(taskId, {
        status: status,
        admin_comment: comment
      })
      toast({
        title: "审核成功",
        description: `任务已${status === 'approved' ? '批准' : '拒绝'}`,
      })
      loadAdminData() // 重新加载数据
    } catch (error) {
      console.error('Failed to update task status:', error)
      toast({
        title: "审核失败",
        description: "无法更新任务状态，请稍后重试",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">管理面板</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              系统设置
            </Button>
          </div>
        </div>
      </header>

      <div className="p-6 space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">管理控制台</h1>
          <p className="text-muted-foreground mt-1">监控系统性能并管理用户</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-foreground">{stats.total_users}</div>
                  <p className="text-sm text-muted-foreground">总用户数</p>
                </div>
                <Users className="h-8 w-8 text-primary" />
              </div>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="h-3 w-3 text-green-600" />
                <span className="text-xs text-green-600">总计{stats.total_tasks}个任务</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-foreground">{stats.pending_tasks}</div>
                  <p className="text-sm text-muted-foreground">待处理任务</p>
                </div>
                <Clock className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-foreground">{stats.completed_tasks}</div>
                  <p className="text-sm text-muted-foreground">已完成</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-foreground">{stats.success_rate}%</div>
                  <p className="text-sm text-muted-foreground">成功率</p>
                </div>
                <Activity className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-foreground">3</div>
                  <p className="text-sm text-muted-foreground">警报</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="users" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="users">用户管理</TabsTrigger>
            <TabsTrigger value="tasks">任务监控</TabsTrigger>
            <TabsTrigger value="system">系统指标</TabsTrigger>
            <TabsTrigger value="settings">配置</TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle>用户管理</CardTitle>
                <CardDescription>管理用户账户和权限</CardDescription>
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="搜索用户..."
                      value={userSearchTerm}
                      onChange={(e) => setUserSearchTerm(e.target.value)}
                      className="pl-10 bg-input border-border"
                    />
                  </div>
                  <Select value={userStatusFilter} onValueChange={setUserStatusFilter}>
                    <SelectTrigger className="w-full sm:w-[180px] bg-input border-border">
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue placeholder="按状态筛选" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有状态</SelectItem>
                      <SelectItem value="active">活跃</SelectItem>
                      <SelectItem value="inactive">非活跃</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>用户</TableHead>
                      <TableHead>角色</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>任务</TableHead>
                      <TableHead>加入时间</TableHead>
                      <TableHead>最后活跃</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium text-foreground">{user.name}</div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getRoleBadge(user.role)}
                        </TableCell>
                        <TableCell>{getStatusBadge(user.status)}</TableCell>
                        <TableCell className="text-foreground">{user.tasksCompleted}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(user.joinedAt).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(user.lastActive).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>查看资料</DropdownMenuItem>
                              <DropdownMenuItem>编辑用户</DropdownMenuItem>
                              <DropdownMenuItem>重置密码</DropdownMenuItem>
                              {user.is_active ? (
                                <DropdownMenuItem 
                                  className="text-red-600"
                                  onClick={() => handleUserStatusUpdate(user.id.toString(), false)}
                                >
                                  禁用用户
                                </DropdownMenuItem>
                              ) : (
                                <DropdownMenuItem 
                                  className="text-green-600"
                                  onClick={() => handleUserStatusUpdate(user.id.toString(), true)}
                                >
                                  启用用户
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle>任务监控</CardTitle>
                <CardDescription>监控和审核用户任务</CardDescription>
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="搜索任务..."
                      value={taskSearchTerm}
                      onChange={(e) => setTaskSearchTerm(e.target.value)}
                      className="pl-10 bg-input border-border"
                    />
                  </div>
                  <Select value={taskStatusFilter} onValueChange={setTaskStatusFilter}>
                    <SelectTrigger className="w-full sm:w-[180px] bg-input border-border">
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue placeholder="按状态筛选" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有状态</SelectItem>
                      <SelectItem value="completed">已完成</SelectItem>
                      <SelectItem value="in-progress">进行中</SelectItem>
                      <SelectItem value="in-review">审核中</SelectItem>
                      <SelectItem value="failed">失败</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>任务</TableHead>
                      <TableHead>用户</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>优先级</TableHead>
                      <TableHead>审核状态</TableHead>
                      <TableHead>创建时间</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>
                          <div className="font-medium text-foreground">{task.name || task.title}</div>
                          {task.error_message && <div className="text-sm text-red-600">{task.error_message}</div>}
                        </TableCell>
                        <TableCell className="text-foreground">{task.user_id}</TableCell>
                        <TableCell>{getStatusBadge(task.status)}</TableCell>
                        <TableCell>
                          <Badge variant="outline">待处理</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(task.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>查看详情</DropdownMenuItem>
                              <DropdownMenuItem>审核代码</DropdownMenuItem>
                              {(task.status === "pending" || task.status === "in-progress") && (
                                <>
                                  <DropdownMenuItem 
                                    className="text-green-600"
                                    onClick={() => handleTaskStatusUpdate(task.id.toString(), 'approved', '管理员批准')}
                                  >
                                    批准任务
                                  </DropdownMenuItem>
                                  <DropdownMenuItem 
                                    className="text-red-600"
                                    onClick={() => handleTaskStatusUpdate(task.id.toString(), 'rejected', '管理员拒绝')}
                                  >
                                    拒绝任务
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="system" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mockSystemMetrics.map((metric, index) => (
                <Card key={index} className="border-border">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">{metric.name}</p>
                        <div className="text-2xl font-bold text-foreground mt-1">{metric.value}</div>
                      </div>
                      <div className={`text-right ${metric.color}`}>
                        <TrendingUp className="h-4 w-4 mb-1" />
                        <p className="text-xs capitalize">{metric.trend}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="border-border">
              <CardHeader>
                <CardTitle>系统警报</CardTitle>
                <CardDescription>最近的系统通知和警报</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">存储使用率过高</h4>
                    <p className="text-sm text-yellow-700">
                      存储使用率为67%。建议清理旧的测试环境。
                    </p>
                    <p className="text-xs text-yellow-600 mt-1">2小时前</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <Activity className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-800">系统维护计划</h4>
                    <p className="text-sm text-blue-700">
                      计划维护时间：2024年1月20日 上午2:00 - 上午4:00 UTC
                    </p>
                    <p className="text-xs text-blue-600 mt-1">1天前</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-800">系统更新完成</h4>
                    <p className="text-sm text-green-700">
                      AI模型已更新至Claude Sonnet 4.1，代码生成能力得到改进。
                    </p>
                    <p className="text-xs text-green-600 mt-1">3天前</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="border-border">
                <CardHeader>
                  <CardTitle>系统配置</CardTitle>
                  <CardDescription>管理系统全局设置</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">AI模型</Label>
                    <Select defaultValue="claude-sonnet-4">
                      <SelectTrigger className="bg-input border-border">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="claude-sonnet-4">Claude Sonnet 4</SelectItem>
                        <SelectItem value="claude-sonnet-3.5">Claude Sonnet 3.5</SelectItem>
                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">最大并发任务数</Label>
                    <Input type="number" defaultValue="50" className="bg-input border-border" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">任务超时时间（分钟）</Label>
                    <Input type="number" defaultValue="30" className="bg-input border-border" />
                  </div>
                  <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                    保存配置
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-border">
                <CardHeader>
                  <CardTitle>安全设置</CardTitle>
                  <CardDescription>配置安全和访问控制</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">会话超时时间（小时）</Label>
                    <Input type="number" defaultValue="24" className="bg-input border-border" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">最大登录尝试次数</Label>
                    <Input type="number" defaultValue="5" className="bg-input border-border" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-foreground">密码策略</Label>
                    <Select defaultValue="strong">
                      <SelectTrigger className="bg-input border-border">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="basic">基础（8位以上字符）</SelectItem>
                        <SelectItem value="strong">强（8位以上，大小写混合，数字）</SelectItem>
                        <SelectItem value="very-strong">很强（12位以上，包含符号）</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                    更新安全设置
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
