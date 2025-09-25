'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Info, 
  Loader2, 
  Zap,
  Clock,
  TrendingUp,
  Activity,
  Bell,
  X,
  Minimize2,
  Maximize2,
  Volume2,
  VolumeX
} from 'lucide-react'

// 反馈类型定义
type FeedbackType = 'success' | 'error' | 'warning' | 'info' | 'loading'
type FeedbackPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'center'

interface FeedbackMessage {
  id: string
  type: FeedbackType
  title: string
  message: string
  duration?: number // 毫秒，0表示不自动消失
  action?: {
    label: string
    onClick: () => void
  }
  progress?: number // 0-100
  timestamp: Date
  persistent?: boolean // 是否持久显示
}

interface ProgressFeedback {
  id: string
  title: string
  current: number
  total: number
  status: 'running' | 'completed' | 'error' | 'paused'
  details?: string
  estimatedTime?: number // 剩余时间（秒）
  speed?: string // 处理速度
}

interface SystemStatus {
  cpu: number
  memory: number
  network: 'online' | 'offline' | 'slow'
  activeConnections: number
  lastUpdate: Date
}

// 全局反馈状态管理
class FeedbackManager {
  private static instance: FeedbackManager
  private listeners: Set<(messages: FeedbackMessage[]) => void> = new Set()
  private messages: FeedbackMessage[] = []
  private progressTasks: Map<string, ProgressFeedback> = new Map()
  private progressListeners: Set<(tasks: ProgressFeedback[]) => void> = new Set()
  
  static getInstance(): FeedbackManager {
    if (!FeedbackManager.instance) {
      FeedbackManager.instance = new FeedbackManager()
    }
    return FeedbackManager.instance
  }
  
  // 添加反馈消息
  addMessage(message: Omit<FeedbackMessage, 'id' | 'timestamp'>): string {
    const id = Math.random().toString(36).substr(2, 9)
    const newMessage: FeedbackMessage = {
      ...message,
      id,
      timestamp: new Date()
    }
    
    this.messages.unshift(newMessage)
    this.notifyListeners()
    
    // 自动移除消息
    if (message.duration && message.duration > 0) {
      setTimeout(() => {
        this.removeMessage(id)
      }, message.duration)
    }
    
    return id
  }
  
  // 移除消息
  removeMessage(id: string) {
    this.messages = this.messages.filter(msg => msg.id !== id)
    this.notifyListeners()
  }
  
  // 清空所有消息
  clearAll() {
    this.messages = []
    this.notifyListeners()
  }
  
  // 订阅消息变化
  subscribe(listener: (messages: FeedbackMessage[]) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }
  
  // 通知监听器
  private notifyListeners() {
    this.listeners.forEach(listener => listener([...this.messages]))
  }
  
  // 进度任务管理
  addProgressTask(task: ProgressFeedback) {
    this.progressTasks.set(task.id, task)
    this.notifyProgressListeners()
  }
  
  updateProgressTask(id: string, updates: Partial<ProgressFeedback>) {
    const task = this.progressTasks.get(id)
    if (task) {
      this.progressTasks.set(id, { ...task, ...updates })
      this.notifyProgressListeners()
    }
  }
  
  removeProgressTask(id: string) {
    this.progressTasks.delete(id)
    this.notifyProgressListeners()
  }
  
  subscribeProgress(listener: (tasks: ProgressFeedback[]) => void) {
    this.progressListeners.add(listener)
    return () => this.progressListeners.delete(listener)
  }
  
  private notifyProgressListeners() {
    const tasks = Array.from(this.progressTasks.values())
    this.progressListeners.forEach(listener => listener(tasks))
  }
}

// 反馈管理器实例
const feedbackManager = FeedbackManager.getInstance()

// 反馈Hook
export function useFeedback() {
  const showSuccess = useCallback((title: string, message: string, duration = 3000) => {
    return feedbackManager.addMessage({ type: 'success', title, message, duration })
  }, [])
  
  const showError = useCallback((title: string, message: string, duration = 5000) => {
    return feedbackManager.addMessage({ type: 'error', title, message, duration })
  }, [])
  
  const showWarning = useCallback((title: string, message: string, duration = 4000) => {
    return feedbackManager.addMessage({ type: 'warning', title, message, duration })
  }, [])
  
  const showInfo = useCallback((title: string, message: string, duration = 3000) => {
    return feedbackManager.addMessage({ type: 'info', title, message, duration })
  }, [])
  
  const showLoading = useCallback((title: string, message: string) => {
    return feedbackManager.addMessage({ type: 'loading', title, message, duration: 0 })
  }, [])
  
  const showProgress = useCallback((task: ProgressFeedback) => {
    feedbackManager.addProgressTask(task)
  }, [])
  
  const updateProgress = useCallback((id: string, updates: Partial<ProgressFeedback>) => {
    feedbackManager.updateProgressTask(id, updates)
  }, [])
  
  const hideMessage = useCallback((id: string) => {
    feedbackManager.removeMessage(id)
  }, [])
  
  const hideProgress = useCallback((id: string) => {
    feedbackManager.removeProgressTask(id)
  }, [])
  
  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    showProgress,
    updateProgress,
    hideMessage,
    hideProgress
  }
}

