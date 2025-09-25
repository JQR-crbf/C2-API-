"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CheckCircle, Clock, AlertCircle, Play, Loader2, Zap } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useAuth } from "@/contexts/AuthContext"
import { EnhancedWorkflow } from "./enhanced-workflow"

interface WorkflowStep {
  index: number
  status: string
  name: string
  description: string
  auto: boolean
  required_actions: string[]
  completed: boolean
  current: boolean
  can_advance?: boolean
}

interface WorkflowInfo {
  current_step_index: number
  current_step: any
  total_steps: number
  progress_percentage: number
  completed_steps: WorkflowStep[]
  pending_steps: WorkflowStep[]
  all_steps: WorkflowStep[]
}

interface LegacyWorkflowStep {
  step_id: number
  step_name: string
  name: string
  status: string
  auto_status: string
  description?: string
  estimated_duration?: number
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
  completed: boolean
  current: boolean
  auto: boolean
  can_advance: boolean
  required_actions: string[]
}

interface LegacyWorkflowInfo {
  workflow_id: number
  status: string
  current_step: number
  total_steps: number
  progress_percentage: number
  created_at: string
  updated_at: string
  steps: LegacyWorkflowStep[]
  all_steps: LegacyWorkflowStep[]
}

interface TaskWorkflowProps {
  taskId: number
  onStatusUpdate?: () => void
}

