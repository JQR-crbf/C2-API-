"use client"

import type React from "react"
import { useEffect } from "react"
import { useWebSocket } from "@/hooks/use-websocket"
import { useAuth } from "@/contexts/AuthContext"

// WebSocket连接组件
export default function ClientProviders({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const { isConnected } = useWebSocket()

  useEffect(() => {
    if (user && isConnected) {
      console.log('WebSocket已连接，实时通知功能已启用')
    }
  }, [user, isConnected])

  return <>{children}</>
}