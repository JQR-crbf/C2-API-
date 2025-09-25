"use client"

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, Terminal as TerminalIcon, X } from 'lucide-react'

interface WebTerminalProps {
  sessionId?: string
  className?: string
  onConnect?: () => void
  onDisconnect?: () => void
}

export function WebTerminal({ 
  sessionId = 'default', 
  className = '',
  onConnect,
  onDisconnect 
}: WebTerminalProps) {
  const { token } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [showCloudShell, setShowCloudShell] = useState(false)



  // 连接CloudShell
  const connectCloudShell = () => {
    if (!token) return

    setIsConnecting(true)
    
    try {
      setShowCloudShell(true)
      setIsConnected(true)
      setIsConnecting(false)
      onConnect?.()
    } catch (error) {
      console.error('Failed to load CloudShell:', error)
      setIsConnecting(false)
    }
  }




  // 断开连接
  const disconnect = () => {
    // 关闭CloudShell
    setShowCloudShell(false)
    setIsConnected(false)
    onDisconnect?.()
  }



  return (
    <div className={`flex flex-col bg-gray-900 text-white rounded-lg overflow-hidden ${className}`} style={{ height: '100%' }}>
      {/* 终端控制栏 */}
      <div className="flex items-center justify-between p-2 bg-gray-100 border-b">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-4 w-4" />
          <span className="text-sm font-medium">CloudShell 终端</span>
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? "已连接" : "未连接"}
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          {!isConnected ? (
            <Button 
              size="sm" 
              onClick={connectCloudShell}
              disabled={isConnecting || !token}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              {isConnecting ? (
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
              ) : (
                <TerminalIcon className="h-3 w-3 mr-1" />
              )}
              {isConnecting ? '连接中...' : '华为云 CloudShell'}
            </Button>
          ) : (
            <Button size="sm" variant="outline" onClick={disconnect}>
              <X className="h-3 w-3 mr-1" />
              断开
            </Button>
          )}
        </div>
      </div>
      
      {/* 终端显示区域 */}
      {showCloudShell && (
        <div className="flex-1 bg-white relative">
          <div className="h-full w-full">
            {/* CloudShell iframe */}
            <iframe
               src="https://console.huaweicloud.com/shell?agencyId=e4b03adc7f9e441ea20a7beb571c8054&region=cn-north-4&locale=zh-cn#/remote?eip=124.70.0.110&az=cn-north-4g&id=f8d2de19-b680-41d5-89fe-fd5d62feb125&name=hcss_ecs_9b31&redirect_url=https:%2F%2Fconsole.huaweicloud.com%2Fsmb%2F%3FagencyId%3De4b03adc7f9e441ea20a7beb571c8054%26region%3Dcn-north-4%26locale%3Dzh-cn%23%2Fresource%2Fplan%2F67ca7657b678a5715a497d55%2Fhecs"
               className="w-full h-full border-0 rounded-lg"
               style={{ minHeight: '450px', height: '100%' }}
               title="华为云 CloudShell"
               allow="clipboard-read; clipboard-write; fullscreen"
               sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
             />
          </div>
        </div>
      )}
    </div>
  )
}

export default WebTerminal