// 反馈消息组件
function FeedbackMessage({ message, onClose }: { message: FeedbackMessage; onClose: () => void }) {
  const getIcon = () => {
    switch (message.type) {
      case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error': return <XCircle className="h-5 w-5 text-red-500" />
      case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'info': return <Info className="h-5 w-5 text-blue-500" />
      case 'loading': return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
    }
  }
  
  const getBgColor = () => {
    switch (message.type) {
      case 'success': return 'bg-green-50 border-green-200'
      case 'error': return 'bg-red-50 border-red-200'
      case 'warning': return 'bg-yellow-50 border-yellow-200'
      case 'info': return 'bg-blue-50 border-blue-200'
      case 'loading': return 'bg-blue-50 border-blue-200'
    }
  }
  
  return (
    <Card className={cn("mb-2 animate-in slide-in-from-right-full", getBgColor())}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm">{message.title}</h4>
            <p className="text-sm text-muted-foreground mt-1">{message.message}</p>
            
            {message.progress !== undefined && (
              <div className="mt-2">
                <Progress value={message.progress} className="h-2" />
                <p className="text-xs text-muted-foreground mt-1">{message.progress}% 完成</p>
              </div>
            )}
            
            {message.action && (
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={message.action.onClick}
              >
                {message.action.label}
              </Button>
            )}
          </div>
          
          {!message.persistent && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 flex-shrink-0"
              onClick={onClose}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// 进度任务组件
function ProgressTask({ task }: { task: ProgressFeedback }) {
  const progress = (task.current / task.total) * 100
  
  const getStatusIcon = () => {
    switch (task.status) {
      case 'running': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      case 'paused': return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }
  
  const getStatusColor = () => {
    switch (task.status) {
      case 'running': return 'border-blue-200 bg-blue-50'
      case 'completed': return 'border-green-200 bg-green-50'
      case 'error': return 'border-red-200 bg-red-50'
      case 'paused': return 'border-yellow-200 bg-yellow-50'
    }
  }
  
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`
  }
  
  return (
    <Card className={cn("mb-2", getStatusColor())}>
      <CardContent className="p-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <h4 className="font-medium text-sm">{task.title}</h4>
            </div>
            <Badge variant="outline" className="text-xs">
              {task.current}/{task.total}
            </Badge>
          </div>
          
          <div className="space-y-2">
            <Progress value={progress} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{progress.toFixed(1)}% 完成</span>
              {task.estimatedTime && task.status === 'running' && (
                <span>剩余 {formatTime(task.estimatedTime)}</span>
              )}
            </div>
          </div>
          
          {task.details && (
            <p className="text-xs text-muted-foreground">{task.details}</p>
          )}
          
          {task.speed && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3" />
              <span>{task.speed}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// 系统状态组件
function SystemStatusIndicator({ status }: { status: SystemStatus }) {
  const getNetworkColor = () => {
    switch (status.network) {
      case 'online': return 'text-green-500'
      case 'slow': return 'text-yellow-500'
      case 'offline': return 'text-red-500'
    }
  }
  
  const getNetworkText = () => {
    switch (status.network) {
      case 'online': return '在线'
      case 'slow': return '缓慢'
      case 'offline': return '离线'
    }
  }
  
  return (
    <Card className="mb-2">
      <CardContent className="p-3">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">系统状态</span>
            <div className={cn("flex items-center gap-1 text-xs", getNetworkColor())}>
              <div className="w-2 h-2 rounded-full bg-current" />
              {getNetworkText()}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">CPU</span>
                <span>{status.cpu}%</span>
              </div>
              <Progress value={status.cpu} className="h-1 mt-1" />
            </div>
            
            <div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">内存</span>
                <span>{status.memory}%</span>
              </div>
              <Progress value={status.memory} className="h-1 mt-1" />
            </div>
          </div>
          
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>活跃连接: {status.activeConnections}</span>
            <span>更新: {status.lastUpdate.toLocaleTimeString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// 主反馈容器组件
export function RealTimeFeedback({ 
  position = 'top-right',
  showSystemStatus = true,
  maxMessages = 5
}: {
  position?: FeedbackPosition
  showSystemStatus?: boolean
  maxMessages?: number
}) {
  const [messages, setMessages] = useState<FeedbackMessage[]>([])
  const [progressTasks, setProgressTasks] = useState<ProgressFeedback[]>([])
  const [isMinimized, setIsMinimized] = useState(false)
  const [isHidden, setIsHidden] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    cpu: 45,
    memory: 62,
    network: 'online',
    activeConnections: 3,
    lastUpdate: new Date()
  })
  
  // 订阅反馈消息
  useEffect(() => {
    const unsubscribe = feedbackManager.subscribe(setMessages)
    return () => {
      unsubscribe()
    }
  }, [])
  
  // 订阅进度任务
  useEffect(() => {
    const unsubscribe = feedbackManager.subscribeProgress(setProgressTasks)
    return () => {
      unsubscribe()
    }
  }, [])
  
  // 模拟系统状态更新
  useEffect(() => {
    if (!showSystemStatus) return
    
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        cpu: Math.max(0, Math.min(100, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, prev.memory + (Math.random() - 0.5) * 5)),
        lastUpdate: new Date()
      }))
    }, 5000)
    
    return () => clearInterval(interval)
  }, [showSystemStatus])
  
  // 播放提示音
  const playNotificationSound = useCallback((type: FeedbackType) => {
    if (!soundEnabled) return
    
    // 这里可以添加实际的音频播放逻辑
    // const audio = new Audio(`/sounds/${type}.mp3`)
    // audio.play().catch(() => {})
  }, [soundEnabled])
  
  // 监听新消息并播放提示音
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[0]
      playNotificationSound(latestMessage.type)
    }
  }, [messages, playNotificationSound])
  
  const getPositionClasses = () => {
    switch (position) {
      case 'top-right': return 'top-4 right-4'
      case 'top-left': return 'top-4 left-4'
      case 'bottom-right': return 'bottom-4 right-4'
      case 'bottom-left': return 'bottom-4 left-4'
      case 'center': return 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'
    }
  }
  
  const visibleMessages = messages.slice(0, maxMessages)
  const hasContent = visibleMessages.length > 0 || progressTasks.length > 0 || showSystemStatus
  
  // 如果被隐藏，只显示一个小的重新显示按钮
  if (isHidden) {
    return (
      <div className={cn(
        "fixed z-50",
        getPositionClasses()
      )}>
        <Button
          variant="outline"
          size="sm"
          className="h-8 w-8 p-0 bg-background/95 backdrop-blur-sm"
          onClick={() => setIsHidden(false)}
          title="显示实时反馈"
        >
          <Bell className="h-4 w-4" />
        </Button>
      </div>
    )
  }
  
  if (!hasContent) return null
  
  return (
    <div className={cn(
      "fixed z-50 w-80 max-h-[80vh] overflow-hidden",
      getPositionClasses()
    )}>
      <div className="space-y-2">
        {/* 控制栏 */}
        <div className="flex items-center justify-between bg-background/95 backdrop-blur-sm border rounded-lg p-2">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium">实时反馈</span>
            {(visibleMessages.length > 0 || progressTasks.length > 0) && (
              <Badge variant="secondary" className="text-xs h-5">
                {visibleMessages.length + progressTasks.length}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setSoundEnabled(!soundEnabled)}
            >
              {soundEnabled ? 
                <Volume2 className="h-3 w-3" /> : 
                <VolumeX className="h-3 w-3" />
              }
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setIsMinimized(!isMinimized)}
              title={isMinimized ? "展开" : "最小化"}
            >
              {isMinimized ? 
                <Maximize2 className="h-3 w-3" /> : 
                <Minimize2 className="h-3 w-3" />
              }
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setIsHidden(true)}
              title="隐藏反馈窗口"
            >
              <X className="h-3 w-3" />
            </Button>
            
            {visibleMessages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => feedbackManager.clearAll()}
                title="清除所有消息"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
        
        {/* 内容区域 */}
        {!isMinimized && (
          <div className="space-y-2 max-h-[60vh] overflow-y-auto">
            {/* 系统状态 */}
            {showSystemStatus && (
              <SystemStatusIndicator status={systemStatus} />
            )}
            
            {/* 进度任务 */}
            {progressTasks.map(task => (
              <ProgressTask key={task.id} task={task} />
            ))}
            
            {/* 反馈消息 */}
            {visibleMessages.map(message => (
              <FeedbackMessage
                key={message.id}
                message={message}
                onClose={() => feedbackManager.removeMessage(message.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// 简化的Toast组件
export function FeedbackToast() {
  return <RealTimeFeedback position="top-right" showSystemStatus={false} maxMessages={3} />
}

// 全屏反馈组件
export function FullScreenFeedback() {
  return <RealTimeFeedback position="center" showSystemStatus={true} maxMessages={10} />
}

// 导出反馈管理器供外部使用
export { feedbackManager }