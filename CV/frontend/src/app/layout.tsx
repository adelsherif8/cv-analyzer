import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
})

export const metadata: Metadata = {
  title: 'CV Analyzer (MVP)',
  description: 'AI-powered CV analysis for HR teams',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">
        <header className="bg-white border-b">
          <div className="mx-auto px-4 py-4 container">
            <h1 className="font-bold text-gray-900 text-xl">
              CV Analyzer (MVP)
            </h1>
          </div>
        </header>
        <main className="bg-gray-50 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
