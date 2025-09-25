"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { WebTerminal } from "@/components/web-terminal"
import { 
  CheckCircle, 
  Circle, 
  AlertCircle, 
  Copy, 
  Terminal, 
  Code2, 
  GitBranch
} from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"

// 组件属性接口
interface GuidedDeploymentProps {
  taskId: number
  taskTitle: string
  generatedCode: string
}

// 向导步骤接口
interface WizardStep {
  id: number
  title: string
  description: string
  command?: string
  isCompleted: boolean
  requiresInput?: boolean
  inputPlaceholder?: string
  inputValue?: string
}

export function GuidedDeployment({ taskId, taskTitle, generatedCode }: GuidedDeploymentProps) {
  const { toast } = useToast()
  
  // 向导状态
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const [projectPath, setProjectPath] = useState('/home/api_projects')
  const [gitRepoUrl, setGitRepoUrl] = useState('')
  const [fileName, setFileName] = useState('')
  const [filePath, setFilePath] = useState('/home/api_projects/api')
  const [gitCommitMessage, setGitCommitMessage] = useState('')
  
  // 13个部署步骤
  const [steps, setSteps] = useState<WizardStep[]>([
    {
      id: 1,
      title: '连接服务器',
      description: '点击下方华为云CloudShell按钮连接到服务器',
      isCompleted: false
    },
    {
      id: 2,
      title: '进入项目目录',
      description: '切换到指定的项目目录',
      command: `cd ${projectPath}`,
      isCompleted: false
    },
    {
      id: 3,
      title: '从Git库拉取项目',
      description: '从Git仓库拉取最新的项目代码',
      command: 'git pull origin main',
      isCompleted: false,
      requiresInput: true,
      inputPlaceholder: '请输入Git仓库URL（如果首次克隆）'
    },
    {
      id: 4,
      title: 'AI生成代码',
      description: '查看中间区域显示的AI生成的代码',
      isCompleted: false
    },
    {
      id: 5,
      title: '进入代码存放目录',
      description: '切换到代码文件存放的目录',
      command: `cd ${filePath}`,
      isCompleted: false,
      requiresInput: true,
      inputPlaceholder: '请输入代码存放路径'
    },
    {
      id: 6,
      title: '创建Python文件',
      description: '根据需求创建新的Python文件',
      command: `touch ${fileName || 'new_api.py'}`,
      isCompleted: false,
      requiresInput: true,
      inputPlaceholder: '请输入文件名（如：user_api.py）'
    },
    {
      id: 7,
      title: '复制代码到文件',
      description: '从中间代码区复制代码，然后粘贴到服务器终端中',
      isCompleted: false
    },
    {
      id: 8,
      title: '保存文件',
      description: '保存新创建的文件',
      command: `nano ${fileName || 'new_api.py'}`,
      isCompleted: false
    },
    {
      id: 9,
      title: '返回项目根目录',
      description: '回到项目的根目录',
      command: `cd ${projectPath}`,
      isCompleted: false
    },
    {
      id: 10,
      title: '启动项目',
      description: '启动项目服务',
      command: 'python main.py',
      isCompleted: false
    },
    {
      id: 11,
      title: 'Git添加文件',
      description: '将所有更改添加到Git暂存区',
      command: 'git add .',
      isCompleted: false
    },
    {
      id: 12,
      title: 'Git提交',
      description: '提交更改到本地仓库',
      command: `git commit -m "${gitCommitMessage || '添加新的API功能'}"`,
      isCompleted: false,
      requiresInput: true,
      inputPlaceholder: '请输入提交信息'
    },
    {
      id: 13,
      title: 'Git推送',
      description: '推送更改到远程仓库',
      command: 'git push origin main',
      isCompleted: false
    }
  ])
  
  // 获取当前步骤
  const getCurrentStep = () => steps[currentStepIndex]
  
  // 下一步
  const nextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1)
    }
  }
  
  // 复制命令到剪贴板
  const copyCommand = async (command: string) => {
    try {
      await navigator.clipboard.writeText(command)
      toast({
        title: "已复制",
        description: "命令已复制到剪贴板"
      })
    } catch (error) {
      console.error('复制失败:', error)
      toast({
        title: "复制失败",
        description: "请手动复制命令",
        variant: "destructive"
      })
    }
  }
  
  // 更新所有命令中的变量
  const updateCommands = () => {
    setSteps(prevSteps => 
      prevSteps.map(step => {
        let updatedCommand = step.command
        if (updatedCommand) {
          updatedCommand = updatedCommand.replace(/\$\{projectPath\}/g, projectPath)
          updatedCommand = updatedCommand.replace(/\$\{filePath\}/g, filePath)
          updatedCommand = updatedCommand.replace(/\$\{fileName\}/g, fileName || 'new_api.py')
          updatedCommand = updatedCommand.replace(/\$\{gitCommitMessage\}/g, gitCommitMessage || '添加新的API功能')
        }
        return { ...step, command: updatedCommand }
      })
    )
  }
  
  // 标记步骤完成
  const markStepCompleted = (stepId: number) => {
    setSteps(prevSteps => 
      prevSteps.map(step => 
        step.id === stepId ? { ...step, isCompleted: true } : step
      )
    )
  }
  
  // 监听输入变化，更新命令
  useEffect(() => {
    updateCommands()
  }, [projectPath, filePath, fileName, gitCommitMessage])
  
  // 处理输入变化
  const handleInputChange = (stepId: number, value: string) => {
    const step = steps.find(s => s.id === stepId)
    if (!step) return
    
    // 根据步骤ID更新对应的状态
    switch (stepId) {
      case 3: // Git仓库URL
        setGitRepoUrl(value)
        break
      case 5: // 代码存放路径
        setFilePath(value)
        break
      case 6: // 文件名
        setFileName(value)
        break
      case 12: // Git提交信息
        setGitCommitMessage(value)
        break
    }
    
    // 更新步骤的输入值
    setSteps(prevSteps => 
      prevSteps.map(s => 
        s.id === stepId ? { ...s, inputValue: value } : s
      )
    )
  }
  
  // 获取步骤图标
  const getStepIcon = (step: WizardStep, index: number) => {
    if (step.isCompleted) {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    } else if (index === currentStepIndex) {
      return <Circle className="h-5 w-5 text-blue-500 fill-current" />
    } else {
      return <Circle className="h-5 w-5 text-gray-300" />
    }
  }
  
  // 如果没有生成代码，显示提示
  if (!generatedCode) {
    return (
      <div className="flex items-center justify-center h-64">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            任务尚未生成代码，无法开始部署。请等待AI代码生成完成。
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  const currentStep = steps[currentStepIndex]
  
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
      {/* 上栏：步骤引导 */}
      <Card className="flex-shrink-0">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            部署步骤
          </CardTitle>
          <CardDescription>
            按顺序执行以下步骤完成部署
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 步骤进度条 */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">
                步骤 {currentStepIndex + 1} / {steps.length}
              </span>
              <div className="flex-1 mx-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium">
                {Math.round(((currentStepIndex + 1) / steps.length) * 100)}%
              </span>
            </div>

            {/* 当前步骤详情 */}
            <div className="border rounded-lg p-4 bg-blue-50 border-blue-200">
              <div className="flex items-start gap-3">
                {getStepIcon(currentStep, currentStepIndex)}
                <div className="flex-1">
                  <h3 className="font-medium text-blue-900">{currentStep.title}</h3>
                  <p className="text-sm text-blue-700 mt-1">{currentStep.description}</p>
                  
                  {/* 输入字段 */}
                  {currentStep.requiresInput && (
                    <div className="mt-3">
                      <Input
                        placeholder={currentStep.inputPlaceholder}
                        value={currentStep.inputValue || ''}
                        onChange={(e) => handleInputChange(currentStep.id, e.target.value)}
                        className="bg-white"
                      />
                    </div>
                  )}
                  
                  {/* 命令显示 */}
                  {currentStep.command && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between bg-gray-900 text-green-400 p-3 rounded font-mono text-sm">
                        <code>{currentStep.command}</code>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyCommand(currentStep.command!)}
                          className="text-green-400 hover:text-green-300 hover:bg-gray-800"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {/* 操作按钮 */}
                  <div className="flex gap-2 mt-4">
                    {currentStep.isCompleted ? (
                      <Button 
                        onClick={nextStep}
                        disabled={currentStepIndex >= steps.length - 1}
                      >
                        下一步
                      </Button>
                    ) : (
                      <Button 
                        onClick={() => markStepCompleted(currentStep.id)}
                        variant="outline"
                      >
                        标记完成
                      </Button>
                    )}
                    
                    {currentStepIndex > 0 && (
                      <Button 
                        variant="ghost"
                        onClick={() => setCurrentStepIndex(currentStepIndex - 1)}
                      >
                        上一步
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 所有步骤概览 */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">所有步骤</h4>
              <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className={`flex items-center gap-2 p-2 rounded text-sm cursor-pointer transition-colors ${
                      index === currentStepIndex 
                        ? 'bg-blue-100 border border-blue-300' 
                        : step.isCompleted 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                    }`}
                    onClick={() => setCurrentStepIndex(index)}
                  >
                    {getStepIcon(step, index)}
                    <span className={`flex-1 ${
                      step.isCompleted ? 'text-green-700' : 
                      index === currentStepIndex ? 'text-blue-700' : 'text-gray-600'
                    }`}>
                      {step.title}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* 下栏：代码和终端 */}
      <div className="flex-1 flex flex-col gap-4">
        {/* 生成的代码 */}
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Code2 className="h-5 w-5" />
              生成的代码
            </CardTitle>
            <CardDescription>
              查看将要部署的代码内容
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="preview" className="h-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="preview">代码预览</TabsTrigger>
                <TabsTrigger value="files">文件列表</TabsTrigger>
              </TabsList>
              
              <TabsContent value="preview" className="mt-4">
                <ScrollArea className="h-[300px] w-full">
                  <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto">
                    <code>{generatedCode}</code>
                  </pre>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="files" className="mt-4">
                <ScrollArea className="h-[300px] w-full">
                  <div className="space-y-2">
                    <div className="p-4 text-center text-gray-500">
                      <p className="text-sm">将要创建的文件:</p>
                      <div className="mt-2 p-2 border rounded bg-gray-50">
                        <div className="font-mono text-sm">{fileName || 'new_api.py'}</div>
                        <div className="text-xs text-gray-500">Python API文件</div>
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        
        {/* 终端输出 */}
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              终端输出
            </CardTitle>
            <CardDescription>
              实时查看部署过程中的命令执行结果
            </CardDescription>
          </CardHeader>
          <CardContent>
            <WebTerminal
               sessionId={`deployment-${taskId}-${Date.now()}`}
               className="h-[400px]"
               onConnect={() => {
                 setIsConnected(true)
                 toast({
                   title: "连接成功",
                   description: "已连接到服务器终端"
                 })
               }}
               onDisconnect={() => {
                 setIsConnected(false)
                 toast({
                   title: "连接断开",
                   description: "与服务器终端的连接已断开"
                 })
               }}
             />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}