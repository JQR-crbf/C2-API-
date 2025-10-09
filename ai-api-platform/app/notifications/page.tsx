"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { notifications, Notification as ApiNotification } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Bell,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Info,
  Trash2,
  Check,
  CheckCheck
} from "lucide-react"
import Link from "next/link"
import { ProtectedRoute } from "@/contexts/AuthContext"

type Notification = ApiNotification

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success':
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case 'warning':
      return <AlertCircle className="h-4 w-4 text-yellow-600" />
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-600" />
    default:
      return <Info className="h-4 w-4 text-blue-600" />
  }
}

const getNotificationBadge = (type: string) => {
  switch (type) {
    case 'success':
      return <Badge variant="outline" className="text-green-600 border-green-600">成功</Badge>
    case 'warning':
      return <Badge variant="outline" className="text-yellow-600 border-yellow-600">警告</Badge>
    case 'error':
      return <Badge variant="outline" className="text-red-600 border-red-600">错误</Badge>
    default:
      return <Badge variant="outline" className="text-blue-600 border-blue-600">信息</Badge>
  }
}

export default function NotificationsPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [allNotifications, setAllNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("all")

  useEffect(() => {
    loadNotifications()
  }, [])

  const loadNotifications = async () => {
    try {
      setLoading(true)
      const data = await notifications.getAll()
      setAllNotifications(data)
    } catch (error) {
      console.error('加载通知失败:', error)
      toast({
        title: "错误",
        description: "加载通知失败，请稍后重试",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await notifications.markAsRead(notificationId.toString())
      setAllNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      )
      toast({
        title: "成功",
        description: "通知已标记为已读",
      })
    } catch (error) {
      console.error('标记通知失败:', error)
      toast({
        title: "错误",
        description: "标记通知失败，请稍后重试",
        variant: "destructive",
      })
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notifications.markAllAsRead()
      setAllNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      )
      toast({
        title: "成功",
        description: "所有通知已标记为已读",
      })
    } catch (error) {
      console.error('标记所有通知失败:', error)
      toast({
        title: "错误",
        description: "标记所有通知失败，请稍后重试",
        variant: "destructive",
      })
    }
  }

  const handleDeleteNotification = async (notificationId: number) => {
    try {
      await notifications.delete(notificationId.toString())
      setAllNotifications(prev => 
        prev.filter(n => n.id !== notificationId)
      )
      toast({
        title: "成功",
        description: "通知已删除",
      })
    } catch (error) {
      console.error('删除通知失败:', error)
      toast({
        title: "错误",
        description: "删除通知失败，请稍后重试",
        variant: "destructive",
      })
    }
  }

  const filteredNotifications = allNotifications.filter(notification => {
    if (activeTab === "unread") {
      return !notification.is_read
    }
    return true
  })

  const unreadCount = allNotifications.filter(n => !n.is_read).length

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">加载通知中...</p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回首页
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
                <Bell className="h-8 w-8" />
                通知中心
              </h1>
              <p className="text-muted-foreground mt-1">
                查看和管理您的所有通知
              </p>
            </div>
          </div>
          
          {unreadCount > 0 && (
            <Button onClick={handleMarkAllAsRead} variant="outline">
              <CheckCheck className="h-4 w-4 mr-2" />
              全部标记为已读
            </Button>
          )}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="all">
              全部通知 ({allNotifications.length})
            </TabsTrigger>
            <TabsTrigger value="unread">
              未读通知 ({unreadCount})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-6">
            <NotificationList 
              notifications={filteredNotifications}
              onMarkAsRead={handleMarkAsRead}
              onDelete={handleDeleteNotification}
            />
          </TabsContent>

          <TabsContent value="unread" className="mt-6">
            <NotificationList 
              notifications={filteredNotifications}
              onMarkAsRead={handleMarkAsRead}
              onDelete={handleDeleteNotification}
            />
          </TabsContent>
        </Tabs>
      </div>
    </ProtectedRoute>
  )
}

interface NotificationListProps {
  notifications: Notification[]
  onMarkAsRead: (id: number) => void
  onDelete: (id: number) => void
}

function NotificationList({ notifications, onMarkAsRead, onDelete }: NotificationListProps) {
  if (notifications.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Bell className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">暂无通知</h3>
          <p className="text-muted-foreground text-center">
            您目前没有任何通知
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {notifications.map((notification) => (
        <Card key={notification.id} className={`${!notification.is_read ? 'border-l-4 border-l-primary' : ''}`}>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                {getNotificationIcon(notification.type)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className={`font-semibold ${!notification.is_read ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {notification.title || '通知'}
                    </h3>
                    {getNotificationBadge(notification.type)}
                    {!notification.is_read && (
                      <Badge variant="secondary" className="text-xs">
                        未读
                      </Badge>
                    )}
                  </div>
                  <p className={`${!notification.is_read ? 'text-foreground' : 'text-muted-foreground'} mb-2`}>
                    {notification.content}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(notification.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 ml-4">
                {!notification.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onMarkAsRead(notification.id)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                      <Check className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(notification.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}