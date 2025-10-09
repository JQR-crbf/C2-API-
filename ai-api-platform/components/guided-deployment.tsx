"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
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
import { useToast } from "@/hooks/use-toast"

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
  userAction?: 'manual' | 'auto'
  userInstruction?: string
  expectedOutput?: string
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
  
  // 向导步骤配置
  const [steps, setSteps] = useState<WizardStep[]>([])
  const [isLoadingSteps, setIsLoadingSteps] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  

  
  // 添加重置步骤状态的功能
  const resetStepsStatus = () => {
    localStorage.removeItem(`completed_steps_${taskId}`)
    setSteps(prevSteps => 
      prevSteps.map(step => ({ ...step, isCompleted: false }))
    )
    setCurrentStepIndex(0)
    toast({
      title: "步骤状态已重置",
      description: "所有步骤已标记为未完成",
    })
  }

  // 从后端获取动态生成的步骤
  const fetchDeploymentSteps = async () => {
    try {
      setIsLoadingSteps(true)
      const token = localStorage.getItem('access_token')
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
      const response = await fetch(`${API_BASE_URL}/api/guided-deployment/generate-steps`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          project_name: taskTitle || 'API项目',
          project_description: '自动生成的API项目',
          deployment_path: projectPath,
          git_repo_url: gitRepoUrl || null,
          code_files: generatedCode ? [{
             path: 'main.py',
             content: generatedCode,
             type: 'python'
           }] : []
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch deployment steps')
      }
      
      const data = await response.json()
      
      // 从localStorage获取已完成的步骤状态
      const savedCompletedSteps = localStorage.getItem(`completed_steps_${taskId}`)
      const completedStepIds = savedCompletedSteps ? JSON.parse(savedCompletedSteps) : []
      const completedStepsSet = new Set(completedStepIds)
      
      // 转换后端步骤格式为前端格式
      const convertedSteps: WizardStep[] = data.steps.map((step: any) => ({
        id: step.step_number,
        title: step.step_name,
        description: step.step_description,
        command: step.command,
        isCompleted: completedStepsSet.has(step.step_number),
        userAction: step.user_action || 'auto',
        userInstruction: step.user_instruction,
        expectedOutput: step.expected_output,
        requiresInput: step.requires_input || false,
        inputPlaceholder: step.input_placeholder
      }))
      
      setSteps(convertedSteps)
      
      // 恢复当前步骤索引：找到第一个未完成的步骤
      const firstIncompleteIndex = convertedSteps.findIndex(step => !step.isCompleted)
      if (firstIncompleteIndex !== -1) {
        setCurrentStepIndex(firstIncompleteIndex)
      } else if (convertedSteps.length > 0) {
        // 如果所有步骤都完成了，显示最后一个步骤
        setCurrentStepIndex(convertedSteps.length - 1)
      }
    } catch (error) {
      console.error('Error fetching deployment steps:', error)
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      setFetchError(`获取部署步骤失败: ${errorMessage}`)
      
      toast({
        title: "获取部署步骤失败",
        description: `错误详情: ${errorMessage}`,
        variant: "destructive"
      })
      
      // 不再自动降级到默认步骤
      setSteps([])
    } finally {
      setIsLoadingSteps(false)
    }
  }
  
  // 默认步骤（作为后备）
  const getDefaultSteps = (): WizardStep[] => [
    {
      id: 1,
      title: '进入项目目录',
      description: '进入项目部署目录',
      command: `cd ${projectPath}`,
      isCompleted: false
    },
    {
      id: 2,
      title: '切换到主分支',
      description: '切换到主分支',
      command: 'git checkout main',
      isCompleted: false
    },
    {
      id: 3,
      title: '获取最新代码',
      description: '从远程仓库拉取最新的代码',
      command: 'git pull origin main',
      isCompleted: false
    }
  ]
  
  // 重试获取步骤
  const retryFetchSteps = () => {
    setFetchError(null)
    setIsLoadingSteps(true)
    fetchDeploymentSteps()
  }

  // 组件加载时获取步骤
  useEffect(() => {
    fetchDeploymentSteps()
  }, [taskId, taskTitle, generatedCode])
  
  // 保存当前步骤索引到localStorage
  useEffect(() => {
    if (steps.length > 0) {
      localStorage.setItem(`deployment_step_${taskId}`, currentStepIndex.toString())
    }
  }, [currentStepIndex, taskId, steps.length])
  
  // 从localStorage恢复步骤索引（仅在步骤加载完成后）
  useEffect(() => {
    if (steps.length > 0) {
      const savedStepIndex = localStorage.getItem(`deployment_step_${taskId}`)
      if (savedStepIndex !== null) {
        const stepIndex = parseInt(savedStepIndex, 10)
        if (stepIndex >= 0 && stepIndex < steps.length) {
          // 只有当保存的步骤索引有效且该步骤未完成时才恢复
          const savedStep = steps[stepIndex]
          if (savedStep && !savedStep.isCompleted) {
            setCurrentStepIndex(stepIndex)
          }
        }
      }
    }
  }, [steps, taskId])

  // 从localStorage恢复已完成的步骤状态
  useEffect(() => {
    if (!taskId || steps.length === 0) return
    
    const savedCompletedSteps = localStorage.getItem(`completed_steps_${taskId}`)
    if (savedCompletedSteps) {
      try {
        const completedStepIds = JSON.parse(savedCompletedSteps)
        const completedStepsSet = new Set(completedStepIds)
        
        setSteps(prevSteps => 
          prevSteps.map(step => ({
            ...step,
            isCompleted: completedStepsSet.has(step.id)
          }))
        )
      } catch (error) {
        console.error('恢复步骤状态失败:', error)
      }
    }
  }, [taskId, steps.length])

  // 更新步骤命令
  const updateStepCommands = () => {
    setSteps(prevSteps => 
      prevSteps.map(step => {
        let updatedCommand = step.command
        if (updatedCommand) {
          updatedCommand = updatedCommand.replace(/\$\{projectPath\}/g, projectPath)
          updatedCommand = updatedCommand.replace(/\$\{filePath\}/g, filePath)
          updatedCommand = updatedCommand.replace(/\$\{fileName\}/g, fileName)
          updatedCommand = updatedCommand.replace(/\$\{gitCommitMessage\}/g, gitCommitMessage || '添加新的API功能')
        }
        return {
          ...step,
          command: updatedCommand
        }
      })
    )
  }

  // 监听配置变化，更新命令
  useEffect(() => {
    updateStepCommands()
  }, [projectPath, filePath, fileName, gitCommitMessage])

  // 获取当前步骤
  const getCurrentStep = () => steps[currentStepIndex]

  // 下一步
  const nextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      const newIndex = currentStepIndex + 1;
      setCurrentStepIndex(newIndex);
      // 自动滚动到当前步骤
      setTimeout(() => {
        const stepElement = document.getElementById(`step-${newIndex}`);
        if (stepElement) {
          stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }

  // 上一步
  const prevStep = () => {
    if (currentStepIndex > 0) {
      const newIndex = currentStepIndex - 1;
      setCurrentStepIndex(newIndex);
      // 自动滚动到当前步骤
      setTimeout(() => {
        const stepElement = document.getElementById(`step-${newIndex}`);
        if (stepElement) {
          stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }

  // 处理输入变化
  const handleInputChange = (value: string) => {
    const currentStep = getCurrentStep()
    if (currentStep.id === 7) {
      setFileName(value)
    } else if (currentStep.id === 18) {
      setGitCommitMessage(value)
    }
  }



  // 标记步骤完成（纯前端状态管理）
  const markStepCompleted = (stepId: number) => {
    // 更新本地状态
    setSteps(prevSteps => {
      const updatedSteps = prevSteps.map(step => 
        step.id === stepId ? { ...step, isCompleted: true } : step
      )
      
      // 保存到localStorage以实现持久化
      const completedSteps = updatedSteps
        .filter(step => step.isCompleted)
        .map(step => step.id)
      localStorage.setItem(`completed_steps_${taskId}`, JSON.stringify(completedSteps))
      
      return updatedSteps
    })
    
    // 自动跳转到下一个未完成的步骤
    const nextIncompleteIndex = steps.findIndex((step, index) => 
      index > currentStepIndex && step.id !== stepId && !step.isCompleted
    )
    if (nextIncompleteIndex !== -1) {
      setCurrentStepIndex(nextIncompleteIndex)
    }
    
    toast({
      title: "步骤已完成",
      description: "步骤状态已更新",
    })
  }

  // 复制命令到剪贴板
  const copyCommand = async (command: string) => {
    try {
      await navigator.clipboard.writeText(command)
      toast({
        title: "已复制",
        description: "命令已复制到剪贴板",
      })
    } catch (err) {
      toast({
        title: "复制失败",
        description: "无法复制到剪贴板",
        variant: "destructive",
      })
    }
  }

  // 执行命令
  const executeCommand = async (command: string) => {
    if (!isConnected) {
      toast({
        title: "未连接",
        description: "请先连接到服务器终端",
        variant: "destructive",
      })
      return
    }

    try {
      // 这里应该通过WebSocket或API发送命令到终端
      console.log('执行命令:', command)
      toast({
        title: "命令已发送",
        description: "正在执行: " + command,
      })
    } catch (error) {
      toast({
        title: "执行失败",
        description: "命令执行失败，请检查连接",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-6">


      {/* 中间：步骤向导 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            部署向导
          </CardTitle>
          <CardDescription>
            按步骤完成API部署
          </CardDescription>
          {/* 进度条 */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                进度: {steps.filter(step => step.isCompleted).length} / {steps.length} 步骤完成
              </span>
              <span className="font-medium">
                {steps.length > 0 ? Math.round((steps.filter(step => step.isCompleted).length / steps.length) * 100) : 0}%
              </span>
            </div>
            <Progress 
              value={steps.length > 0 ? (steps.filter(step => step.isCompleted).length / steps.length) * 100 : 0} 
              className="h-2"
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 步骤列表 */}
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                共 {steps.length} 个步骤，当前第 {currentStepIndex + 1} 步
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">跳转到步骤:</span>
                <Input
                  type="number"
                  min="1"
                  max={steps.length}
                  value={currentStepIndex + 1}
                  onChange={(e) => {
                    const stepNum = parseInt(e.target.value) - 1;
                    if (stepNum >= 0 && stepNum < steps.length) {
                      setCurrentStepIndex(stepNum);
                      // 自动滚动到选中的步骤
                      setTimeout(() => {
                        const stepElement = document.getElementById(`step-${stepNum}`);
                        if (stepElement) {
                          stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                      }, 100);
                    }
                  }}
                  className="w-16 h-6 text-xs"
                />
              </div>
            </div>
            <ScrollArea className="h-[600px] max-h-[80vh]">
              {isLoadingSteps ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">正在生成部署步骤...</p>
                  </div>
                </div>
              ) : fetchError ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center space-y-4">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <div>
                      <h3 className="text-lg font-medium text-foreground mb-2">获取部署步骤失败</h3>
                      <p className="text-sm text-muted-foreground mb-4 max-w-md">{fetchError}</p>
                      <div className="space-y-2">
                        <Button onClick={retryFetchSteps} className="w-full">
                          重试获取步骤
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          请检查网络连接和后端服务状态
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : steps.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center space-y-4">
                    <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto" />
                    <div>
                      <h3 className="text-lg font-medium text-foreground mb-2">暂无部署步骤</h3>
                      <p className="text-sm text-muted-foreground mb-4">未能获取到部署步骤，请重试</p>
                      <Button onClick={retryFetchSteps} variant="outline">
                        重新获取
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {steps.map((step, index) => (
                  <div
                    key={step.id}
                    id={`step-${index}`}
                    className={`p-3 rounded-lg border transition-colors ${
                      index === currentStepIndex
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                        : step.isCompleted
                        ? 'border-green-500 bg-green-50 dark:bg-green-950'
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {step.isCompleted ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : index === currentStepIndex ? (
                          <AlertCircle className="h-5 w-5 text-blue-500" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm">{step.title}</h4>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {step.description}
                        </p>
                        
                        {/* 用户手动操作指导 */}
                        {step.userAction === 'manual' && step.userInstruction && (
                          <div className="mt-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="text-xs font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                                  手动操作指导：
                                </p>
                                <p className="text-xs text-yellow-700 dark:text-yellow-300">
                                  {step.userInstruction}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* 预期输出提示 */}
                        {step.expectedOutput && (
                          <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
                            <p className="text-xs font-medium text-blue-800 dark:text-blue-200 mb-1">
                              预期结果：
                            </p>
                            <p className="text-xs text-blue-700 dark:text-blue-300">
                              {step.expectedOutput}
                            </p>
                          </div>
                        )}
                        
                        {step.command && (
                          <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono break-all">
                            {step.command}
                          </div>
                        )}
                        {step.requiresInput && index === currentStepIndex && (
                          <div className="mt-2">
                            <Input
                              className="h-8 text-sm"
                              placeholder={step.inputPlaceholder}
                              onChange={(e) => handleInputChange(e.target.value)}
                            />
                          </div>
                        )}
                      </div>
                      {step.command && step.userAction !== 'manual' && (
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyCommand(step.command!)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => executeCommand(step.command!)}
                            disabled={!isConnected}
                          >
                            <Terminal className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                      
                      {/* 手动操作步骤的按钮 */}
                      {step.userAction === 'manual' && (
                        <div className="flex gap-1">
                          {step.command && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyCommand(step.command!)}
                              title="复制命令"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => markStepCompleted(step.id)}
                            title="标记为已完成"
                          >
                            完成
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                </div>
              )}
            </ScrollArea>

            {/* 导航按钮 */}
            <div className="flex justify-between pt-4 border-t">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={prevStep}
                  disabled={currentStepIndex === 0}
                >
                  上一步
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetStepsStatus}
                  className="text-red-600 hover:text-red-700"
                >
                  重置
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => markStepCompleted(getCurrentStep().id)}
                  disabled={!getCurrentStep() || getCurrentStep().isCompleted}
                >
                  标记完成
                </Button>
                <Button
                  onClick={nextStep}
                  disabled={currentStepIndex === steps.length - 1}
                >
                  下一步
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>



      {/* 服务器终端 - 下方 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            服务器终端
          </CardTitle>
          <CardDescription>
            连接到服务器执行命令
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[110px]">
            <WebTerminal
              sessionId={`task-${taskId}`}
              onConnect={() => setIsConnected(true)}
              onDisconnect={() => setIsConnected(false)}
              className="h-full"
            />
          </div>
        </CardContent>
      </Card>

      


    </div>
  )
}