'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { 
  HelpCircle, 
  Search, 
  BookOpen, 
  MessageCircle, 
  ExternalLink,
  ChevronRight,
  Star,
  ThumbsUp,
  ThumbsDown,
  Send,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  Clock,
  User,
  Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'

// 帮助文档类型
interface HelpArticle {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimatedTime: number // 分钟
  lastUpdated: Date
  helpful: number
  notHelpful: number
}

// FAQ类型
interface FAQ {
  id: string
  question: string
  answer: string
  category: string
  popularity: number
}

// 快速指南类型
interface QuickGuide {
  id: string
  title: string
  description: string
  steps: {
    title: string
    description: string
    action?: string
  }[]
  category: string
}

// 模拟数据
const helpArticles: HelpArticle[] = [
  {
    id: '1',
    title: '如何创建第一个API任务',
    content: `# 创建第一个API任务

## 步骤1：登录系统
首先确保您已经登录到AI API开发平台。

## 步骤2：进入任务页面
点击左侧导航栏的"任务管理"进入任务列表页面。

## 步骤3：创建新任务
1. 点击"创建新任务"按钮
2. 填写任务基本信息：
   - 任务名称：简洁明了的名称
   - 任务描述：详细描述您想要实现的功能
   - 编程语言：选择Python、Node.js等
   - 框架：选择FastAPI、Express等
   - 数据库：选择MySQL、PostgreSQL等

## 步骤4：提交任务
确认信息无误后，点击"提交任务"按钮。系统将自动开始处理您的任务。

## 注意事项
- 任务描述越详细，生成的代码质量越高
- 建议先从简单的功能开始
- 可以随时查看任务进度和日志`,
    category: '入门指南',
    tags: ['新手', '任务创建', 'API'],
    difficulty: 'beginner',
    estimatedTime: 5,
    lastUpdated: new Date('2024-01-15'),
    helpful: 45,
    notHelpful: 3
  },
  {
    id: '2',
    title: '理解工作流程引擎',
    content: `# 工作流程引擎详解

## 什么是工作流程引擎
工作流程引擎是平台的核心功能，它将API开发过程分解为15个标准化步骤。

## 工作流程步骤
1. **需求分析** - 分析用户需求
2. **技术选型** - 选择合适的技术栈
3. **架构设计** - 设计系统架构
4. **数据库设计** - 设计数据模型
5. **API设计** - 设计接口规范
6. **代码生成** - AI生成代码
7. **代码审查** - 自动代码审查
8. **单元测试** - 生成和运行测试
9. **集成测试** - API集成测试
10. **部署准备** - 准备部署环境
11. **部署执行** - 部署到测试环境
12. **功能测试** - 功能验证测试
13. **性能测试** - 性能基准测试
14. **安全测试** - 安全漏洞扫描
15. **交付确认** - 最终交付确认

## 如何使用
- 每个步骤都有明确的输入和输出
- 可以暂停和恢复工作流程
- 支持自定义步骤配置
- 提供实时进度跟踪`,
    category: '核心功能',
    tags: ['工作流', '引擎', '步骤'],
    difficulty: 'intermediate',
    estimatedTime: 10,
    lastUpdated: new Date('2024-01-20'),
    helpful: 32,
    notHelpful: 2
  },
  {
    id: '3',
    title: 'Git集成使用指南',
    content: `# Git集成功能

## 功能概述
平台集成了完整的Git工作流，支持自动化的代码管理。

## 主要功能
- **自动分支管理** - 为每个任务创建独立分支
- **代码提交** - 自动提交生成的代码
- **推送到远程** - 推送到GitHub/GitLab
- **Pull Request** - 自动创建PR

## 配置步骤
1. 在设置页面配置Git仓库信息
2. 添加SSH密钥或访问令牌
3. 选择默认分支策略
4. 配置提交信息模板

## 最佳实践
- 使用有意义的分支命名
- 定期同步远程仓库
- 及时处理合并冲突
- 保持提交历史清晰`,
    category: '版本控制',
    tags: ['Git', '版本控制', '分支'],
    difficulty: 'intermediate',
    estimatedTime: 8,
    lastUpdated: new Date('2024-01-18'),
    helpful: 28,
    notHelpful: 1
  }
]

