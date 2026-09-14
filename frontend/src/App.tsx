import { lazy, Suspense, useCallback, useEffect, useState } from 'react'

import { AccessGate } from './components/AccessGate'
import { AuthModal } from './components/AuthModal'
import { Onboarding } from './components/Onboarding'
import { Dashboard, DocumentsView, GrievancesView, NotificationsView, ProfileView, SchemesView } from './components/PortalViews'
import { SahayakHeader } from './components/SahayakHeader'
import { SahayakLanding } from './components/SahayakLanding'
import { useAuth } from './hooks/useAuth'
import type { SahayakProfile } from './types/api'
import { asAppRoute, type AppRoute } from './types/navigation'
import './App.css'

const PROTECTED_ROUTES: AppRoute[] = ['/dashboard', '/documents', '/schemes', '/grievances', '/notifications', '/profile', '/onboarding']
const VoiceExperience = lazy(() => import('./components/VoiceExperience'))

function App() {
  const [route, setRoute] = useState<AppRoute>(() => asAppRoute(window.location.pathname))
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const auth = useAuth()

  useEffect(() => {
    const onPopState = () => setRoute(asAppRoute(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const navigate = useCallback((nextRoute: AppRoute): void => {
    if (PROTECTED_ROUTES.includes(nextRoute) && !auth.user) {
      setIsAuthOpen(true)
      return
    }
    if (window.location.pathname !== nextRoute) window.history.pushState({}, '', nextRoute)
    setRoute(nextRoute)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [auth.user])

  const onVerified = useCallback((profile: SahayakProfile) => {
    navigate(profile.needs_onboarding ? '/onboarding' : '/dashboard')
  }, [navigate])

  async function logout(): Promise<void> {
    await auth.signOut()
    navigate('/')
  }

  let content: React.ReactNode
  if (auth.status === 'loading' && PROTECTED_ROUTES.includes(route)) {
    content = <main className="page-loader" aria-live="polite"><span className="loader-ring" /> Checking your secure session…</main>
  } else if (auth.user?.needs_onboarding && route !== '/onboarding' && route !== '/voice') {
    content = <Onboarding auth={auth} onComplete={() => navigate('/dashboard')} profile={auth.user} />
  } else {
    switch (route) {
      case '/voice':
        content = <Suspense fallback={<main className="page-loader"><span className="loader-ring" /> Opening voice assistant…</main>}><VoiceExperience /></Suspense>
        break
      case '/onboarding':
        content = auth.user ? <Onboarding auth={auth} onComplete={() => navigate('/dashboard')} profile={auth.user} /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Account setup" />
        break
      case '/dashboard':
        content = auth.user ? <Dashboard onNavigate={navigate} profile={auth.user} /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Services" />
        break
      case '/documents':
        content = auth.user ? <DocumentsView onTalk={() => navigate('/voice')} /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Documents" />
        break
      case '/schemes':
        content = auth.user ? <SchemesView onTalk={() => navigate('/voice')} /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Schemes" />
        break
      case '/grievances':
        content = auth.user ? <GrievancesView /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Grievance support" />
        break
      case '/notifications':
        content = auth.user ? <NotificationsView /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Notifications" />
        break
      case '/profile':
        content = auth.user ? <ProfileView auth={auth} profile={auth.user} /> : <AccessGate onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} title="Profile" />
        break
      default:
        content = <SahayakLanding onOpenAuth={() => setIsAuthOpen(true)} onTalk={() => navigate('/voice')} onViewServices={() => auth.user ? navigate('/dashboard') : setIsAuthOpen(true)} />
    }
  }

  return (
    <>
      <div className="app-shell">
        <SahayakHeader activeRoute={route} onNavigate={navigate} onOpenAuth={() => setIsAuthOpen(true)} onSignOut={logout} user={auth.user} />
        {content}
        <footer className="site-footer"><span>© Sahayak AI</span><span>Educational guidance, not legal or financial advice.</span><span>Available in 10 Indian languages.</span></footer>
      </div>
      <AuthModal auth={auth} isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} onVerified={onVerified} />
    </>
  )
}

export default App
