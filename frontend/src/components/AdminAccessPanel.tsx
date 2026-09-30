import { type FormEvent, useEffect, useState } from 'react'
import { LoaderCircle, LogOut, ShieldCheck } from 'lucide-react'

import { endAdminSession, getAdminSession, startAdminSession } from '../lib/api'

/** A deliberately small private area until administrator features are approved. */
export function AdminAccessPanel() {
  const [adminId, setAdminId] = useState('')
  const [password, setPassword] = useState('')
  const [authenticated, setAuthenticated] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void getAdminSession()
      .then((session) => {
        if (active) setAuthenticated(session.authenticated)
      })
      .catch(() => {
        // A missing private-session cookie is normal for a first visit.
      })
      .finally(() => {
        if (active) setIsChecking(false)
      })
    return () => { active = false }
  }, [])

  async function submitLogin(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      const session = await startAdminSession(adminId.trim(), password)
      setPassword('')
      setAuthenticated(session.authenticated)
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Administrator sign-in failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function logout(): Promise<void> {
    setError(null)
    try {
      await endAdminSession()
      setAuthenticated(false)
      setAdminId('')
      setPassword('')
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Administrator sign-out failed.')
    }
  }

  if (isChecking) {
    return <main className="page-loader"><LoaderCircle className="spin" size={20} /> Checking administrator session…</main>
  }

  if (authenticated) {
    return (
      <main className="admin-access-page">
        <section className="admin-access-card admin-access-card--authenticated" aria-labelledby="admin-access-title">
          <span className="admin-access-card__icon" aria-hidden="true"><ShieldCheck size={27} /></span>
          <p className="section-kicker">Private area</p>
          <h1 id="admin-access-title">Admin signed in</h1>
          <p>Administrator access is active. Private management tools will be added in a later approved release.</p>
          <button className="admin-logout-button" onClick={() => void logout()} type="button"><LogOut size={16} /> Sign out</button>
          {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
        </section>
      </main>
    )
  }

  return (
    <main className="admin-access-page">
      <section className="admin-access-card" aria-labelledby="admin-access-title">
        <span className="admin-access-card__icon" aria-hidden="true"><ShieldCheck size={27} /></span>
        <p className="section-kicker">Restricted area</p>
        <h1 id="admin-access-title">Administrator sign in</h1>
        <p>Use the separate administrator credentials to open the private area.</p>
        <form className="admin-login-form" onSubmit={(event) => void submitLogin(event)}>
          <label>
            Administrator ID
            <input autoComplete="username" maxLength={64} onChange={(event) => setAdminId(event.target.value)} required value={adminId} />
          </label>
          <label>
            Password
            <input autoComplete="current-password" maxLength={256} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
          <button className="primary-action" disabled={isSubmitting} type="submit">
            {isSubmitting ? <LoaderCircle className="spin" size={18} /> : <ShieldCheck size={18} />}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
        <p className="admin-access-card__note">Knowledge sources and public update records are available in Knowledge Base. Private configuration remains protected.</p>
      </section>
    </main>
  )
}
