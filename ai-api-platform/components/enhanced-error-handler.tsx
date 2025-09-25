'use client'

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { 
  AlertCircle, 
  CheckCircle, 
  Info, 
  AlertTriangle, 
  RefreshCw, 
  HelpCircle,
  Loader2,
  X,
  Copy,
  ExternalLink
} from 'lucide-react'
import { cn } from '@/lib/utils'

// 错误类型定义
export interface AppError {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  title: string
  message: string
  details?: string
  code?: string
  timestamp: Date
  retryable?: boolean
  helpUrl?: string
  context?: Record<string, any>
}

// 加载状态类型
export interface LoadingState {
  id: string
  message: string
  progress?: number
  cancelable?: boolean
}

// 错误处理上下文
interface ErrorContextType {
  errors: AppError[]
  loadingStates: LoadingState[]
  addError: (error: Omit<AppError, 'id' | 'timestamp'>) => void
  removeError: (id: string) => void
  clearErrors: () => void
  addLoading: (loading: Omit<LoadingState, 'id'>) => string
  updateLoading: (id: string, updates: Partial<LoadingState>) => void
  removeLoading: (id: string) => void
  showSuccess: (message: string, title?: string) => void
  showWarning: (message: string, title?: string) => void
  showInfo: (message: string, title?: string) => void
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined)

// 错误处理Provider
export function ErrorProvider({ children }: { children: ReactNode }) {
  const [errors, setErrors] = useState<AppError[]>([])
  const [loadingStates, setLoadingStates] = useState<LoadingState[]>([])
  const { toast } = useToast()

  const addError = useCallback((error: Omit<AppError, 'id' | 'timestamp'>) => {
    const newError: AppError = {
      ...error,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date()
    }
    setErrors(prev => [...prev, newError])
    
    // 同时显示toast通知
    toast({
      title: error.title,
      description: error.message,
      variant: error.type === 'error' ? 'destructive' : 'default'
    })
  }, [toast])

  const removeError = useCallback((id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id))
  }, [])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  const addLoading = useCallback((loading: Omit<LoadingState, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newLoading: LoadingState = { ...loading, id }
    setLoadingStates(prev => [...prev, newLoading])
    return id
  }, [])

  const updateLoading = useCallback((id: string, updates: Partial<LoadingState>) => {
    setLoadingStates(prev => 
      prev.map(loading => 
        loading.id === id ? { ...loading, ...updates } : loading
      )
    )
  }, [])

  const removeLoading = useCallback((id: string) => {
    setLoadingStates(prev => prev.filter(loading => loading.id !== id))
  }, [])

  const showSuccess = useCallback((message: string, title = '成功') => {
    addError({ type: 'success', title, message })
  }, [addError])

  const showWarning = useCallback((message: string, title = '警告') => {
    addError({ type: 'warning', title, message })
  }, [addError])

  const showInfo = useCallback((message: string, title = '信息') => {
    addError({ type: 'info', title, message })
  }, [addError])

  return (
    <ErrorContext.Provider value={{
      errors,
      loadingStates,
      addError,
      removeError,
      clearErrors,
      addLoading,
      updateLoading,
      removeLoading,
      showSuccess,
      showWarning,
      showInfo
    }}>
      {children}
    </ErrorContext.Provider>
  )
}

// 使用错误处理的Hook
export function useErrorHandler() {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useErrorHandler must be used within an ErrorProvider')
  }
  return context
}

// 错误图标组件
function ErrorIcon({ type, className }: { type: AppError['type'], className?: string }) {
  const iconProps = { className: cn('h-4 w-4', className) }
  
  switch (type) {
    case 'error':
      return <AlertCircle {...iconProps} className={cn(iconProps.className, 'text-destructive')} />
    case 'warning':
      return <AlertTriangle {...iconProps} className={cn(iconProps.className, 'text-yellow-500')} />
    case 'success':
      return <CheckCircle {...iconProps} className={cn(iconProps.className, 'text-green-500')} />
    case 'info':
    default:
      return <Info {...iconProps} className={cn(iconProps.className, 'text-blue-500')} />
  }
}

