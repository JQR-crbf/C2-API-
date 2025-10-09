"use client"

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

import { Loader2, X, Terminal } from 'lucide-react'

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
  const [isConnecting, setIsConnecting] = useState(false)




  // 连接CloudShell（直接在新标签页打开）
  const connectCloudShell = () => {
    if (!token) return

    setIsConnecting(true)
    
    try {
      // 华为云CloudShell不支持iframe嵌入，直接在新标签页打开
      const url = generateCloudShellUrl()
      window.open(url, '_blank', 'noopener,noreferrer')
      
      setIsConnecting(false)
      onConnect?.()
    } catch (error) {
      console.error('Failed to open CloudShell:', error)
      setIsConnecting(false)
    }
  }

  // 生成CloudShell URL
  const generateCloudShellUrl = () => {
    // 使用用户提供的完整CloudShell链接作为基础
    // 这个链接包含了必要的id和所有认证参数
    const userProvidedUrl = 'https://console.huaweicloud.com/shell?agencyId=e4b03adc7f9e441ea20a7beb571c8054&region=cn-north-4&locale=zh-cn#/remote?eip=124.70.0.110&az=cn-north-4g&id=f8d2de19-b680-41d5-89fe-fd5d62feb125&name=hcss_ecs_9b31&redirect_url=https:%2F%2Fconsole.huaweicloud.com%2Fsmb%2F%3FagencyId%3De4b03adc7f9e441ea20a7beb571c8054%26region%3Dcn-north-4%26locale%3Dzh-cn%23%2Fresource%2Fplan%2F67ca7657b678a5715a497d55%2Fhecs'
    
    // 直接使用用户提供的完整URL
    return userProvidedUrl
  }










  return (
    <div className={`${className}`}>
      {/* 控制按钮区域 */}
      <div className="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">华为云 CloudShell</span>
          <Badge variant="secondary" className="text-xs">
            新标签页打开
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            size="sm" 
            onClick={connectCloudShell}
            disabled={isConnecting || !token}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            {isConnecting ? (
              <Loader2 className="h-3 w-3 animate-spin mr-1" />
            ) : (
              <Terminal className="h-3 w-3 mr-1" />
            )}
            {isConnecting ? '连接中...' : '打开 CloudShell'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default WebTerminal