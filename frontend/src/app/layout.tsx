import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SmartCanopy - Urban Tree Planting AI',
  description: 'AI-powered urban tree planting recommendations for healthier cities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
