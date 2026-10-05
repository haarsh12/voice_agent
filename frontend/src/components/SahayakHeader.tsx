import { useState } from 'react'
import { Bell, ChevronDown, LogOut, Menu, MessageCircleMore, UserRound, X } from 'lucide-react'

import type { SahayakProfile } from '../types/api'
import type { AppRoute } from '../types/navigation'

type SahayakHeaderProps = {
  activeRoute: AppRoute
  onNavigate: (route: AppRoute) => void
  onOpenAuth: () => void
  onSignOut: () => Promise<void>
  user: SahayakProfile | null
}

const NAVIGATION: Array<{ label: string; route: AppRoute; protected?: boolean }> = [
  { label: 'Discover', route: '/' },
  { label: 'Ask Sahayak', route: '/voice' },
  { label: 'Services', route: '/dashboard' },
  { label: 'Schemes', route: '/schemes' },
  { label: 'Grievances', route: '/grievances', protected: true },
  { label: 'Knowledge Base', route: '/knowledge-base' },
  { label: 'Admin', route: '/admin' },
]

function nameFor(profile: SahayakProfile): string {
  return profile.full_name?.trim() || 'My profile'
}

export function SahayakHeader({ activeRoute, onNavigate, onOpenAuth, onSignOut, user }: SahayakHeaderProps) {
  const initial = user ? nameFor(user).slice(0, 1).toUpperCase() : ''
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleNavigate = (route: AppRoute) => {
    setIsMobileMenuOpen(false)
    onNavigate(route)
  }

  const handleAuthNavigate = (item: typeof NAVIGATION[number]) => {
    if (item.protected && !user) {
      setIsMobileMenuOpen(false)
      onOpenAuth()
    } else {
      handleNavigate(item.route)
    }
  }

  return (
    <>
      <header className="site-header">
        <button className="site-logo" onClick={() => handleNavigate('/')} type="button">
          <span className="site-logo__mark" aria-hidden="true"><MessageCircleMore size={20} /></span>
          <span>Sahayak AI</span>
        </button>
        <nav className="site-navigation" aria-label="Main navigation">
          {NAVIGATION.map((item) => (
            <button
              className={activeRoute === item.route ? 'is-active' : ''}
              key={item.route}
              onClick={() => handleAuthNavigate(item)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="site-header__account">
          {user ? (
            <>
              <button aria-label="Open notifications" className="header-icon-button" onClick={() => handleNavigate('/notifications')} type="button"><Bell size={18} /></button>
              <details className="account-menu">
                <summary>
                  <span className="account-menu__avatar" aria-hidden="true">{initial}</span>
                  <span className="account-menu__name">{nameFor(user).split(/\s+/)[0]}</span>
                  <ChevronDown size={15} aria-hidden="true" />
                </summary>
                <div className="account-menu__content">
                  <button onClick={() => handleNavigate('/profile')} type="button"><UserRound size={16} /> Profile</button>
                  <button onClick={() => void onSignOut()} type="button"><LogOut size={16} /> Log out</button>
                </div>
              </details>
            </>
          ) : (
            <button className="sign-in-button" onClick={onOpenAuth} type="button"><UserRound size={17} /> Sign in</button>
          )}
          <button 
            aria-label="Open menu" 
            className="mobile-menu-button" 
            onClick={() => setIsMobileMenuOpen(true)} 
            type="button"
          >
            <Menu size={20} />
          </button>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="mobile-menu-overlay" onClick={() => setIsMobileMenuOpen(false)}>
          <div className="mobile-menu" onClick={(e) => e.stopPropagation()}>
            <div className="mobile-menu__header">
              <span className="mobile-menu__title">Sahayak AI</span>
              <button 
                aria-label="Close menu" 
                className="mobile-menu__close" 
                onClick={() => setIsMobileMenuOpen(false)}
                type="button"
              >
                <X size={24} />
              </button>
            </div>
            <nav className="mobile-menu__nav">
              {NAVIGATION.map((item) => (
                <button
                  className={activeRoute === item.route ? 'is-active' : ''}
                  key={item.route}
                  onClick={() => handleAuthNavigate(item)}
                  type="button"
                >
                  {item.label}
                </button>
              ))}
            </nav>
            <div className="mobile-menu__footer">
              {user ? (
                <>
                  <button onClick={() => { setIsMobileMenuOpen(false); handleNavigate('/profile'); }} type="button">
                    <UserRound size={18} /> {nameFor(user)}
                  </button>
                  <button onClick={() => { setIsMobileMenuOpen(false); void onSignOut(); }} type="button">
                    <LogOut size={18} /> Log out
                  </button>
                </>
              ) : (
                <button onClick={() => { setIsMobileMenuOpen(false); onOpenAuth(); }} type="button">
                  <UserRound size={18} /> Sign in
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
