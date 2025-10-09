"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Bot,
  Plus,
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  Download,
  MoreHorizontal,
  ArrowLeft,
} from "lucide-react"
import Link from "next/link"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { apiClient, Task, admin, tasks } from "@/lib/api"
import { toast } from "@/hooks/use-toast"
import { useAuth } from "@/contexts/AuthContext"
import { getStatusBadgeProps, categorizeTasksByStatus } from "@/lib/task-status"

export default function TasksPage() {
  const { user } = useAuth()
  const [tasksList, setTasksList] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [priorityFilter, setPriorityFilter] = useState("all")
  const [sortBy, setSortBy] = useState("newest")

   // Helper function to get progress from status
   const getProgressFromStatus = (status: string) => {
     switch (status) {
       case 'pending': return 0
       case 'in_progress': return 50
       case 'completed': return 100
       case 'failed': return 0
       default: return 0
     }
   }

  // Fetch tasks from API
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true)
        let tasksData
        
        // 根据用户角色调用不同的API端点
        if (user?.role === 'admin') {
          // 管理员获取所有任务
          const response = await admin.getTasks()
          tasksData = response.tasks || []
        } else {
          // 普通用户获取自己的任务
          tasksData = await tasks.getAll()
        }
        
        // Ensure tasksData is always an array
        setTasksList(Array.isArray(tasksData) ? tasksData : [])
      } catch (error) {
        console.error('Failed to fetch tasks:', error)
        // Ensure tasks is set to empty array on error
        setTasksList([])
        toast({
          title: "错误",
          description: "获取任务列表失败",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    // 只有在用户信息加载完成后才获取任务
    if (user) {
      fetchTasks()
    }
  }, [user])

  // Listen for real-time task updates in a separate useEffect
  useEffect(() => {
    const handleTaskUpdate = (event: CustomEvent) => {
      const taskData = event.detail
      // Use setTimeout to defer the state update to avoid render-time setState
      setTimeout(() => {
        setTasksList(prevTasks => {
          // Ensure prevTasks is always an array
          const tasksArray = Array.isArray(prevTasks) ? prevTasks : []
          return tasksArray.map(task => 
            task.id === taskData.task_id ? { 
              ...task, 
              status: taskData.status,
              progress: getProgressFromStatus(taskData.status)
            } : task
          )
        })
      }, 0)
    }

    window.addEventListener('task-status-updated', handleTaskUpdate as EventListener)

    return () => {
      window.removeEventListener('task-status-updated', handleTaskUpdate as EventListener)
    }
  }, [])

   // Handle task download
   const handleDownload = async (taskId: string) => {
     try {
       const blob = await apiClient.tasks.downloadCode(taskId)
       const url = window.URL.createObjectURL(blob)
       const a = document.createElement('a')
       a.style.display = 'none'
       a.href = url
       a.download = `task-${taskId}-code.zip`
       document.body.appendChild(a)
       a.click()
       window.URL.revokeObjectURL(url)
       document.body.removeChild(a)
       
       toast({
         title: "下载成功",
         description: "任务代码已开始下载",
       })
     } catch (error) {
       console.error('Download failed:', error)
       toast({
         title: "下载失败",
         description: "无法下载任务代码，请稍后重试",
         variant: "destructive",
       })
     }
   }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "in-progress":
        return <Clock className="h-4 w-4 text-blue-600" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case "pending":
        return <Clock className="h-4 w-4 text-gray-400" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getPriorityBadgeProps = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case "high":
        return { variant: "destructive" as const, children: "高优先级" }
      case "medium":
        return { variant: "secondary" as const, children: "中优先级" }
      case "low":
        return { variant: "outline" as const, children: "低优先级" }
      default:
        return { variant: "secondary" as const, children: "中优先级" }
    }
  }



  // Ensure tasks is always an array before filtering
  const tasksArray = Array.isArray(tasksList) ? tasksList : []
  
  const filteredTasks = tasksArray
    .filter((task) => {
      const taskTitle = task.title || task.name || ''
      const taskDescription = task.description || ''
      const matchesSearch =
        taskTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        taskDescription.toLowerCase().includes(searchTerm.toLowerCase())
      
      // 使用与控制台页面相同的状态分类逻辑
      let matchesStatus = true
      if (statusFilter !== "all") {
        const taskCategories = categorizeTasksByStatus([task])
        switch (statusFilter) {
          case "completed":
            matchesStatus = taskCategories.completed.length > 0
            break
          case "in-progress":
            matchesStatus = taskCategories.inProgress.length > 0
            break
          case "pending":
            matchesStatus = taskCategories.pending.length > 0
            break
          case "failed":
            matchesStatus = taskCategories.failed.length > 0
            break
          default:
            matchesStatus = true
        }
      }
      
      // 优先级筛选
      const matchesPriority = priorityFilter === "all" || task.priority === priorityFilter
      
      return matchesSearch && matchesStatus && matchesPriority
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "newest":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        case "oldest":
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        case "name":
          const aTitle = a.title || a.name || ''
          const bTitle = b.title || b.name || ''
          return aTitle.localeCompare(bTitle)
        case "progress":
          const aProgress = a.progress || getProgressFromStatus(a.status)
          const bProgress = b.progress || getProgressFromStatus(b.status)
          return bProgress - aProgress
        default:
          return 0
      }
    })

  // 使用与控制台页面相同的分类逻辑
  const { completed, inProgress, pending, failed } = categorizeTasksByStatus(tasksArray)
  
  const statusCounts = {
    all: tasksArray.length,
    completed: completed.length,
    "in-progress": inProgress.length,
    failed: failed.length,
    pending: pending.length,
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
              <span className="text-xl font-bold text-foreground">任务管理</span>
            </div>
          </div>
          <Link href="/tasks/create">
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
              <Plus className="h-4 w-4 mr-2" />
              创建新任务
            </Button>
          </Link>
        </div>
      </header>

      <div className="p-6 space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">所有任务</h1>
          <p className="text-muted-foreground mt-1">管理和监控您的API开发任务</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-foreground">{statusCounts.all}</div>
              <p className="text-sm text-muted-foreground">总任务数</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{statusCounts.completed}</div>
              <p className="text-sm text-muted-foreground">已完成</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">{statusCounts["in-progress"]}</div>
              <p className="text-sm text-muted-foreground">进行中</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-gray-600">{statusCounts.pending}</div>
              <p className="text-sm text-muted-foreground">待处理</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{statusCounts.failed}</div>
              <p className="text-sm text-muted-foreground">失败</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索任务..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-input border-border"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[180px] bg-input border-border">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="按状态筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有状态</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="in-progress">进行中</SelectItem>
              <SelectItem value="pending">待处理</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className="w-full sm:w-[180px] bg-input border-border">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="按优先级筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有优先级</SelectItem>
              <SelectItem value="high">高优先级</SelectItem>
              <SelectItem value="medium">中优先级</SelectItem>
              <SelectItem value="low">低优先级</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full sm:w-[180px] bg-input border-border">
              <SelectValue placeholder="排序方式" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">最新优先</SelectItem>
              <SelectItem value="oldest">最旧优先</SelectItem>
              <SelectItem value="name">名称A-Z</SelectItem>
              <SelectItem value="progress">进度</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Tasks List */}
        <div className="space-y-4">
          {loading ? (
            <Card className="border-border">
              <CardContent className="p-8 text-center">
                <div className="text-muted-foreground">
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-50 animate-pulse" />
                  <h3 className="text-lg font-medium mb-2">加载中...</h3>
                  <p className="text-sm">正在获取任务列表</p>
                </div>
              </CardContent>
            </Card>
          ) : filteredTasks.length === 0 ? (
            <Card className="border-border">
              <CardContent className="p-8 text-center">
                <div className="text-muted-foreground">
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">未找到任务</h3>
                  <p className="text-sm">请尝试调整搜索或筛选条件</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            filteredTasks.map((task) => (
              <Card key={task.id} className="border-border hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {/* Header with title, status and actions */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        {getStatusIcon(task.status)}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-foreground truncate">{task.title || task.name}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge {...getStatusBadgeProps(task.status)} />
                            {task.priority && <Badge {...getPriorityBadgeProps(task.priority)} />}
                          </div>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex-shrink-0">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => window.location.href = `/tasks/${task.id}`}>
                              <Eye className="h-4 w-4 mr-2" />
                              查看详情
                            </DropdownMenuItem>
                            {task.status === "deployed" && (
                              <DropdownMenuItem onClick={() => handleDownload(task.id)}>
                                <Download className="h-4 w-4 mr-2" />
                                下载代码
                              </DropdownMenuItem>
                            )}
                            {task.status === "rejected" && (
                              <DropdownMenuItem>
                                <Clock className="h-4 w-4 mr-2" />
                                重试任务
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-muted-foreground break-words">{task.description}</p>

                    {/* Progress Bar */}
                    {(task.status === "ai_generating" || task.status === "code_submitted" || task.status === "under_review") && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">进度</span>
                          <span className="text-sm text-muted-foreground">{task.progress || getProgressFromStatus(task.status)}%</span>
                        </div>
                        <Progress value={task.progress || getProgressFromStatus(task.status)} className="h-2" />
                      </div>
                    )}

                    {/* Error Message */}
                    {task.status === "rejected" && task.admin_comment && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800 break-words">{task.admin_comment}</p>
                      </div>
                    )}

                    {/* Task Details */}
                    <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:gap-4 text-sm text-muted-foreground">
                      <span className="whitespace-nowrap">创建时间: {new Date(task.created_at).toLocaleDateString()}</span>
                      {task.input_params?.language && <span className="whitespace-nowrap">语言: {task.input_params.language}</span>}
                      {task.input_params?.framework && <span className="whitespace-nowrap">框架: {task.input_params.framework}</span>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
