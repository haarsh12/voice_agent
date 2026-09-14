import { Bell, ChevronDown, LogOut, Menu, MessageCircleMore, UserRound } from 'lucide-react'

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
  { label: 'Services', route: '/dashboard', protected: true },
  { label: 'Schemes', route: '/schemes', protected: true },
]

function nameFor(profile: SahayakProfile): string {
  return profile.full_name?.trim() || 'My profile'
}

export function SahayakHeader({ activeRoute, onNavigate, onOpenAuth, onSignOut, user }: SahayakHeaderProps) {
  const initial = user ? nameFor(user).slice(0, 1).toUpperCase() : ''
  return (
    <header className="site-header">
      <button className="site-logo" onClick={() => onNavigate('/')} type="button">
        <span className="site-logo__mark" aria-hidden="true"><MessageCircleMore size={20} /></span>
        <span>Sahayak AI</span>
      </button>
      <nav className="site-navigation" aria-label="Main navigation">
        {NAVIGATION.map((item) => (
          <button
            className={activeRoute === item.route ? 'is-active' : ''}
            key={item.route}
            onClick={() => item.protected && !user ? onOpenAuth() : onNavigate(item.route)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="site-header__account">
        {user ? (
          <>
            <button aria-label="Open notifications" className="header-icon-button" onClick={() => onNavigate('/notifications')} type="button"><Bell size={18} /></button>
            <details className="account-menu">
              <summary>
                <span className="account-menu__avatar" aria-hidden="true">{initial}</span>
                <span className="account-menu__name">{nameFor(user).split(/\s+/)[0]}</span>
                <ChevronDown size={15} aria-hidden="true" />
              </summary>
              <div className="account-menu__content">
                <button onClick={() => onNavigate('/profile')} type="button"><UserRound size={16} /> Profile</button>
                <button onClick={() => void onSignOut()} type="button"><LogOut size={16} /> Log out</button>
              </div>
            </details>
          </>
        ) : (
          <button className="sign-in-button" onClick={onOpenAuth} type="button"><UserRound size={17} /> Sign in</button>
        )}
        <button aria-label="Open menu" className="mobile-menu-button" type="button"><Menu size={20} /></button>
      </div>
    </header>
  )
}
