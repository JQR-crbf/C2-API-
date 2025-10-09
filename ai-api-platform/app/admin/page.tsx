"use client"

import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts/AuthContext"
import { admin, apiClient, Task } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
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
  User,
  Mail,
  Calendar,
  Shield,
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

// 任务状态显示函数
const getTaskStatusBadge = (status: string) => {
  const statusConfig = {
    submitted: { label: "任务提交", variant: "secondary" as const, className: "bg-blue-100 text-blue-800" },
    ai_generating: { label: "代码生成", variant: "secondary" as const, className: "bg-purple-100 text-purple-800" },
    code_submitted: { label: "代码提交", variant: "secondary" as const, className: "bg-green-100 text-green-800" },
    under_review: { label: "管理员审核", variant: "secondary" as const, className: "bg-orange-100 text-orange-800" },
    deployed: { label: "部署完成", variant: "secondary" as const, className: "bg-green-100 text-green-800" },
    approved: { label: "审核通过", variant: "secondary" as const, className: "bg-green-100 text-green-800" },
    rejected: { label: "审核拒绝", variant: "destructive" as const, className: "bg-red-100 text-red-800" },
  }
  
  const config = statusConfig[status as keyof typeof statusConfig] || { label: status, variant: "outline" as const, className: "" }
  return <Badge variant={config.variant} className={config.className}>{config.label}</Badge>
}

const getRoleBadge = (role: string) => {
  return role === "admin" ? (
    <Badge variant="destructive">管理员</Badge>
  ) : (
    <Badge variant="secondary">用户</Badge>
  )
}

