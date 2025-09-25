"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Bot, ArrowLeft, Play, Copy, Download, History, Zap, Code, FileText } from "lucide-react"
import { useAuth, ProtectedRoute } from "@/contexts/AuthContext"
import { apiClient, APITestRequest, APITestResponse, Task } from "@/lib/api"
import { toast } from "sonner"
import Link from "next/link"

// Helper functions for status display
const getStatusColor = (status: number) => {
  if (status >= 200 && status < 300) return "text-green-600"
  if (status >= 400 && status < 500) return "text-yellow-600"
  if (status >= 500) return "text-red-600"
  return "text-gray-600"
}

const getStatusBadge = (success: boolean) => {
  return success ? (
    <Badge variant="secondary" className="bg-green-100 text-green-800">
      成功
    </Badge>
  ) : (
    <Badge variant="secondary" className="bg-red-100 text-red-800">
      失败
    </Badge>
  )
}

function APITestingContent() {
  const { user } = useAuth()
  const [userTasks, setUserTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [method, setMethod] = useState('GET')
  const [url, setUrl] = useState('')
  const [requestBody, setRequestBody] = useState('{\n  "email": "user@example.com",\n  "password": "password123"\n}')
  const [headers, setHeaders] = useState('{\n  "Content-Type": "application/json"\n}')
  const [response, setResponse] = useState<APITestResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [testHistory, setTestHistory] = useState<any[]>([])
  const [availableEndpoints, setAvailableEndpoints] = useState<any[]>([])
  const [sampleData, setSampleData] = useState<any>(null)

  useEffect(() => {
    loadUserTasks()
    loadTestEndpoints()
    loadSampleData()
  }, [])

  const loadUserTasks = async () => {
    try {
      const tasksResponse = await apiClient.tasks.getAll()
      const tasksData = Array.isArray(tasksResponse) ? tasksResponse : []
      const completedTasks = tasksData.filter((task: Task) => task.status === 'completed')
      setUserTasks(completedTasks)
      if (completedTasks.length > 0) {
        setSelectedTask(completedTasks[0])
        // 根据任务设置默认的测试URL
        setUrl(`http://localhost:8080/api/auth/login`)
      }
    } catch (error) {
      console.error('Failed to load tasks:', error)
      toast.error('加载任务失败')
      // 如果无法加载任务，设置一些示例数据用于测试
      const mockTasks = [
        {
          id: 'mock-1',
          name: '用户管理API',
          title: '用户管理API',
          description: '用户注册、登录、信息管理',
          status: 'completed' as const,
          progress: 100,
          language: 'Python',
          framework: 'FastAPI',
          database: 'PostgreSQL',
          features: ['用户认证', 'CRUD操作'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_id: user?.id?.toString() || 'test',
          input_params: {},
          output_params: {},
          generated_code: '',
          branch_name: '',
          test_cases: '',
          test_result_image: '',
          test_url: '',
          admin_comment: '',
          user: null
        }
      ]
      setUserTasks(mockTasks)
      setSelectedTask(mockTasks[0])
      setUrl('http://localhost:8080/api/auth/login')
    }
  }

  const loadTestEndpoints = async () => {
    try {
      const response = await apiClient.getTestEndpoints()
      setAvailableEndpoints(response.endpoints || [])
    } catch (error) {
      console.error('Failed to load test endpoints:', error)
    }
  }

  const loadSampleData = async () => {
    try {
      const data = await apiClient.getSampleTestData()
      setSampleData(data)
    } catch (error) {
      console.error('Failed to load sample data:', error)
    }
  }

  const handleTaskChange = (taskId: string) => {
    const task = userTasks.find(t => t.id === taskId)
    if (task) {
      setSelectedTask(task)
      // 根据任务类型设置不同的测试端点
      if ((task.name || task.title).includes('用户')) {
        setUrl('http://localhost:8080/api/auth/login')
        setMethod('POST')
        setRequestBody(JSON.stringify(sampleData?.login_request || {
          username: 'admin',
          password: 'admin123'
        }, null, 2))
      } else if ((task.name || task.title).includes('认证') || (task.name || task.title).includes('登录')) {
        setUrl('http://localhost:8080/api/auth/login')
        setMethod('POST')
        setRequestBody(JSON.stringify(sampleData?.login_request || {
          username: 'admin',
          password: 'admin123'
        }, null, 2))
      } else {
        setUrl('http://localhost:8080/health')
        setMethod('GET')
      }
    }
  }

  const handleEndpointSelect = (endpoint: any) => {
    setUrl(endpoint.url)
    setMethod(endpoint.method)
    if (endpoint.sample_body) {
      setRequestBody(JSON.stringify(endpoint.sample_body, null, 2))
    }
    if (endpoint.headers) {
      setHeaders(JSON.stringify(endpoint.headers, null, 2))
    }
  }

  const handleSendRequest = async () => {
    if (!selectedTask) {
      toast.error('请先选择一个已完成的任务')
      return
    }

    setIsLoading(true)
    
    try {
      let parsedHeaders = {}
      let parsedBody = undefined

      // 解析headers
      if (headers.trim()) {
        try {
          parsedHeaders = JSON.parse(headers)
        } catch (error) {
          toast.error('Headers格式错误，请使用有效的JSON格式')
          setIsLoading(false)
          return
        }
      }

      // 解析body（仅对POST、PUT、PATCH方法）
      if (['POST', 'PUT', 'PATCH'].includes(method) && requestBody.trim()) {
        try {
          parsedBody = requestBody
        } catch (error) {
          toast.error('请求体格式错误')
          setIsLoading(false)
          return
        }
      }

      const testRequest: APITestRequest = {
        method,
        url,
        headers: parsedHeaders,
        body: parsedBody
      }

      const testResponse = await apiClient.testAPI(testRequest)
      setResponse(testResponse)
      
      // 添加到测试历史
      const historyItem = {
        id: Date.now(),
        method,
        url,
        status: testResponse.status,
        responseTime: testResponse.responseTime,
        timestamp: new Date().toISOString()
      }
      setTestHistory(prev => [historyItem, ...prev.slice(0, 9)]) // 保留最近10条记录
      
      toast.success('API测试完成')
    } catch (error: any) {
      console.error('API test failed:', error)
      setResponse(error)
      toast.error('API测试失败')
    } finally {
      setIsLoading(false)
    }
  }



  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">API 测试</span>
            </div>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">API 测试界面</h1>
          <p className="text-muted-foreground mt-1">在浏览器中直接测试您生成的 API</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Request Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* API Selection */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" />
                  API 配置
                </CardTitle>
                <CardDescription>选择您要测试的 API 和端点</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>选择已完成的任务</Label>
                    <Select 
                      value={selectedTask?.id || ''} 
                      onValueChange={handleTaskChange}
                      disabled={userTasks.length === 0}
                    >
                      <SelectTrigger className="bg-input border-border">
                        <SelectValue placeholder={userTasks.length === 0 ? "暂无已完成的任务" : "选择一个任务"} />
                      </SelectTrigger>
                      <SelectContent>
                        {userTasks.map((task) => (
                          <SelectItem key={task.id} value={task.id}>
                            {task.name || task.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>请求方法</Label>
                      <Select value={method} onValueChange={setMethod}>
                        <SelectTrigger className="bg-input border-border">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="GET">GET</SelectItem>
                          <SelectItem value="POST">POST</SelectItem>
                          <SelectItem value="PUT">PUT</SelectItem>
                          <SelectItem value="DELETE">DELETE</SelectItem>
                          <SelectItem value="PATCH">PATCH</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>API URL</Label>
                      <Input 
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="http://localhost:8080/api/v1/endpoint"
                        className="bg-input border-border"
                      />
                    </div>
                  </div>
                </div>

                {/* Request URL */}
                <div className="space-y-2">
                  <Label>完整请求 URL</Label>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="px-3 py-1">
                      {method}
                    </Badge>
                    <Input
                      value={url}
                      readOnly
                      className="bg-muted border-border"
                    />
                    <Button variant="outline" size="sm">
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Request Details */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5 text-primary" />
                  请求详情
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="body" className="space-y-4">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="body">请求体</TabsTrigger>
                    <TabsTrigger value="headers">请求头</TabsTrigger>
                  </TabsList>

                  <TabsContent value="body" className="space-y-2">
                    <Label>请求体 (JSON)</Label>
                    <Textarea
                      value={requestBody}
                      onChange={(e) => setRequestBody(e.target.value)}
                      placeholder="输入 JSON 请求体..."
                      rows={8}
                      className="bg-input border-border font-mono text-sm"
                      disabled={method === "GET"}
                    />
                    {method === "GET" && (
                      <p className="text-sm text-muted-foreground">GET 请求不需要请求体</p>
                    )}
                  </TabsContent>

                  <TabsContent value="headers" className="space-y-2">
                    <Label>请求头 (JSON)</Label>
                    <Textarea
                      value={headers}
                      onChange={(e) => setHeaders(e.target.value)}
                      placeholder="输入请求头..."
                      rows={6}
                      className="bg-input border-border font-mono text-sm"
                    />
                  </TabsContent>
                </Tabs>

                <div className="flex justify-end mt-4">
                  <Button
                    onClick={handleSendRequest}
                    disabled={isLoading}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                        发送中...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Play className="h-4 w-4" />
                        发送请求
                      </div>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Response */}
            {response && (
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    响应
                  </CardTitle>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">状态:</span>
                      <span className={`font-medium ${getStatusColor(response.status)}`}>
                        {response.status} {response.statusText}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">时间:</span>
                      <span className="font-medium text-foreground">{response.responseTime}ms</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="response" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="response">响应体</TabsTrigger>
                      <TabsTrigger value="response-headers">响应头</TabsTrigger>
                    </TabsList>

                    <TabsContent value="response">
                      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                        <pre className="text-sm text-gray-100">
                          <code>{JSON.stringify(response.data, null, 2)}</code>
                        </pre>
                      </div>
                      <div className="flex justify-end mt-2">
                        <Button variant="outline" size="sm">
                          <Copy className="h-4 w-4 mr-2" />
                          复制响应
                        </Button>
                      </div>
                    </TabsContent>

                    <TabsContent value="response-headers">
                      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                        <pre className="text-sm text-gray-100">
                          <code>{JSON.stringify(response.headers, null, 2)}</code>
                        </pre>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Available Tasks */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-foreground">已完成的任务</CardTitle>
                <CardDescription>您可以测试的API项目</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {userTasks.length === 0 ? (
                  <p className="text-sm text-muted-foreground">暂无已完成的任务</p>
                ) : (
                  userTasks.map((task) => (
                    <div
                      key={task.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedTask?.id === task.id ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                      }`}
                      onClick={() => handleTaskChange(task.id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-foreground">{task.name || task.title}</h4>
                        <Badge variant="secondary" className="bg-green-100 text-green-800">
                          已完成
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{task.description}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Test History */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-4 w-4 text-primary" />
                  测试历史
                </CardTitle>
                <CardDescription>您最新的 API 测试结果</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {testHistory.length === 0 ? (
                  <p className="text-sm text-muted-foreground">暂无测试历史</p>
                ) : (
                  testHistory.map((test) => (
                    <div key={test.id} className="p-3 bg-muted rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {test.method}
                          </Badge>
                          <span className="text-sm font-medium text-foreground truncate">{test.url}</span>
                        </div>
                        {getStatusBadge(test.status >= 200 && test.status < 300)}
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className={getStatusColor(test.status)}>{test.status}</span>
                        <span>{test.responseTime}ms</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{new Date(test.timestamp).toLocaleString()}</p>
                    </div>
                  ))
                )}
                {testHistory.length > 0 && (
                  <Button variant="outline" className="w-full bg-transparent">
                    <Download className="h-4 w-4 mr-2" />
                    导出测试结果
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function APITestingPage() {
  return (
    <ProtectedRoute>
      <APITestingContent />
    </ProtectedRoute>
  )
}