const faqs: FAQ[] = [
  {
    id: '1',
    question: '为什么我的任务一直显示"处理中"状态？',
    answer: '任务处理时间取决于复杂度。简单任务通常在2-5分钟内完成，复杂任务可能需要10-15分钟。如果超过30分钟仍未完成，请检查网络连接或联系技术支持。',
    category: '任务管理',
    popularity: 95
  },
  {
    id: '2',
    question: '如何查看生成的代码？',
    answer: '在任务详情页面，点击"查看代码"按钮即可查看AI生成的完整代码。您也可以下载代码文件到本地进行进一步开发。',
    category: '代码查看',
    popularity: 87
  },
  {
    id: '3',
    question: '支持哪些编程语言和框架？',
    answer: '目前支持Python(FastAPI、Django、Flask)、Node.js(Express、Koa)、Java(Spring Boot)、Go(Gin、Echo)等主流技术栈。我们会持续添加更多支持。',
    category: '技术支持',
    popularity: 82
  },
  {
    id: '4',
    question: '如何修改已生成的代码？',
    answer: '您可以下载代码后在本地修改，或者创建新任务来生成改进版本。我们建议使用Git版本控制来管理代码变更。',
    category: '代码修改',
    popularity: 76
  },
  {
    id: '5',
    question: '测试功能如何使用？',
    answer: '平台提供自动化测试功能，包括语法检查、单元测试、API测试和性能测试。在任务完成后，点击"运行测试"即可执行全套测试。',
    category: '测试',
    popularity: 71
  }
]

const quickGuides: QuickGuide[] = [
  {
    id: '1',
    title: '5分钟快速上手',
    description: '快速了解平台基本功能，创建您的第一个API',
    steps: [
      { title: '注册登录', description: '使用邮箱注册账号并登录系统' },
      { title: '创建任务', description: '点击"创建新任务"，填写基本信息' },
      { title: '等待处理', description: '系统自动处理任务，生成API代码' },
      { title: '查看结果', description: '查看生成的代码和测试结果' },
      { title: '下载部署', description: '下载代码并部署到您的环境' }
    ],
    category: '快速开始'
  },
  {
    id: '2',
    title: '配置Git集成',
    description: '设置Git仓库，实现代码自动管理',
    steps: [
      { title: '进入设置', description: '点击右上角头像，选择"设置"' },
      { title: '配置Git', description: '在"Git设置"中添加仓库信息' },
      { title: '添加密钥', description: '配置SSH密钥或访问令牌' },
      { title: '测试连接', description: '点击"测试连接"验证配置' },
      { title: '启用自动推送', description: '开启任务完成后自动推送功能' }
    ],
    category: '高级功能'
  }
]

