"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  CheckCircle, Clock, AlertCircle, Play, Loader2, Settings, 
  Code, Server, GitBranch, TestTube, Rocket, Eye,
  FileText, Zap, Shield, Monitor, Users, CheckSquare
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useAuth } from "@/contexts/AuthContext"

// 工作流程步骤类型
interface WorkflowStep {
  step_id: number
  step_number: number
  step_name: string
  step_type: string
  status: string
  description?: string
  estimated_duration?: number
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
  actions: WorkflowAction[]
}

// 工作流程操作
interface WorkflowAction {
  action_id: number
  action_name: string
  action_type: string
  status: string
  description?: string
  command?: string
  output?: string
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
}

// 工作流程会话状态
interface WorkflowStatus {
  session_id: number
  status: string
  current_step: number
  total_steps: number
  progress_percentage: number
  created_at: string
  updated_at: string
  steps: WorkflowStep[]
}

// 用户输入表单数据
interface UserInputData {
  [key: string]: any
}

interface EnhancedWorkflowProps {
  taskId: number
  onStatusUpdate?: () => void
}

export function EnhancedWorkflow({ taskId, onStatusUpdate }: EnhancedWorkflowProps) {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isExecuting, setIsExecuting] = useState(false)
  const [userInputData, setUserInputData] = useState<UserInputData>({})
  const [showInputDialog, setShowInputDialog] = useState(false)
  const [currentInputStep, setCurrentInputStep] = useState<WorkflowStep | null>(null)
  const [sessionId, setSessionId] = useState<number | null>(null)
  const { toast } = useToast()
  const { user } = useAuth()

  useEffect(() => {
    initializeWorkflow()
  }, [taskId])

  // 初始化工作流程
  const initializeWorkflow = async () => {
    try {
      setIsLoading(true)
      
      // 首先尝试获取现有的工作流程会话
      const existingSessions = await fetchUserWorkflows()
      const existingSession = existingSessions.find((session: any) => session.task_id === taskId)
      
      if (existingSession) {
        setSessionId(existingSession.session_id)
        await loadWorkflowStatus(existingSession.session_id)
      } else {
        // 创建新的工作流程会话
        await createWorkflowSession()
      }
    } catch (error) {
      console.error('初始化工作流程失败:', error)
      toast({
        title: "错误",
        description: "初始化工作流程失败",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 获取用户的工作流程列表
  const fetchUserWorkflows = async () => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    const response = await fetch(`${API_BASE_URL}/api/workflow/list`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('获取工作流程列表失败')
    }
    
    return await response.json()
  }

  // 创建新的工作流程会话
  const createWorkflowSession = async () => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    const response = await fetch(`${API_BASE_URL}/api/workflow/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        task_id: taskId,
        requirements: {
          api_name: `Task ${taskId} API`,
          description: "AI生成的API项目"
        },
        project_name: `task-${taskId}-project`,
        project_description: "通过AI自动生成的API项目"
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '创建工作流程失败')
    }
    
    const result = await response.json()
    setSessionId(result.session_id)
    await loadWorkflowStatus(result.session_id)
    
    toast({
      title: "成功",
      description: "工作流程创建成功",
    })
  }

  // 加载工作流程状态
  const loadWorkflowStatus = async (sessionId: number) => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    const response = await fetch(`${API_BASE_URL}/api/workflow/status/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('获取工作流程状态失败')
    }
    
    const data = await response.json()
    setWorkflowStatus(data)
  }

  // 执行工作流程步骤
  const executeStep = async (stepNumber: number, userInput?: UserInputData) => {
    if (!sessionId) return
    
    try {
      setIsExecuting(true)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const response = await fetch(`${API_BASE_URL}/api/workflow/execute/${sessionId}/${stepNumber}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          user_input: userInput
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '执行步骤失败')
      }
      
      const result = await response.json()
      
      if (result.success) {
        toast({
          title: "成功",
          description: result.message,
        })
        
        // 重新加载工作流程状态
        await loadWorkflowStatus(sessionId)
        
        // 通知父组件状态已更新
        if (onStatusUpdate) {
          onStatusUpdate()
        }
      } else {
        toast({
          title: "错误",
          description: result.error,
          variant: "destructive",
        })
      }
    } catch (error: any) {
      console.error('执行步骤失败:', error)
      toast({
        title: "错误",
        description: error.message || "执行步骤失败",
        variant: "destructive",
      })
    } finally {
      setIsExecuting(false)
      setShowInputDialog(false)
      setCurrentInputStep(null)
    }
  }

  // 处理需要用户输入的步骤
  const handleStepWithInput = (step: WorkflowStep) => {
    setCurrentInputStep(step)
    setUserInputData({})
    setShowInputDialog(true)
  }

  // 获取步骤图标
  const getStepIcon = (stepType: string) => {
    const iconMap: { [key: string]: any } = {
      'DEMAND_ANALYSIS': FileText,
      'TECH_SELECTION': Settings,
      'SERVER_CONNECTION': Server,
      'ENVIRONMENT_SETUP': Shield,
      'GIT_SETUP': GitBranch,
      'AI_CODE_GENERATION': Code,
      'CODE_REVIEW': Eye,
      'SYNTAX_CHECK': CheckSquare,
      'UNIT_TEST': TestTube,
      'PERFORMANCE_TEST': Zap,
      'GIT_COMMIT': GitBranch,
      'DEPLOYMENT': Rocket,
      'API_TEST': Monitor,
      'USER_ACCEPTANCE': Users,
      'COMPLETION': CheckCircle
    }
    
    const IconComponent = iconMap[stepType] || Clock
    return <IconComponent className="h-4 w-4" />
  }

  // 获取步骤状态颜色
  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'IN_PROGRESS':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'FAILED':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'BLOCKED':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'REQUIRES_INPUT':
        return 'text-purple-600 bg-purple-50 border-purple-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // 获取操作状态徽章
  const getActionStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="default" className="bg-green-100 text-green-800">已完成</Badge>
      case 'IN_PROGRESS':
        return <Badge variant="default" className="bg-blue-100 text-blue-800">进行中</Badge>
      case 'FAILED':
        return <Badge variant="destructive">失败</Badge>
      case 'BLOCKED':
        return <Badge variant="secondary">阻塞</Badge>
      default:
        return <Badge variant="outline">待执行</Badge>
    }
  }

  // 渲染用户输入表单
  const renderUserInputForm = () => {
    if (!currentInputStep) return null
    
    const stepType = currentInputStep.step_type
    
    if (stepType === 'SERVER_CONNECTION') {
      return (
        <div className="space-y-4">
          <div>
            <Label htmlFor="host">服务器地址</Label>
            <Input
              id="host"
              placeholder="例如: 192.168.1.100"
              value={userInputData.host || ''}
              onChange={(e) => setUserInputData(prev => ({ ...prev, host: e.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="port">端口</Label>
            <Input
              id="port"
              type="number"
              placeholder="22"
              value={userInputData.port || 22}
              onChange={(e) => setUserInputData(prev => ({ ...prev, port: parseInt(e.target.value) }))}
            />
          </div>
          <div>
            <Label htmlFor="username">用户名</Label>
            <Input
              id="username"
              placeholder="例如: root"
              value={userInputData.username || ''}
              onChange={(e) => setUserInputData(prev => ({ ...prev, username: e.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="password">密码</Label>
            <Input
              id="password"
              type="password"
              placeholder="服务器密码"
              value={userInputData.password || ''}
              onChange={(e) => setUserInputData(prev => ({ ...prev, password: e.target.value }))}
            />
          </div>
        </div>
      )
    }
    
    if (stepType === 'DEMAND_ANALYSIS') {
      return (
        <div className="space-y-4">
          <div>
            <Label htmlFor="api_name">API名称</Label>
            <Input
              id="api_name"
              placeholder="例如: 用户管理API"
              value={userInputData.api_name || ''}
              onChange={(e) => setUserInputData(prev => ({ ...prev, api_name: e.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="description">功能描述</Label>
            <Textarea
              id="description"
              placeholder="详细描述API的功能和用途..."
              value={userInputData.description || ''}
              onChange={(e) => setUserInputData(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
        </div>
      )
    }
    
    return (
      <div className="space-y-4">
        <div>
          <Label htmlFor="general_input">输入信息</Label>
          <Textarea
            id="general_input"
            placeholder="请输入相关信息..."
            value={userInputData.general_input || ''}
            onChange={(e) => setUserInputData(prev => ({ ...prev, general_input: e.target.value }))}
          />
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            初始化工作流程...
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  if (!workflowStatus) {
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

  const currentStep = workflowStatus.steps.find(step => step.step_number === workflowStatus.current_step)

  return (
    <div className="space-y-6">
      {/* 工作流程概览 */}
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Rocket className="h-5 w-5 text-primary" />
            智能开发工作流程
          </CardTitle>
          <CardDescription>
            15步完整开发流程，从需求分析到部署上线
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                当前进度: 第 {workflowStatus.current_step} 步 / 共 {workflowStatus.total_steps} 步
              </div>
              <Badge variant="outline">
                {workflowStatus.progress_percentage}% 完成
              </Badge>
            </div>
            <Progress value={workflowStatus.progress_percentage} className="w-full" />
          </div>
        </CardContent>
      </Card>

      {/* 步骤详情 */}
      <Card className="border-border">
        <CardHeader>
          <CardTitle>执行步骤</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="current" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="current">当前步骤</TabsTrigger>
              <TabsTrigger value="all">所有步骤</TabsTrigger>
              <TabsTrigger value="actions">操作详情</TabsTrigger>
            </TabsList>
            
            <TabsContent value="current" className="space-y-4">
              {currentStep ? (
                <div className={`p-4 rounded-lg border ${getStepStatusColor(currentStep.status)}`}>
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      {getStepIcon(currentStep.step_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium">{currentStep.step_name}</h3>
                        {getActionStatusBadge(currentStep.status)}
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        {currentStep.description}
                      </p>
                      
                      {/* 执行按钮 */}
                      {currentStep.status === 'PENDING' && (
                        <div className="space-y-2">
                          {currentStep.actions.some(action => action.action_type === 'USER_INPUT') ? (
                            <Button
                              onClick={() => handleStepWithInput(currentStep)}
                              disabled={isExecuting}
                              className="w-full"
                            >
                              {isExecuting ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4 mr-2" />
                              )}
                              开始执行
                            </Button>
                          ) : (
                            <Button
                              onClick={() => executeStep(currentStep.step_number)}
                              disabled={isExecuting}
                              className="w-full"
                            >
                              {isExecuting ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4 mr-2" />
                              )}
                              自动执行
                            </Button>
                          )}
                        </div>
                      )}
                      
                      {/* 错误信息 */}
                      {currentStep.error_message && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                          <p className="text-sm text-red-600">{currentStep.error_message}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  工作流程已完成
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="all" className="space-y-3">
              {workflowStatus.steps.map((step) => (
                <div key={step.step_id} className={`p-3 rounded-lg border ${getStepStatusColor(step.status)}`}>
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                      {getStepIcon(step.step_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">
                          {step.step_number}. {step.step_name}
                        </span>
                        {getActionStatusBadge(step.status)}
                      </div>
                      {step.duration_seconds && (
                        <div className="text-xs text-muted-foreground mt-1">
                          耗时: {step.duration_seconds}秒
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </TabsContent>
            
            <TabsContent value="actions" className="space-y-4">
              {currentStep?.actions.map((action) => (
                <div key={action.action_id} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{action.action_name}</span>
                    {getActionStatusBadge(action.status)}
                  </div>
                  {action.description && (
                    <p className="text-xs text-muted-foreground mb-2">{action.description}</p>
                  )}
                  {action.output && (
                    <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono">
                      {action.output}
                    </div>
                  )}
                  {action.error_message && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
                      {action.error_message}
                    </div>
                  )}
                </div>
              )) || (
                <div className="text-center py-4 text-muted-foreground text-sm">
                  当前步骤暂无操作详情
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* 用户输入对话框 */}
      <Dialog open={showInputDialog} onOpenChange={setShowInputDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>步骤输入</DialogTitle>
            <DialogDescription>
              {currentInputStep?.step_name} - 请提供必要的信息
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {renderUserInputForm()}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowInputDialog(false)}>
              取消
            </Button>
            <Button 
              onClick={() => currentInputStep && executeStep(currentInputStep.step_number, { 
                server_info: userInputData,
                ...userInputData 
              })}
              disabled={isExecuting}
            >
              {isExecuting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              执行
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}