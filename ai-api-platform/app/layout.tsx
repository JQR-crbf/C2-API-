import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Manrope } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { Toaster } from "sonner"
import { AuthProvider } from "@/contexts/AuthContext"
import { ErrorProvider } from "@/components/enhanced-error-handler"
import { FloatingHelpButton } from "@/components/help-system"
import { RealTimeFeedback } from "@/components/real-time-feedback"
import "./globals.css"
import { Suspense } from "react"
import ClientProviders from "./client-providers"

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
})

export const metadata: Metadata = {
  title: "AI API 开发平台",
  description: "使用自然语言创建API - 无需编程",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="zh-CN">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable} ${manrope.variable}`}>
        <ErrorProvider>
          <AuthProvider>
            <ClientProviders>
              <Suspense fallback={null}>{children}</Suspense>
              <Toaster position="top-right" richColors />
              <RealTimeFeedback position="top-right" showSystemStatus={false} maxMessages={3} />
              <FloatingHelpButton />
            </ClientProviders>
          </AuthProvider>
        </ErrorProvider>
        <Analytics />
      </body>
    </html>
  )
}
