import React from "react"
import { CheckCircle, Clock, AlertCircle, Activity } from "lucide-react"

// 根据后端状态计算进度 - 简化为5个核心步骤
export const getProgressFromStatus = (status: string): number => {
  switch (status) {
    case 'submitted': return 20        // 1. 任务提交
    case 'ai_generating': return 40    // 2. 代码生成步骤
    case 'test_ready': return 40       // 2. 代码生成步骤
    case 'code_submitted': return 60   // 3. 代码提交
    case 'under_review': return 80     // 4. 管理员审核
    case 'deployed': return 100        // 5. 部署完成
    case 'approved': return 90         // 审核通过（中间状态）
    case 'rejected': return 0          // 审核拒绝
    default: return 0
  }
}

// 获取状态图标 - 简化为5个核心步骤
export const getStatusIcon = (status: string) => {
  switch (status) {
    case "submitted":
      return React.createElement(Clock, { className: "h-4 w-4 text-blue-600" })
    case "ai_generating":
      return React.createElement(Activity, { className: "h-4 w-4 text-purple-600" })
    case "code_submitted":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "under_review":
      return React.createElement(Clock, { className: "h-4 w-4 text-orange-600" })
    case "deployed":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "approved":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "rejected":
      return React.createElement(AlertCircle, { className: "h-4 w-4 text-red-600" })
    default:
      return React.createElement(Clock, { className: "h-4 w-4 text-gray-400" })
  }
}

// 获取状态徽章属性 - 简化为5个核心步骤
export const getStatusBadgeProps = (status: string) => {
  switch (status) {
    case "submitted":
      return { variant: "secondary" as const, className: "bg-blue-100 text-blue-800" }
    case "ai_generating":
      return { variant: "secondary" as const, className: "bg-purple-100 text-purple-800" }
    case "code_submitted":
      return { variant: "secondary" as const, className: "bg-green-100 text-green-800" }
    case "under_review":
      return { variant: "secondary" as const, className: "bg-orange-100 text-orange-800" }
    case "deployed":
      return { variant: "secondary" as const, className: "bg-green-100 text-green-800" }
    case "approved":
      return { variant: "secondary" as const, className: "bg-green-100 text-green-800" }
    case "rejected":
      return { variant: "destructive" as const, className: "bg-red-100 text-red-800" }
    default:
      return { variant: "secondary" as const, className: "bg-gray-100 text-gray-600" }
  }
}

// 获取状态文本 - 简化为5个核心步骤
export const getStatusText = (status: string): string => {
  switch (status) {
    case "submitted":
      return "任务提交"
    case "ai_generating":
      return "代码生成步骤"
    case "test_ready":
      return "代码生成步骤"
    case "code_submitted":
      return "代码提交"
    case "under_review":
      return "管理员审核"
    case "deployed":
      return "部署完成"
    case "approved":
      return "审核通过"
    case "rejected":
      return "审核拒绝"
    default:
      return "未知状态"
  }
}

// 根据状态分类任务 - 简化为5个核心步骤
export const categorizeTasksByStatus = (tasks: any[]) => {
  return {
    pending: tasks.filter(task => 
      ['submitted', 'ai_generating'].includes(task.status)
    ),
    inProgress: tasks.filter(task => 
      ['code_submitted', 'under_review'].includes(task.status)
    ),
    completed: tasks.filter(task => 
      ['approved', 'deployed'].includes(task.status)
    ),
    failed: tasks.filter(task => 
      ['rejected'].includes(task.status)
    )
  }
}