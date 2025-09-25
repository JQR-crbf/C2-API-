"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Bot, ArrowLeft, Upload, Zap, Code, Database, Shield, FileText } from "lucide-react"
import { useAuth, ProtectedRoute } from "@/contexts/AuthContext"
import { apiClient } from "@/lib/api"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import Link from "next/link"

function CreateTaskContent() {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    language: "",
    framework: "",
    database: "",
    authentication: false,
    fileUpload: false,
    apiDocumentation: true,
    testCases: true,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    try {
      const features = []
      if (formData.authentication) features.push('authentication')
      if (formData.fileUpload) features.push('file_upload')
      if (formData.apiDocumentation) features.push('api_documentation')
      if (formData.testCases) features.push('test_cases')
      
      const taskData = {
        name: formData.name,
        description: formData.description,
        language: formData.language || 'python',
        framework: formData.framework || 'fastapi',
        database: formData.database || 'mysql',
        features,
      }
      
      const newTask = await apiClient.tasks.create(taskData)
      toast.success('API任务创建成功！')
      router.push(`/tasks/${newTask.id}`)
    } catch (error) {
      const message = error instanceof Error ? error.message : '创建任务失败'
      toast.error(message)
      console.error('Failed to create task:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Link href="/tasks">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">创建新API</span>
            </div>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">创建新API任务</h1>
          <p className="text-muted-foreground">
            用自然语言描述您的API需求，让AI为您生成代码
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                基本信息
              </CardTitle>
              <CardDescription>提供关于您API的基本详细信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">API名称 *</Label>
                <Input
                  id="name"
                  placeholder="例如：用户管理API"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">描述 *</Label>
                <Textarea
                  id="description"
                  placeholder="用自然语言描述您的API应该做什么。请尽可能详细。例如：'创建一个允许用户注册、登录、更新个人资料和管理账户设置的API。包括密码重置功能和邮箱验证。'"
                  value={formData.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  required
                  rows={6}
                  className="bg-input border-border resize-none"
                />
                <p className="text-sm text-muted-foreground">
                  您的描述越详细，AI就能更好地理解您的需求。
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Technical Configuration */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5 text-primary" />
                技术配置
              </CardTitle>
              <CardDescription>选择您偏好的技术栈</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="language">编程语言</Label>
                  <Select value={formData.language} onValueChange={(value) => handleInputChange("language", value)}>
                    <SelectTrigger className="bg-input border-border">
                      <SelectValue placeholder="选择语言" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="python">Python</SelectItem>
                      <SelectItem value="javascript">JavaScript/Node.js</SelectItem>
                      <SelectItem value="typescript">TypeScript</SelectItem>
                      <SelectItem value="java">Java</SelectItem>
                      <SelectItem value="csharp">C#</SelectItem>
                      <SelectItem value="go">Go</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="framework">框架</Label>
                  <Select value={formData.framework} onValueChange={(value) => handleInputChange("framework", value)}>
                    <SelectTrigger className="bg-input border-border">
                      <SelectValue placeholder="选择框架" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fastapi">FastAPI</SelectItem>
                      <SelectItem value="flask">Flask</SelectItem>
                      <SelectItem value="django">Django REST</SelectItem>
                      <SelectItem value="express">Express.js</SelectItem>
                      <SelectItem value="nestjs">NestJS</SelectItem>
                      <SelectItem value="spring">Spring Boot</SelectItem>
                      <SelectItem value="gin">Gin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="database">数据库</Label>
                <Select value={formData.database} onValueChange={(value) => handleInputChange("database", value)}>
                  <SelectTrigger className="bg-input border-border">
                    <SelectValue placeholder="选择数据库（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="postgresql">PostgreSQL</SelectItem>
                    <SelectItem value="mysql">MySQL</SelectItem>
                    <SelectItem value="sqlite">SQLite</SelectItem>
                    <SelectItem value="mongodb">MongoDB</SelectItem>
                    <SelectItem value="redis">Redis</SelectItem>
                    <SelectItem value="none">无数据库</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Additional Features */}
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                附加功能
              </CardTitle>
              <CardDescription>选择要包含在您API中的附加功能</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="authentication"
                    checked={formData.authentication}
                    onCheckedChange={(checked) => handleInputChange("authentication", checked as boolean)}
                  />
                  <Label htmlFor="authentication" className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-primary" />
                    身份验证和授权
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="fileUpload"
                    checked={formData.fileUpload}
                    onCheckedChange={(checked) => handleInputChange("fileUpload", checked as boolean)}
                  />
                  <Label htmlFor="fileUpload" className="flex items-center gap-2">
                    <Upload className="h-4 w-4 text-primary" />
                    文件上传支持
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="apiDocumentation"
                    checked={formData.apiDocumentation}
                    onCheckedChange={(checked) => handleInputChange("apiDocumentation", checked as boolean)}
                  />
                  <Label htmlFor="apiDocumentation" className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    API文档 (Swagger)
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="testCases"
                    checked={formData.testCases}
                    onCheckedChange={(checked) => handleInputChange("testCases", checked as boolean)}
                  />
                  <Label htmlFor="testCases" className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-primary" />
                    自动化测试用例
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <div className="flex justify-center">
            <Button
              type="submit"
              size="lg"
              className="bg-primary hover:bg-primary/90 text-primary-foreground px-8"
              disabled={isSubmitting || !formData.name || !formData.description}
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  正在创建API任务...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  创建API任务
                </div>
              )}
            </Button>
          </div>
        </form>

        {/* Help Section */}
        <Card className="border-border bg-muted/50">
          <CardContent className="p-6">
            <h3 className="font-semibold text-foreground mb-3">获得更好结果的提示</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• 明确说明您需要的功能</li>
              <li>• 包含数据模型和关系的详细信息</li>
              <li>• 提及任何特定的业务规则或验证要求</li>
              <li>• 指定是否需要分页、排序或筛选功能</li>
              <li>• 包含您需要的任何第三方集成</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function CreateTaskPage() {
  return (
    <ProtectedRoute>
      <CreateTaskContent />
    </ProtectedRoute>
  )
}
