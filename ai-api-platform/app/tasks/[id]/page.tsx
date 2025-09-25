"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Bot,
  ArrowLeft,
  CheckCircle,
  Clock,
  AlertCircle,
  Download,
  Play,
  Code,
  FileText,
  Activity,
  Eye,
} from "lucide-react"
import Link from "next/link"
import { ProtectedRoute, useAuth } from "@/contexts/AuthContext"
import { tasks, admin, Task } from "@/lib/api"
import { getProgressFromStatus, getStatusIcon, getStatusBadgeProps, getStatusText } from '@/lib/task-status'
import { TaskWorkflow } from '@/components/task-workflow'
import { GuidedDeployment } from '@/components/guided-deployment'



function TaskDetailsContent() {
  const params = useParams()
  const { user } = useAuth()
  const [task, setTask] = useState<Task | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDownloading, setIsDownloading] = useState(false)
  const taskId = params.id as string

  useEffect(() => {
    if (taskId && user) {
      loadTask()
    }
  }, [taskId, user])

  const loadTask = async () => {
    try {
      setIsLoading(true)
      let taskData
      // 根据用户角色调用不同的API
      if (user?.role === 'admin') {
        taskData = await admin.getTask(taskId)
      } else {
        taskData = await tasks.getById(taskId)
      }
      setTask(taskData)
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!task) return
    
    try {
      setIsDownloading(true)
      // 模拟下载功能
      const blob = new Blob([task.generated_code || ''], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `${(task.name || task.title).replace(/\s+/g, '_')}_code.py`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
    } finally {
      setIsDownloading(false)
    }
  }







  const getLogLevelColor = (level: string) => {
    switch (level) {
      case "success":
        return "text-green-600"
      case "error":
        return "text-red-600"
      case "warning":
        return "text-yellow-600"
      default:
        return "text-blue-600"
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载任务详情中...</p>
        </div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground mb-4">任务未找到</h1>
          <p className="text-muted-foreground mb-6">请检查任务ID是否正确</p>
          <Link href="/dashboard">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回仪表板
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">任务详情</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Eye className="h-4 w-4 mr-2" />
              测试API
            </Button>
            <Button 
                variant="outline" 
                size="sm" 
                onClick={handleDownload}
                disabled={isDownloading || !task?.generated_code}
              >
                <Download className="h-4 w-4 mr-2" />
                {isDownloading ? '下载中...' : '下载代码'}
              </Button>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-6xl mx-auto space-y-6">
        {/* Task Header */}
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">{task.name || task.title}</h1>
              <p className="text-muted-foreground mt-1">{task.description}</p>
            </div>
            <Badge {...getStatusBadgeProps(task.status)} />
          </div>

          {/* Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">总体进度</span>
              <span className="text-sm text-muted-foreground">{getProgressFromStatus(task.status)}%</span>
            </div>
            <Progress value={getProgressFromStatus(task.status)} className="h-3" />
            <p className="text-sm text-muted-foreground">状态: {getStatusText(task.status)}</p>
          </div>

          {/* Task Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">创建时间:</span>
              <p className="font-medium text-foreground">{new Date(task.created_at).toLocaleDateString('zh-CN')}</p>
            </div>
            <div>
              <span className="text-muted-foreground">编程语言:</span>
              <p className="font-medium text-foreground">{task.language || 'Python'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">框架:</span>
              <p className="font-medium text-foreground">{task.framework || 'FastAPI'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">数据库:</span>
              <p className="font-medium text-foreground">{task.database || 'PostgreSQL'}</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="progress" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="progress">进度</TabsTrigger>
            <TabsTrigger value="code">生成代码</TabsTrigger>
            <TabsTrigger value="logs">执行日志</TabsTrigger>
            <TabsTrigger value="testing">测试</TabsTrigger>
            <TabsTrigger value="deployment">引导部署</TabsTrigger>
          </TabsList>

          <TabsContent value="progress" className="space-y-4">
            <TaskWorkflow 
              taskId={parseInt(taskId)} 
              onStatusUpdate={loadTask}
            />
          </TabsContent>

          <TabsContent value="code" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5 text-primary" />
                  生成的代码
                </CardTitle>
                <CardDescription>AI为您的API生成的代码（预览）</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm text-gray-100">
                    <code>{task.generated_code || '代码生成中...'}</code>
                  </pre>
                </div>
                <div className="flex justify-end mt-4">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleDownload}
                    disabled={isDownloading || !task.generated_code}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {isDownloading ? '下载中...' : '下载完整代码'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  执行日志
                </CardTitle>
                <CardDescription>API生成过程的实时日志</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {task.logs && task.logs.length > 0 ? task.logs.map((log: any, index: number) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                      <div className="text-xs text-muted-foreground mt-1 min-w-[80px]">
                        {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                      </div>
                      <div className={`text-xs font-medium uppercase min-w-[60px] ${getLogLevelColor(log.level)}`}>
                        {log.level}
                      </div>
                      <div className="text-sm text-foreground flex-1">{log.message}</div>
                    </div>
                  )) : (
                    <div className="text-center text-muted-foreground py-8">
                      暂无日志记录
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="testing" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5 text-primary" />
                  API测试
                </CardTitle>
                <CardDescription>测试您生成的API端点</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-muted-foreground mb-4">
                    {task.status === 'completed' ? 
                      'API已生成完成，您可以开始测试。' : 
                      '您的API正在生成中。代码生成完成后将可进行测试。'
                    }
                  </p>
                  <Button disabled={task.status !== 'completed'}>
                    <Play className="h-4 w-4 mr-2" />
                    {task.status === 'completed' ? '测试API' : '测试API（即将推出）'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deployment" className="space-y-4">
            <GuidedDeployment 
              taskId={parseInt(taskId)}
              taskTitle={task.title}
              generatedCode={task.generated_code || ''}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default function TaskDetailPage() {
  return (
    <ProtectedRoute>
      <TaskDetailsContent />
    </ProtectedRoute>
  )
}