// 帮助系统主组件
export function HelpSystem() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [filteredArticles, setFilteredArticles] = useState(helpArticles)
  const [filteredFAQs, setFilteredFAQs] = useState(faqs)

  // 搜索和过滤
  useEffect(() => {
    let filtered = helpArticles
    
    if (searchQuery) {
      filtered = filtered.filter(article => 
        article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(article => article.category === selectedCategory)
    }
    
    setFilteredArticles(filtered)
    
    // 过滤FAQ
    let filteredFAQList = faqs
    if (searchQuery) {
      filteredFAQList = filteredFAQList.filter(faq =>
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }
    setFilteredFAQs(filteredFAQList)
  }, [searchQuery, selectedCategory])

  const categories = ['all', ...Array.from(new Set(helpArticles.map(a => a.category)))]

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <HelpCircle className="h-4 w-4 mr-2" />
          帮助
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            帮助中心
          </DialogTitle>
          <DialogDescription>
            查找答案、学习功能使用方法，或获取技术支持
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* 搜索栏 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索帮助文档、FAQ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Tabs defaultValue="guides" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="guides">快速指南</TabsTrigger>
              <TabsTrigger value="articles">帮助文档</TabsTrigger>
              <TabsTrigger value="faq">常见问题</TabsTrigger>
              <TabsTrigger value="contact">联系支持</TabsTrigger>
            </TabsList>
            
            {/* 快速指南 */}
            <TabsContent value="guides" className="space-y-4">
              <ScrollArea className="h-[400px]">
                <div className="grid gap-4">
                  {quickGuides.map(guide => (
                    <QuickGuideCard key={guide.id} guide={guide} />
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
            
            {/* 帮助文档 */}
            <TabsContent value="articles" className="space-y-4">
              {/* 分类过滤 */}
              <div className="flex gap-2 flex-wrap">
                {categories.map(category => (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category === 'all' ? '全部' : category}
                  </Button>
                ))}
              </div>
              
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  {filteredArticles.map(article => (
                    <ArticleCard key={article.id} article={article} />
                  ))}
                  {filteredArticles.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>没有找到相关文档</p>
                      <p className="text-sm">尝试调整搜索关键词或分类</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
            
            {/* 常见问题 */}
            <TabsContent value="faq" className="space-y-4">
              <ScrollArea className="h-[400px]">
                <Accordion type="single" collapsible className="w-full">
                  {filteredFAQs.map(faq => (
                    <AccordionItem key={faq.id} value={faq.id}>
                      <AccordionTrigger className="text-left">
                        <div className="flex items-center gap-2">
                          <span>{faq.question}</span>
                          <Badge variant="secondary" className="text-xs">
                            {faq.popularity}% 有用
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="pt-2">
                          <p className="text-sm text-muted-foreground mb-3">{faq.answer}</p>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">这个答案有用吗？</span>
                            <Button variant="ghost" size="sm" className="h-6 px-2">
                              <ThumbsUp className="h-3 w-3" />
                            </Button>
                            <Button variant="ghost" size="sm" className="h-6 px-2">
                              <ThumbsDown className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
                {filteredFAQs.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>没有找到相关问题</p>
                    <p className="text-sm">尝试调整搜索关键词</p>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
            
            {/* 联系支持 */}
            <TabsContent value="contact" className="space-y-4">
              <ContactSupport />
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// 快速指南卡片
function QuickGuideCard({ guide }: { guide: QuickGuide }) {
  const [currentStep, setCurrentStep] = useState(0)
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          {guide.title}
        </CardTitle>
        <CardDescription>{guide.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {guide.steps.map((step, index) => (
            <div
              key={index}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg transition-colors",
                index === currentStep ? "bg-primary/10 border border-primary/20" : "bg-muted/50",
                index < currentStep ? "opacity-60" : ""
              )}
            >
              <div className={cn(
                "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                index < currentStep ? "bg-green-500 text-white" :
                index === currentStep ? "bg-primary text-primary-foreground" :
                "bg-muted text-muted-foreground"
              )}>
                {index < currentStep ? <CheckCircle className="h-3 w-3" /> : index + 1}
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-sm">{step.title}</h4>
                <p className="text-xs text-muted-foreground mt-1">{step.description}</p>
              </div>
            </div>
          ))}
          
          <div className="flex justify-between pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
            >
              上一步
            </Button>
            <Button
              size="sm"
              onClick={() => setCurrentStep(Math.min(guide.steps.length - 1, currentStep + 1))}
              disabled={currentStep === guide.steps.length - 1}
            >
              下一步
              <ChevronRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// 文档卡片
function ArticleCard({ article }: { article: HelpArticle }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{article.title}</CardTitle>
            <div className="flex items-center gap-2 mt-2">
              <Badge className={getDifficultyColor(article.difficulty)}>
                {article.difficulty === 'beginner' ? '初级' :
                 article.difficulty === 'intermediate' ? '中级' : '高级'}
              </Badge>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {article.estimatedTime} 分钟
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Star className="h-3 w-3" />
                {article.helpful} 有用
              </div>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          {article.tags.map(tag => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {isExpanded ? (
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-sm">{article.content}</pre>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {article.content.split('\n')[0]}
            </p>
          )}
          
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? '收起' : '展开阅读'}
              <ChevronRight className={cn(
                "h-3 w-3 ml-1 transition-transform",
                isExpanded ? "rotate-90" : ""
              )} />
            </Button>
            
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="h-6 px-2">
                <ThumbsUp className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="sm" className="h-6 px-2">
                <ThumbsDown className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// 联系支持组件
function ContactSupport() {
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [category, setCategory] = useState('general')
  
  const supportCategories = [
    { value: 'general', label: '一般咨询' },
    { value: 'technical', label: '技术问题' },
    { value: 'billing', label: '账单问题' },
    { value: 'feature', label: '功能建议' },
    { value: 'bug', label: '错误报告' }
  ]
  
  return (
    <div className="space-y-6">
      {/* 联系方式 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageCircle className="h-4 w-4" />
              在线客服
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              工作时间：周一至周五 9:00-18:00
            </p>
            <Button className="w-full">
              <MessageCircle className="h-4 w-4 mr-2" />
              开始对话
            </Button>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ExternalLink className="h-4 w-4" />
              社区论坛
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              与其他开发者交流经验
            </p>
            <Button variant="outline" className="w-full">
              <ExternalLink className="h-4 w-4 mr-2" />
              访问论坛
            </Button>
          </CardContent>
        </Card>
      </div>
      
      {/* 提交工单 */}
      <Card>
        <CardHeader>
          <CardTitle>提交支持工单</CardTitle>
          <CardDescription>
            详细描述您遇到的问题，我们会尽快回复
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">邮箱地址</label>
              <Input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">问题类型</label>
              <select
                className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {supportCategories.map(cat => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div>
            <label className="text-sm font-medium mb-2 block">问题描述</label>
            <textarea
              className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm min-h-[100px]"
              placeholder="请详细描述您遇到的问题..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          
          <Button className="w-full">
            <Send className="h-4 w-4 mr-2" />
            提交工单
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

// 浮动帮助按钮
export function FloatingHelpButton() {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <HelpSystem />
    </div>
  )
}