// 错误详情组件
function ErrorDetails({ error, onRetry }: { error: AppError, onRetry?: () => void }) {
  const [showDetails, setShowDetails] = useState(false)
  const { removeError } = useErrorHandler()

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const errorDetails = {
    错误ID: error.id,
    错误代码: error.code || '未知',
    发生时间: error.timestamp.toLocaleString(),
    错误类型: error.type,
    上下文: error.context ? JSON.stringify(error.context, null, 2) : '无'
  }

  return (
    <Alert className={cn(
      'mb-4',
      error.type === 'error' && 'border-destructive',
      error.type === 'warning' && 'border-yellow-500',
      error.type === 'success' && 'border-green-500',
      error.type === 'info' && 'border-blue-500'
    )}>
      <ErrorIcon type={error.type} />
      <div className="flex-1">
        <AlertTitle className="flex items-center justify-between">
          <span>{error.title}</span>
          <div className="flex items-center gap-2">
            {error.retryable && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="h-6 px-2"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                重试
              </Button>
            )}
            {error.helpUrl && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(error.helpUrl, '_blank')}
                className="h-6 px-2"
              >
                <HelpCircle className="h-3 w-3 mr-1" />
                帮助
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeError(error.id)}
              className="h-6 w-6 p-0"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </AlertTitle>
        <AlertDescription className="mt-2">
          <p>{error.message}</p>
          
          {error.details && (
            <div className="mt-2">
              <Button
                variant="link"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
                className="p-0 h-auto text-xs"
              >
                {showDetails ? '隐藏详情' : '显示详情'}
              </Button>
              
              {showDetails && (
                <div className="mt-2 p-3 bg-muted rounded-md text-xs font-mono">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">错误详情</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(JSON.stringify(errorDetails, null, 2))}
                      className="h-6 w-6 p-0"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  <pre className="whitespace-pre-wrap">{error.details}</pre>
                  
                  <Separator className="my-2" />
                  
                  <div className="space-y-1">
                    {Object.entries(errorDetails).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground">{key}:</span>
                        <span className="text-right max-w-[200px] truncate">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </AlertDescription>
      </div>
    </Alert>
  )
}

// 加载状态组件
function LoadingIndicator({ loading, onCancel }: { loading: LoadingState, onCancel?: () => void }) {
  return (
    <Card className="mb-4">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm font-medium">{loading.message}</span>
          </div>
          {loading.cancelable && onCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              className="h-6 px-2"
            >
              取消
            </Button>
          )}
        </div>
        {loading.progress !== undefined && (
          <div className="space-y-1">
            <Progress value={loading.progress} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>进度</span>
              <span>{loading.progress}%</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// 错误边界组件
export class ErrorBoundary extends React.Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Card className="m-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              应用程序错误
            </CardTitle>
            <CardDescription>
              应用程序遇到了意外错误。请刷新页面重试，如果问题持续存在，请联系技术支持。
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button
                onClick={() => window.location.reload()}
                className="w-full"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                刷新页面
              </Button>
              
              {this.state.error && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-muted-foreground mb-2">
                    技术详情
                  </summary>
                  <pre className="bg-muted p-2 rounded text-xs overflow-auto">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}

// 主要的错误显示组件
export function ErrorDisplay({ onRetry }: { onRetry?: (errorId: string) => void }) {
  const { errors, loadingStates, removeLoading } = useErrorHandler()

  if (errors.length === 0 && loadingStates.length === 0) {
    return null
  }

  return (
    <div className="space-y-4">
      {/* 显示加载状态 */}
      {loadingStates.map(loading => (
        <LoadingIndicator
          key={loading.id}
          loading={loading}
          onCancel={loading.cancelable ? () => removeLoading(loading.id) : undefined}
        />
      ))}
      
      {/* 显示错误信息 */}
      {errors.map(error => (
        <ErrorDetails
          key={error.id}
          error={error}
          onRetry={error.retryable && onRetry ? () => onRetry(error.id) : undefined}
        />
      ))}
    </div>
  )
}

// 便捷的错误处理Hook
export function useAsyncOperation() {
  const { addError, addLoading, updateLoading, removeLoading, showSuccess } = useErrorHandler()

  const execute = useCallback(
    async (
      operation: () => Promise<any>,
      options: {
        loadingMessage?: string
        successMessage?: string
        errorTitle?: string
        retryable?: boolean
      } = {}
    ): Promise<any> => {
      const loadingId = addLoading({
        message: options.loadingMessage || '处理中...',
        progress: 0
      })

      try {
        updateLoading(loadingId, { progress: 25 })
        const result = await operation()
        updateLoading(loadingId, { progress: 100 })
        
        setTimeout(() => removeLoading(loadingId), 500)
        
        if (options.successMessage) {
          showSuccess(options.successMessage)
        }
        
        return result
      } catch (error) {
        removeLoading(loadingId)
        
        addError({
          type: 'error',
          title: options.errorTitle || '操作失败',
          message: error instanceof Error ? error.message : '未知错误',
          details: error instanceof Error ? error.stack : undefined,
          retryable: options.retryable || false
        })
        
        return null
      }
    },
    [addError, addLoading, updateLoading, removeLoading, showSuccess]
  )

  return { execute }
}