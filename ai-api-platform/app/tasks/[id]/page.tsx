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
  Play,
  FileText,
  Activity,
  Eye,
  MessageSquare,
  Loader2,
} from "lucide-react"
import Link from "next/link"
import { ProtectedRoute, useAuth } from "@/contexts/AuthContext"
import { tasks, admin, Task } from "@/lib/api"
import { getProgressFromStatus, getStatusIcon, getStatusBadgeProps, getStatusText } from '@/lib/task-status'
import { TaskWorkflow } from '@/components/task-workflow'
import { GuidedDeployment } from '@/components/guided-deployment'
import { useToast } from "@/components/ui/use-toast"



function TaskDetailsContent() {
  const params = useParams()
  const { user } = useAuth()
  const { toast } = useToast()
  const [task, setTask] = useState<Task | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
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
      
      // 获取任务日志
      try {
        const logs = await tasks.getLogs(taskId)
        taskData.logs = logs
      } catch (logError) {
        console.warn('Failed to load task logs:', logError)
        // 如果日志加载失败，设置为空数组，不影响主要功能
        taskData.logs = []
      }
      
      setTask(taskData)
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateCode = async () => {
    try {
      setIsGenerating(true)
      await tasks.regenerateCode(taskId)
      
      toast({
        title: "成功",
        description: "代码生成步骤已完成",
      })
      
      // 重新加载任务信息
      await loadTask()
    } catch (error: any) {
      console.error('代码生成失败:', error)
      toast({
        title: "错误",
        description: error.message || "代码生成步骤失败",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }









  // 获取操作类型的中文显示
  const getActionTypeText = (actionType: string) => {
    const actionTypeMap: { [key: string]: string } = {
      'create_task': '创建任务',
      'generate_code': '生成代码',
      'submit_code': '代码提交',
      'admin_review': '管理员审核',
      'deploy': '部署完成',
      'approve': '审核通过',
      'reject': '审核拒绝'
    }
    return actionTypeMap[actionType] || actionType
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
            <TabsTrigger value="logs">操作日志</TabsTrigger>
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
            {/* Generate Code Button */}
            {task.status === 'submitted' && (
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" />
                    代码生成步骤
                  </CardTitle>
                  <CardDescription>点击按钮完成代码生成步骤记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={handleGenerateCode}
                    disabled={isGenerating}
                    className="w-full"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        正在记录步骤...
                      </>
                    ) : (
                      <>
                        <Bot className="h-4 w-4 mr-2" />
                        完成代码生成步骤
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )}
            
            {/* Dify AI Chat Section */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  AI助手聊天
                </CardTitle>
                <CardDescription>与AI助手讨论您的API需求和实现方案</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="w-full h-[600px] border rounded-lg overflow-hidden">
                  <iframe
                    src="https://udify.app/chat/FPrQeaMIhm0OgPiQ"
                    className="w-full h-full border-0"
                    title="Dify AI Chat"
                    allow="microphone; camera"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="space-y-4">
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  操作日志
                </CardTitle>
                <CardDescription>任务的所有操作记录</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {task.logs && task.logs.length > 0 ? task.logs.map((log: any, index: number) => (
                    <div key={index} className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg border">
                      <div className="flex flex-col items-center gap-1">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Activity className="h-4 w-4 text-primary" />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleTimeString('zh-CN', { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </div>
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {log.user_name || '系统'}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {getActionTypeText(log.action_type)}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {log.message}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleDateString('zh-CN')}
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div className="text-center text-muted-foreground py-8">
                      <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>暂无操作记录</p>
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
                    {task.status === 'deployed' ? 
                      'API已生成完成，您可以开始测试。' : 
                      '您的API正在生成中。代码生成完成后将可进行测试。'
                    }
                  </p>
                  <Button disabled={task.status !== 'deployed'}>
                    <Play className="h-4 w-4 mr-2" />
                    {task.status === 'deployed' ? '测试API' : '测试API（即将推出）'}
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