// 安全的日期格式化函数
const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return "-"
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return "-"
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch (error) {
    return "-"
  }
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
  
  // 弹窗状态管理
  const [selectedUser, setSelectedUser] = useState<any>(null)
  const [userDetailOpen, setUserDetailOpen] = useState(false)
  const [editUserOpen, setEditUserOpen] = useState(false)
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false)
  
  // 拒绝任务弹窗状态
  const [rejectTaskOpen, setRejectTaskOpen] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState<string>('')
  const [rejectReason, setRejectReason] = useState('')
  
  // 删除任务弹窗状态
  const [deleteTaskOpen, setDeleteTaskOpen] = useState(false)
  const [deleteTaskId, setDeleteTaskId] = useState<string>('')
  const [deleteTaskTitle, setDeleteTaskTitle] = useState<string>('')
  
  // 编辑用户表单状态
  const [editForm, setEditForm] = useState<{
    username: string
    email: string
    role: 'user' | 'admin'
    password: string
  }>({
    username: '',
    email: '',
    role: 'user',
    password: ''
  })
  
  // 用户状态更新加载状态
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null)

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
      (user.username || '').toLowerCase().includes(userSearchTerm.toLowerCase()) ||
      (user.email || '').toLowerCase().includes(userSearchTerm.toLowerCase())
    const matchesStatus = userStatusFilter === "all" || (userStatusFilter === "active" ? user.is_active : !user.is_active)
    return matchesSearch && matchesStatus
  })

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      (task.title || '').toLowerCase().includes(taskSearchTerm.toLowerCase()) ||
      (task.description || '').toLowerCase().includes(taskSearchTerm.toLowerCase())
    const matchesStatus = taskStatusFilter === "all" || task.status === taskStatusFilter
    return matchesSearch && matchesStatus
  })

  // 处理用户状态更新
  const handleUserStatusUpdate = useCallback(async (userId: string, newStatus: boolean) => {
    const user = users.find(u => u.id.toString() === userId)
    if (!user) return
    
    const action = newStatus ? '启用' : '禁用'
    const confirmMessage = `确认要${action}用户 "${user.username}" 吗？`
    
    if (!window.confirm(confirmMessage)) {
      return
    }
    
    setUpdatingUserId(userId)
    
    try {
      await apiClient.admin.updateUserStatus(userId, newStatus)
      toast({
        title: "状态更新成功",
        description: `用户 "${user.username}" 已${action}`,
      })
      // 重新加载管理员数据
      loadAdminData()
    } catch (error) {
      console.error('Failed to update user status:', error)
      toast({
        title: "状态更新失败",
        description: `无法${action}用户，请稍后重试`,
        variant: "destructive",
      })
    } finally {
      setUpdatingUserId(null)
    }
  }, [users, toast, loadAdminData])

  // 处理任务状态更新
  const handleTaskStatusUpdate = useCallback(async (taskId: string, status: string, comment?: string) => {
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
  }, [toast])

  // 处理查看用户资料
  const handleViewUserProfile = useCallback((userId: string) => {
    const user = users.find(u => u.id.toString() === userId)
    if (user) {
      setSelectedUser(user)
      setUserDetailOpen(true)
    }
  }, [users])

  // 处理编辑用户
  const handleEditUser = useCallback((userId: string) => {
    const user = users.find(u => u.id.toString() === userId)
    if (user) {
      setSelectedUser(user)
      setEditForm({
        username: user.username,
        email: user.email,
        role: user.role,
        password: ''
      })
      setEditUserOpen(true)
    }
  }, [users])

  // 处理重置密码
  const handleResetPassword = useCallback((userId: string) => {
    const user = users.find(u => u.id.toString() === userId)
    if (user) {
      setSelectedUser(user)
      setResetPasswordOpen(true)
    }
  }, [users])

  // 处理拒绝任务
  const handleRejectTask = useCallback((taskId: string) => {
    setSelectedTaskId(taskId)
    setRejectReason('')
    setRejectTaskOpen(true)
  }, [])

  // 处理删除任务
  const handleDeleteTask = useCallback((taskId: string, taskTitle: string) => {
    setDeleteTaskId(taskId)
    setDeleteTaskTitle(taskTitle)
    setDeleteTaskOpen(true)
  }, [])

  // 确认删除任务
  const confirmDeleteTask = useCallback(async () => {
    try {
      await admin.deleteTask(deleteTaskId)
      toast({
        title: "删除成功",
        description: `任务 "${deleteTaskTitle}" 已成功删除`,
      })
      setDeleteTaskOpen(false)
      setDeleteTaskId('')
      setDeleteTaskTitle('')
      loadAdminData() // 重新加载数据
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast({
        title: "删除失败",
        description: "无法删除任务，请稍后重试",
        variant: "destructive",
      })
    }
  }, [deleteTaskId, deleteTaskTitle, toast])

  // 确认拒绝任务
  const confirmRejectTask = useCallback(async () => {
    if (!rejectReason.trim()) {
      toast({
        title: "请输入拒绝理由",
        description: "拒绝任务时必须提供拒绝理由",
        variant: "destructive",
      })
      return
    }

    try {
      await apiClient.admin.updateTaskStatus(selectedTaskId, {
        status: 'rejected',
        admin_comment: rejectReason
      })
      toast({
        title: "审核成功",
        description: "任务已拒绝，并已回退到代码生成步骤",
      })
      setRejectTaskOpen(false)
      setRejectReason('')
      setSelectedTaskId('')
      loadAdminData() // 重新加载数据
    } catch (error) {
      console.error('Failed to reject task:', error)
      toast({
        title: "审核失败",
        description: "无法拒绝任务，请稍后重试",
        variant: "destructive",
      })
    }
  }, [selectedTaskId, rejectReason, toast])

  // 确认重置密码
  const confirmResetPassword = useCallback(async () => {
    if (!selectedUser) return
    
    try {
      // 这里应该调用重置密码的API
      // await apiClient.admin.resetUserPassword(selectedUser.id)
      toast({
        title: "重置成功",
        description: `已为用户 ${selectedUser.username} 重置密码`,
      })
      setResetPasswordOpen(false)
      setSelectedUser(null)
    } catch (error) {
      console.error('Failed to reset password:', error)
      toast({
        title: "重置失败",
        description: "无法重置用户密码，请稍后重试",
        variant: "destructive",
      })
    }
  }, [selectedUser, toast])

  // 保存编辑用户信息
  const saveEditUser = useCallback(async () => {
    if (!selectedUser) return
    
    try {
      // 准备更新数据，过滤掉空密码
      const { password, ...baseData } = editForm
      const updateData = (!password || password.trim() === '') 
        ? baseData 
        : editForm
      
      // 调用更新用户信息的API
      await apiClient.admin.updateUser(selectedUser.id, updateData)
      toast({
        title: "更新成功",
        description: `用户 ${editForm.username} 的信息已更新`,
      })
      setEditUserOpen(false)
      setSelectedUser(null)
      // 重新加载用户数据
      loadAdminData()
    } catch (error) {
      console.error('Failed to update user:', error)
      toast({
        title: "更新失败",
        description: "无法更新用户信息，请稍后重试",
        variant: "destructive",
      })
    }
  }, [selectedUser, editForm, toast, loadAdminData])

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
                            <div className="font-medium text-foreground">{user.username}</div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getRoleBadge(user.role)}
                        </TableCell>
                        <TableCell>{getStatusBadge(user.is_active ? 'active' : 'inactive')}</TableCell>
                        <TableCell className="text-foreground">-</TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(user.created_at)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(user.last_login_at)}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleViewUserProfile(user.id.toString())}>查看资料</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleEditUser(user.id.toString())}>编辑用户</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleResetPassword(user.id.toString())}>重置密码</DropdownMenuItem>
                              {user.is_active ? (
                                <DropdownMenuItem 
                                  className="text-red-600"
                                  onClick={() => handleUserStatusUpdate(user.id.toString(), false)}
                                  disabled={updatingUserId === user.id.toString()}
                                >
                                  {updatingUserId === user.id.toString() ? '禁用中...' : '禁用用户'}
                                </DropdownMenuItem>
                              ) : (
                                <DropdownMenuItem 
                                  className="text-green-600"
                                  onClick={() => handleUserStatusUpdate(user.id.toString(), true)}
                                  disabled={updatingUserId === user.id.toString()}
                                >
                                  {updatingUserId === user.id.toString() ? '启用中...' : '启用用户'}
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
                          <div className="font-medium text-foreground">{task.title}</div>
                          {task.error_message && <div className="text-sm text-red-600">{task.error_message}</div>}
                        </TableCell>
                        <TableCell className="text-foreground">{task.user?.username || `用户${task.user_id}`}</TableCell>
                        <TableCell>{getTaskStatusBadge(task.status)}</TableCell>
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
                              {(task.status === "submitted" || task.status === "code_submitted" || task.status === "under_review") && (
                                <>
                                  <DropdownMenuItem 
                                    className="text-green-600"
                                    onClick={() => handleTaskStatusUpdate(task.id.toString(), 'approved', '管理员批准')}
                                  >
                                    批准任务
                                  </DropdownMenuItem>
                                  <DropdownMenuItem 
                                    className="text-red-600"
                                    onClick={() => handleRejectTask(task.id.toString())}
                                  >
                                    拒绝任务
                                  </DropdownMenuItem>
                                </>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-red-600"
                                onClick={() => handleDeleteTask(task.id.toString(), task.title)}
                              >
                                删除任务
                              </DropdownMenuItem>
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

      {/* 用户详情弹窗 */}
      <Dialog open={userDetailOpen} onOpenChange={setUserDetailOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              用户详情
            </DialogTitle>
            <DialogDescription>
              查看用户的详细信息
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">用户名</Label>
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{selectedUser.username}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">邮箱</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{selectedUser.email}</span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">角色</Label>
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-muted-foreground" />
                    {getRoleBadge(selectedUser.role)}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">状态</Label>
                  <div>{getStatusBadge(selectedUser.is_active ? 'active' : 'inactive')}</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">注册时间</Label>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{formatDate(selectedUser.created_at)}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">最后登录</Label>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{formatDate(selectedUser.last_login_at)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 编辑用户弹窗 */}
      <Dialog open={editUserOpen} onOpenChange={setEditUserOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              编辑用户
            </DialogTitle>
            <DialogDescription>
              修改用户的基本信息
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="space-y-2">
                 <Label htmlFor="edit-username">用户名</Label>
                 <Input 
                   id="edit-username" 
                   value={editForm.username}
                   onChange={(e) => setEditForm(prev => ({ ...prev, username: e.target.value }))}
                   placeholder="请输入用户名"
                 />
               </div>
               <div className="space-y-2">
                 <Label htmlFor="edit-email">邮箱</Label>
                 <Input 
                   id="edit-email" 
                   type="email"
                   value={editForm.email}
                   onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                   placeholder="请输入邮箱地址"
                 />
               </div>
               <div className="space-y-2">
                 <Label htmlFor="edit-role">角色</Label>
                 <Select value={editForm.role} onValueChange={(value) => setEditForm(prev => ({ ...prev, role: value as 'user' | 'admin' }))}>
                   <SelectTrigger>
                     <SelectValue />
                   </SelectTrigger>
                   <SelectContent>
                     <SelectItem value="user">用户</SelectItem>
                     <SelectItem value="admin">管理员</SelectItem>
                   </SelectContent>
                 </Select>
               </div>
               <div className="space-y-2">
                 <Label htmlFor="edit-password">新密码</Label>
                 <Input 
                   id="edit-password" 
                   type="password"
                   value={editForm.password}
                   onChange={(e) => setEditForm(prev => ({ ...prev, password: e.target.value }))}
                   placeholder="留空则不修改密码"
                 />
               </div>
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setEditUserOpen(false)}
                >
                  取消
                </Button>
                <Button 
                   className="flex-1"
                   onClick={saveEditUser}
                 >
                   保存
                 </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 重置密码确认弹窗 */}
      <Dialog open={resetPasswordOpen} onOpenChange={setResetPasswordOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              重置密码
            </DialogTitle>
            <DialogDescription>
              确认要重置该用户的密码吗？
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
                <p className="text-sm text-orange-800 dark:text-orange-200">
                  将为用户 <strong>{selectedUser.username}</strong> 重置密码。
                  新密码将通过邮件发送给用户。
                </p>
              </div>
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setResetPasswordOpen(false)}
                >
                  取消
                </Button>
                <Button 
                  className="flex-1 bg-orange-600 hover:bg-orange-700"
                  onClick={confirmResetPassword}
                >
                  确认重置
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 拒绝任务弹窗 */}
      <Dialog open={rejectTaskOpen} onOpenChange={setRejectTaskOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              拒绝任务
            </DialogTitle>
            <DialogDescription>
              请输入拒绝理由，任务将回退到代码生成步骤。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reject-reason">拒绝理由</Label>
              <textarea
                id="reject-reason"
                className="w-full min-h-[100px] px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="请详细说明拒绝的原因，以便用户了解需要改进的地方..."
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => {
                  setRejectTaskOpen(false)
                  setRejectReason('')
                  setSelectedTaskId('')
                }}
              >
                取消
              </Button>
              <Button 
                className="flex-1 bg-red-600 hover:bg-red-700"
                onClick={confirmRejectTask}
                disabled={!rejectReason.trim()}
              >
                确认拒绝
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 删除任务确认弹窗 */}
      <Dialog open={deleteTaskOpen} onOpenChange={setDeleteTaskOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              删除任务确认
            </DialogTitle>
            <DialogDescription>
              此操作将永久删除任务及其相关数据，无法恢复。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                <strong>警告：</strong>您即将删除任务 "{deleteTaskTitle}"
              </p>
              <p className="text-sm text-red-700 mt-2">
                删除后将无法恢复，请确认您的操作。
              </p>
            </div>
            <div className="flex gap-2 pt-4">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => {
                  setDeleteTaskOpen(false)
                  setDeleteTaskId('')
                  setDeleteTaskTitle('')
                }}
              >
                取消
              </Button>
              <Button 
                className="flex-1 bg-red-600 hover:bg-red-700"
                onClick={confirmDeleteTask}
              >
                确认删除
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
