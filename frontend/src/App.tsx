import React, { useState } from 'react'
import { Header } from '@/views/Header'
import { Footer } from '@/views/Footer'
import { LandingPage } from '@/views/LandingPage'
import { QueryWorkflow } from '@/views/QueryWorkflow'
import { TenderWorkflow } from '@/views/TenderWorkflow'

type View = 'landing' | 'query' | 'tender'

export function App() {
  const [currentView, setCurrentView] = useState<View>('landing')

  const handleNavigate = (view: View) => {
    setCurrentView(view)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header currentView={currentView} onNavigate={handleNavigate} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'landing' && (
          <LandingPage onNavigate={handleNavigate} />
        )}
        {currentView === 'query' && (
          <QueryWorkflow onBack={() => handleNavigate('landing')} />
        )}
        {currentView === 'tender' && (
          <TenderWorkflow onBack={() => handleNavigate('landing')} />
        )}
      </main>

      <Footer />
    </div>
  )
}

export default App
