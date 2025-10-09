# Vercel 部署配置说明

## 📋 Vercel 项目设置

由于项目前端代码在 `ai-api-platform` 子目录中，需要进行特殊配置。

### 方法一：通过 Vercel Dashboard 配置（推荐）

这是最简单的方法：

1. **导入项目**
   - 在 Vercel Dashboard 点击 "Add New Project"
   - 导入你的 Git 仓库

2. **关键配置**
   
   在配置页面设置：
   
   ```
   Framework Preset: Next.js
   Root Directory: ai-api-platform  ⚠️ 重要！
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   Node.js Version: 18.x
   ```

3. **环境变量**
   
   添加以下环境变量：
   
   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `NEXT_PUBLIC_API_URL` | `https://your-backend.railway.app` | 后端API地址 |
   | `NODE_ENV` | `production` | 环境标识 |

4. **部署**
   - 点击 "Deploy"
   - 等待构建完成

### 方法二：使用 vercel.json 配置

项目根目录已经包含 `vercel.json` 配置文件，会自动被 Vercel 识别。

配置内容：
```json
{
  "version": 2,
  "buildCommand": "cd ai-api-platform && npm run build",
  "devCommand": "cd ai-api-platform && npm run dev",
  "installCommand": "cd ai-api-platform && npm install",
  "outputDirectory": "ai-api-platform/.next"
}
```

### 方法三：移动前端到根目录（不推荐）

如果上述方法都不行，可以：

1. 将 `ai-api-platform` 目录下的所有文件移到项目根目录
2. 更新 `.gitignore`
3. 重新部署

但这会改变项目结构，**不推荐使用**。

---

## 🔧 高级配置

### 自定义域名

1. **在 Vercel 项目中**
   - Settings → Domains
   - 添加你的域名

2. **配置 DNS**
   
   在你的域名服务商添加以下记录：
   
   **使用 A 记录**：
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   ```
   
   **使用 CNAME 记录**（推荐）：
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

3. **配置 SSL**
   - Vercel 会自动配置 Let's Encrypt SSL 证书
   - 通常在 DNS 生效后几分钟内完成

### 部署预览

Vercel 会为每个 Pull Request 自动创建预览部署：

- 每个 PR 都有唯一的预览 URL
- 可以在合并前测试变更
- 预览环境使用相同的环境变量

### 生产环境和预览环境分离

如果需要为预览环境使用不同的后端：

1. **添加环境变量**
   - `NEXT_PUBLIC_API_URL` (Production)
   - `NEXT_PUBLIC_API_URL_PREVIEW` (Preview)

2. **修改代码**
   ```typescript
   const API_BASE_URL = process.env.VERCEL_ENV === 'production'
     ? process.env.NEXT_PUBLIC_API_URL
     : process.env.NEXT_PUBLIC_API_URL_PREVIEW || process.env.NEXT_PUBLIC_API_URL
   ```

---

## 🚨 常见问题

### 问题 1: Build 失败 - "Cannot find module"

**错误信息**：
```
Error: Cannot find module './components/...'
```

**原因**：
- TypeScript 路径解析问题
- 依赖安装失败

**解决**：
1. 检查 `tsconfig.json` 的 paths 配置
2. 确认所有导入路径正确
3. 清除缓存重新部署

### 问题 2: 部署成功但页面 404

**原因**：
- Root Directory 配置错误

**解决**：
1. 检查 Root Directory 设置为 `ai-api-platform`
2. 确认 `package.json` 在正确位置
3. 查看部署日志确认构建路径

### 问题 3: 环境变量不生效

**症状**：
- `process.env.NEXT_PUBLIC_API_URL` 为 undefined
- API 请求失败

**解决**：
1. 确认环境变量名以 `NEXT_PUBLIC_` 开头
2. 重新部署（环境变量修改后需要重新部署）
3. 检查构建日志中的环境变量值

### 问题 4: API 请求被 CORS 阻止

**错误信息**：
```
Access to fetch at '...' has been blocked by CORS policy
```

**解决**：
1. 在后端环境变量中添加 Vercel 域名：
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
2. 确认后端已重新部署
3. 清除浏览器缓存

### 问题 5: 构建超时

**错误信息**：
```
Build exceeded maximum time limit
```

**原因**：
- 依赖安装时间过长
- 构建过程耗时

**解决**：
1. 优化依赖（移除不必要的包）
2. 使用 `npm ci` 而不是 `npm install`
3. 升级到 Vercel Pro（有更长的构建时间）

---

## 📊 性能优化

### 启用 Edge Runtime

对于某些页面，可以使用 Edge Runtime 提升性能：

```typescript
// app/page.tsx
export const runtime = 'edge'
```

### 图片优化

Next.js 的 Image 组件会自动优化图片：

```typescript
import Image from 'next/image'

<Image 
  src="/image.jpg" 
  alt="Description" 
  width={500} 
  height={300}
/>
```

### 代码分割

Next.js 自动进行代码分割，但可以进一步优化：

```typescript
// 动态导入
const DynamicComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
})
```

---

## 🔒 安全设置

### 环境变量安全

- ✅ **公开变量**：使用 `NEXT_PUBLIC_` 前缀
- ❌ **私密变量**：不要使用 `NEXT_PUBLIC_` 前缀
- ⚠️ **注意**：`NEXT_PUBLIC_` 的变量会打包到客户端代码中

### 安全头部

Vercel 自动添加安全头部，但可以自定义：

```javascript
// next.config.mjs
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'X-Frame-Options',
          value: 'DENY',
        },
        {
          key: 'X-Content-Type-Options',
          value: 'nosniff',
        },
        {
          key: 'Referrer-Policy',
          value: 'origin-when-cross-origin',
        },
      ],
    },
  ]
}
```

---

## 📈 监控和分析

### Vercel Analytics

启用 Vercel Analytics：

1. 安装包：
   ```bash
   npm install @vercel/analytics
   ```

2. 在 `app/layout.tsx` 中添加：
   ```typescript
   import { Analytics } from '@vercel/analytics/react'
   
   export default function RootLayout({ children }) {
     return (
       <html>
         <body>
           {children}
           <Analytics />
         </body>
       </html>
     )
   ```

### 日志查看

- **部署日志**：Dashboard → Deployments → 选择部署 → Logs
- **实时日志**：Dashboard → Logs（需要 Pro 套餐）
- **错误追踪**：集成 Sentry 等服务

---

## 🔄 回滚部署

如果新部署有问题，可以快速回滚：

1. 进入 Vercel Dashboard → Deployments
2. 找到之前正常的部署
3. 点击 "Promote to Production"

---

## 💡 最佳实践

1. **使用 Git 分支**
   - `main/master`: 生产环境
   - `develop`: 开发环境
   - `feature/*`: 功能分支

2. **环境变量管理**
   - 本地开发：`.env.local`
   - 生产环境：Vercel Dashboard
   - 不要提交 `.env` 文件到 Git

3. **性能监控**
   - 启用 Vercel Analytics
   - 定期检查 Lighthouse 分数
   - 监控 Core Web Vitals

4. **安全检查**
   - 定期更新依赖：`npm audit`
   - 不要在客户端暴露敏感信息
   - 使用环境变量管理密钥

---

## 📚 相关资源

- [Vercel 官方文档](https://vercel.com/docs)
- [Next.js 官方文档](https://nextjs.org/docs)
- [Vercel CLI 文档](https://vercel.com/docs/cli)
- [部署故障排除](https://vercel.com/docs/concepts/deployments/troubleshoot-a-build)

---

**需要帮助？** 查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 或 Vercel 支持
