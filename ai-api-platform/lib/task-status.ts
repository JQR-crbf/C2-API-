import React from "react"
import { CheckCircle, Clock, AlertCircle, Activity } from "lucide-react"

// 根据后端状态计算进度
export const getProgressFromStatus = (status: string): number => {
  switch (status) {
    case 'submitted': return 0
    case 'code_pulling': return 10
    case 'branch_created': return 20
    case 'ai_generating': return 30
    case 'test_ready': return 60
    case 'testing': return 70
    case 'test_completed': return 80
    case 'code_pushed': return 85
    case 'under_review': return 90
    case 'approved': return 95
    case 'deployed': return 100
    case 'rejected': return 0
    default: return 0
  }
}

// 获取状态图标
export const getStatusIcon = (status: string) => {
  switch (status) {
    case "submitted":
      return React.createElement(Clock, { className: "h-4 w-4 text-gray-600" })
    case "code_pulling":
      return React.createElement(Clock, { className: "h-4 w-4 text-blue-600" })
    case "branch_created":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-blue-600" })
    case "ai_generating":
      return React.createElement(Clock, { className: "h-4 w-4 text-purple-600" })
    case "test_ready":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "testing":
      return React.createElement(Activity, { className: "h-4 w-4 text-yellow-600" })
    case "test_completed":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "code_pushed":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "under_review":
      return React.createElement(Clock, { className: "h-4 w-4 text-orange-600" })
    case "approved":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "deployed":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "rejected":
      return React.createElement(AlertCircle, { className: "h-4 w-4 text-red-600" })
    case "completed":
      return React.createElement(CheckCircle, { className: "h-4 w-4 text-green-600" })
    case "in-progress":
      return React.createElement(Clock, { className: "h-4 w-4 text-blue-600" })
    case "failed":
      return React.createElement(AlertCircle, { className: "h-4 w-4 text-red-600" })
    default:
      return React.createElement(Clock, { className: "h-4 w-4 text-gray-400" })
  }
}

// 获取状态徽章的属性
export const getStatusBadgeProps = (status: string) => {
  switch (status) {
    case "submitted":
      return { className: "bg-gray-100 text-gray-800 border-gray-200", children: "已提交" }
    case "code_pulling":
      return { className: "bg-blue-100 text-blue-800 border-blue-200", children: "拉取代码中" }
    case "branch_created":
      return { className: "bg-blue-100 text-blue-800 border-blue-200", children: "分支已创建" }
    case "ai_generating":
      return { className: "bg-purple-100 text-purple-800 border-purple-200", children: "AI生成代码中" }
    case "test_ready":
      return { className: "bg-green-100 text-green-800 border-green-200", children: "测试环境准备就绪" }
    case "testing":
      return { className: "bg-yellow-100 text-yellow-800 border-yellow-200", children: "测试中" }
    case "test_completed":
      return { className: "bg-green-100 text-green-800 border-green-200", children: "测试完成" }
    case "code_pushed":
      return { className: "bg-green-100 text-green-800 border-green-200", children: "代码已推送" }
    case "under_review":
      return { className: "bg-orange-100 text-orange-800 border-orange-200", children: "管理员审核中" }
    case "approved":
      return { className: "bg-green-100 text-green-800 border-green-200", children: "审核通过" }
    case "deployed":
      return { className: "bg-green-100 text-green-800 border-green-200", children: "已部署" }
    case "rejected":
      return { className: "bg-red-100 text-red-800 border-red-200", children: "审核拒绝" }
    case "completed":
      return { variant: "secondary" as const, className: "bg-green-100 text-green-800", children: "已完成" }
    case "in-progress":
      return { variant: "secondary" as const, className: "bg-blue-100 text-blue-800", children: "进行中" }
    case "failed":
      return { variant: "destructive" as const, children: "失败" }
    default:
      return { variant: "outline" as const, children: "未知" }
  }
}

// 获取状态文本
export const getStatusText = (status: string): string => {
  switch (status) {
    case "submitted":
      return "已提交"
    case "code_pulling":
      return "拉取代码中"
    case "branch_created":
      return "分支已创建"
    case "ai_generating":
      return "AI生成代码中"
    case "test_ready":
      return "测试环境准备就绪"
    case "testing":
      return "测试中"
    case "test_completed":
      return "测试完成"
    case "code_pushed":
      return "代码已推送"
    case "under_review":
      return "管理员审核中"
    case "approved":
      return "审核通过"
    case "deployed":
      return "已部署"
    case "rejected":
      return "审核拒绝"
    case "completed":
      return "已完成"
    case "in-progress":
      return "进行中"
    case "failed":
      return "失败"
    default:
      return "未知"
  }
}

// 根据状态分类任务
export const categorizeTasksByStatus = (tasks: any[]) => {
  const completed = tasks.filter(task => 
    ['deployed', 'completed'].includes(task.status)
  )
  const inProgress = tasks.filter(task => 
    ['code_pulling', 'branch_created', 'ai_generating', 'test_ready', 'testing', 'test_completed', 'code_pushed', 'under_review', 'approved', 'in-progress'].includes(task.status)
  )
  const pending = tasks.filter(task => 
    ['submitted'].includes(task.status)
  )
  const failed = tasks.filter(task => 
    ['rejected', 'failed'].includes(task.status)
  )

  return { completed, inProgress, pending, failed }
}