function LegacyWorkflow({ taskId, onStatusUpdate }: TaskWorkflowProps) {
  const [workflowInfo, setWorkflowInfo] = useState<LegacyWorkflowInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAdvancing, setIsAdvancing] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const { toast } = useToast()
  const { user } = useAuth()

  useEffect(() => {
    loadWorkflow()
  }, [taskId])

  const loadWorkflow = async () => {
    try {
      setIsLoading(true)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/workflow`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('获取工作流程信息失败')
      }
      
      const data = await response.json()
      setWorkflowInfo(data.workflow)
    } catch (error) {
      console.error('加载工作流程失败:', error)
      toast({
        title: "错误",
        description: "加载工作流程信息失败",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const advanceToNextStep = async () => {
    try {
      setIsAdvancing(true)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/advance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '推进步骤失败')
      }
      
      const result = await response.json()
      toast({
        title: "成功",
        description: result.message,
      })
      
      // 重新加载工作流程信息
      await loadWorkflow()
      
      // 通知父组件状态已更新
      if (onStatusUpdate) {
        onStatusUpdate()
      }
    } catch (error: any) {
      console.error('推进步骤失败:', error)
      toast({
        title: "错误",
        description: error.message || "推进步骤失败",
        variant: "destructive",
      })
    } finally {
      setIsAdvancing(false)
    }
  }

  const markActionCompleted = async (action: string, stepName: string) => {
    try {
      setActionLoading(action)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/actions/${action}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          message: `用户手动完成了 ${stepName} 步骤的 ${action} 操作`
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '标记操作完成失败')
      }
      
      const result = await response.json()
      toast({
        title: "成功",
        description: result.message,
      })
      
      // 重新加载工作流程信息
      await loadWorkflow()
    } catch (error: any) {
      console.error('标记操作完成失败:', error)
      toast({
        title: "错误",
        description: error.message || "标记操作完成失败",
        variant: "destructive",
      })
    } finally {
      setActionLoading(null)
    }
  }

  const getActionButtonText = (action: string) => {
    const actionMap: { [key: string]: string } = {
      'pull_code': '拉取代码',
      'create_branch': '创建分支',
      'generate_code': '生成代码',
      'run_tests': '运行测试',
      'confirm_tests': '确认测试',
      'push_code': '推送代码',
      'admin_approve': '管理员审批',
      'deploy': '部署'
    }
    return actionMap[action] || action
  }

  if (isLoading) {
    return (
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            加载工作流程信息...
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  if (!workflowInfo) {
    return (
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            无法加载工作流程信息
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-primary" />
          任务执行步骤
        </CardTitle>
        <CardDescription>
          按顺序完成每个步骤，确保任务正确执行
        </CardDescription>
        <div className="flex items-center gap-4 mt-2">
          <div className="text-sm text-muted-foreground">
            进度: {workflowInfo.current_step + 1} / {workflowInfo.total_steps}
          </div>
          <Badge variant="outline">
            {workflowInfo.progress_percentage}% 完成
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {workflowInfo.all_steps.map((step: LegacyWorkflowStep, index: number) => {
            const isCompleted = step.completed && !step.current
            const isCurrent = step.current
            const isUpcoming = !step.completed && !step.current
            
            return (
              <div key={step.status} className={`flex items-start gap-4 p-4 rounded-lg border ${
                isCurrent ? 'border-primary bg-primary/5' : 
                isCompleted ? 'border-green-200 bg-green-50' : 
                'border-gray-200 bg-gray-50'
              }`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  isCompleted ? 'bg-green-500 text-white' :
                  isCurrent ? 'bg-primary text-primary-foreground' :
                  'bg-gray-300 text-gray-600'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : isCurrent ? (
                    <Clock className="h-4 w-4" />
                  ) : (
                    <span className="text-xs font-medium">{index + 1}</span>
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className={`font-medium ${
                      isCurrent ? 'text-primary' :
                      isCompleted ? 'text-green-700' :
                      'text-gray-600'
                    }`}>
                      {step.name}
                    </h4>
                    {step.auto && (
                      <Badge variant="secondary" className="text-xs">
                        自动
                      </Badge>
                    )}
                  </div>
                  <p className={`text-sm mt-1 ${
                    isCurrent ? 'text-primary/80' :
                    isCompleted ? 'text-green-600' :
                    'text-gray-500'
                  }`}>
                    {step.description}
                  </p>
                  
                  {/* 当前步骤的操作按钮 */}
                  {isCurrent && !step.auto && step.required_actions.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs text-muted-foreground">
                        需要完成的操作:
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {step.required_actions.map((action: string) => (
                          <Button
                            key={action}
                            size="sm"
                            variant="outline"
                            onClick={() => markActionCompleted(action, step.name)}
                            disabled={actionLoading === action}
                            className="text-xs"
                          >
                            {actionLoading === action ? (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Play className="h-3 w-3 mr-1" />
                            )}
                            {getActionButtonText(action)}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* 推进到下一步的按钮 */}
                  {isCurrent && step.completed && step.can_advance && (
                    <div className="mt-3">
                      <Button
                        size="sm"
                        onClick={advanceToNextStep}
                        disabled={isAdvancing}
                        className="text-xs"
                      >
                        {isAdvancing ? (
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        ) : (
                          <Play className="h-3 w-3 mr-1" />
                        )}
                        进入下一步
                      </Button>
                    </div>
                  )}
                  
                  {/* 当前步骤状态指示 */}
                  {isCurrent && (
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                        <span className="text-xs text-primary font-medium">
                          {step.completed ? '已完成，可进入下一步' : '进行中'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

export function TaskWorkflow({ taskId, onStatusUpdate }: TaskWorkflowProps) {
  return (
    <Tabs defaultValue="enhanced" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="enhanced" className="flex items-center gap-2">
          <Zap className="h-4 w-4" />
          增强版工作流
        </TabsTrigger>
        <TabsTrigger value="legacy" className="flex items-center gap-2">
          <Play className="h-4 w-4" />
          传统工作流
        </TabsTrigger>
      </TabsList>
      <TabsContent value="enhanced">
        <EnhancedWorkflow taskId={taskId} onStatusUpdate={onStatusUpdate} />
      </TabsContent>
      <TabsContent value="legacy">
        <LegacyWorkflow taskId={taskId} onStatusUpdate={onStatusUpdate} />
      </TabsContent>
    </Tabs>
  )
}