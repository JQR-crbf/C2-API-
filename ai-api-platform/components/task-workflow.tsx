"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { CheckCircle, Clock, AlertCircle, Play, Loader2, ThumbsUp, ThumbsDown } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useAuth } from "@/contexts/AuthContext"
import { admin } from "@/lib/api"
import { useState as useReactState } from "react"

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
  const [reviewLoading, setReviewLoading] = useReactState<string | null>(null)
  const [showRejectDialog, setShowRejectDialog] = useReactState(false)
  const [rejectComment, setRejectComment] = useReactState('')
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
      'submit_task': '提交任务',
      'generate_code': '代码生成步骤',
      'submit_code': '提交代码',
      'admin_review': '管理员审核',
      'deploy': '部署完成'
    }
    return actionMap[action] || action
  }

  // 管理员审核处理函数
  const handleAdminReview = async (action: 'approve' | 'reject', comment?: string) => {
    try {
      setReviewLoading(action)
      await admin.reviewTask(taskId.toString(), action, comment)
      
      toast({
        title: "成功",
        description: action === 'approve' ? '任务审核通过' : '任务已拒绝',
      })
      
      // 重新加载工作流程信息
      await loadWorkflow()
      
      // 通知父组件状态已更新
      if (onStatusUpdate) {
        onStatusUpdate()
      }
      
      // 关闭拒绝对话框
      if (action === 'reject') {
        setShowRejectDialog(false)
        setRejectComment('')
      }
    } catch (error: any) {
      console.error('审核操作失败:', error)
      toast({
        title: "错误",
        description: error.message || "审核操作失败",
        variant: "destructive",
      })
    } finally {
      setReviewLoading(null)
    }
  }

  const handleRejectClick = () => {
    setShowRejectDialog(true)
  }

  const handleRejectConfirm = () => {
    if (!rejectComment.trim()) {
      toast({
        title: "错误",
        description: "请输入拒绝理由",
        variant: "destructive",
      })
      return
    }
    handleAdminReview('reject', rejectComment)
  }

  // 获取步骤的中文显示名称
  const getStepDisplayName = (stepName: string, status: string) => {
    const stepNameMap: { [key: string]: string } = {
      'submitted': '任务提交',
      'ai_generating': '代码生成步骤',
      'test_ready': '代码生成步骤',
      'code_submitted': '代码提交',
      'under_review': '管理员审核',
      'deployed': '部署完成',
      'approved': '审核通过',
      'rejected': '审核拒绝'
    }
    return stepNameMap[status] || stepNameMap[stepName] || stepName
  }

  // 获取步骤的描述
  const getStepDescription = (status: string) => {
    const descriptionMap: { [key: string]: string } = {
      'submitted': '用户已提交API开发需求',
      'ai_generating': 'AI正在分析需求并生成代码',
      'code_submitted': '代码已生成并提交到代码库',
      'under_review': '等待管理员审核代码质量',
      'deployed': '代码已部署到生产环境',
      'approved': '管理员审核通过',
      'rejected': '管理员审核未通过，需要修改'
    }
    return descriptionMap[status] || '步骤进行中'
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
    <>
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
                      {getStepDisplayName(step.name, step.status)}
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
                    {step.description || getStepDescription(step.status)}
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
                  
                  {/* 管理员审核按钮 */}
                  {isCurrent && step.status === 'under_review' && user?.role === 'admin' && (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs text-muted-foreground">
                        管理员审核操作:
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="default"
                          onClick={() => handleAdminReview('approve')}
                          disabled={reviewLoading !== null}
                          className="text-xs bg-green-600 hover:bg-green-700"
                        >
                          {reviewLoading === 'approve' ? (
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          ) : (
                            <ThumbsUp className="h-3 w-3 mr-1" />
                          )}
                          通过
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={handleRejectClick}
                          disabled={reviewLoading !== null}
                          className="text-xs"
                        >
                          {reviewLoading === 'reject' ? (
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          ) : (
                            <ThumbsDown className="h-3 w-3 mr-1" />
                          )}
                          拒绝
                        </Button>
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
                          {step.completed ? 
                            (step.can_advance ? '已完成，可进入下一步' : '已完成') : 
                            '进行中'
                          }
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
    
    {/* 拒绝对话框 */}
    <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>拒绝任务</DialogTitle>
          <DialogDescription>
            请输入拒绝理由，任务将回到代码生成步骤。
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="reject-comment">拒绝理由</Label>
            <Textarea
              id="reject-comment"
              placeholder="请输入拒绝理由..."
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              className="mt-1"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setShowRejectDialog(false)}
            disabled={reviewLoading === 'reject'}
          >
            取消
          </Button>
          <Button
            variant="destructive"
            onClick={handleRejectConfirm}
            disabled={reviewLoading === 'reject' || !rejectComment.trim()}
          >
            {reviewLoading === 'reject' ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : null}
            确认拒绝
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  )
}

export function TaskWorkflow({ taskId, onStatusUpdate }: TaskWorkflowProps) {
  return <LegacyWorkflow taskId={taskId} onStatusUpdate={onStatusUpdate} />
}