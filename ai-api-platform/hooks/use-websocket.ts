import { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from '@/hooks/use-toast'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

interface UseWebSocketReturn {
  isConnected: boolean
  sendMessage: (message: any) => void
  lastMessage: WebSocketMessage | null
}

export function useWebSocket(): UseWebSocketReturn {
  const { user, token } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const connect = () => {
    if (!token || !user) {
      return
    }

    try {
      const wsUrl = `ws://localhost:8080/ws?token=${token}`
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket连接已建立')
        setIsConnected(true)
        
        // 启动心跳
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000) // 每30秒发送一次心跳
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          handleMessage(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      ws.onclose = (event) => {
      console.log('WebSocket连接已关闭', event.code, event.reason)
        setIsConnected(false)
        
        // 清理心跳
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }
        
        // 如果不是主动关闭，则尝试重连
        if (event.code !== 1000 && token && user) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('尝试重新连接WebSocket...')
            connect()
          }, 5000)
        }
      }

      ws.onerror = (error) => {
      console.error('WebSocket连接错误:', error)
        setIsConnected(false)
      }
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected')
      wsRef.current = null
    }
    
    setIsConnected(false)
  }

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'notification':
        // 显示通知
        const notificationData = message.data
        toast({
          title: notificationData.title,
          description: notificationData.content,
          variant: notificationData.type === 'error' ? 'destructive' : 'default',
        })
        break
        
      case 'task_status_update':
        // 任务状态更新
        const taskData = message.data
        toast({
          title: '任务状态更新',
          description: `任务 "${taskData.title}" 状态已更新: ${taskData.message}`,
        })
        
        // 触发任务列表刷新（通过自定义事件）
        window.dispatchEvent(new CustomEvent('task-status-updated', {
          detail: taskData
        }))
        break
        
      case 'pong':
        // 心跳响应，不需要处理
        break
        
      default:
        console.log('收到未知类型的WebSocket消息:', message)
    }
  }

  useEffect(() => {
    if (token && user) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [token, user])

  return {
    isConnected,
    sendMessage,
    lastMessage,
  }
}