import { type FormEvent, useEffect, useState } from 'react'
import { ArrowLeft, LoaderCircle, MessageCircleMore, ShieldCheck, X } from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import type { SahayakProfile } from '../types/api'

type AuthModalProps = {
  auth: SahayakAuth
  isOpen: boolean
  onClose: () => void
  onVerified: (profile: SahayakProfile) => void
}

function IndianNumber({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="mobile-field">
      <span>Mobile number</span>
      <div>
        <span className="mobile-field__prefix">+91</span>
        <input
          autoComplete="tel-national"
          inputMode="numeric"
          maxLength={10}
          onChange={(event) => onChange(event.target.value.replace(/\D/g, '').slice(0, 10))}
          placeholder="10-digit mobile number"
          required
          value={value}
        />
      </div>
    </label>
  )
}

export function AuthModal({ auth, isOpen, onClose, onVerified }: AuthModalProps) {
  const [step, setStep] = useState<'mobile' | 'otp'>('mobile')
  const [mobile, setMobile] = useState('')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)

  useEffect(() => {
    if (!secondsLeft) return
    const timer = window.setTimeout(() => setSecondsLeft((seconds) => seconds - 1), 1_000)
    return () => window.clearTimeout(timer)
  }, [secondsLeft])

  useEffect(() => {
    if (isOpen) return
    setStep('mobile')
    setOtp('')
    setError(null)
    setNotice(null)
    setIsSubmitting(false)
  }, [isOpen])

  if (!isOpen) return null

  async function sendOtp(event?: FormEvent<HTMLFormElement>): Promise<void> {
    event?.preventDefault()
    setError(null)
    setNotice(null)
    if (mobile.length !== 10) {
      setError('Enter your 10-digit mobile number.')
      return
    }
    setIsSubmitting(true)
    try {
      await auth.requestOtp(mobile)
      setStep('otp')
      setSecondsLeft(30)
      setNotice('An OTP has been sent to your mobile number.')
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'We could not send an OTP. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function confirmOtp(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setError(null)
    if (otp.length !== 6) {
      setError('Enter the 6-digit OTP.')
      return
    }
    setIsSubmitting(true)
    try {
      const profile = await auth.verifyOtp(mobile, otp)
      onVerified(profile)
      onClose()
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'We could not verify the OTP.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title">
      <button aria-label="Close sign in" className="auth-modal__backdrop" onClick={onClose} type="button" />
      <section className="auth-modal__card">
        <header className="auth-modal__header">
          <div className="auth-modal__brand">
            <span aria-hidden="true"><MessageCircleMore size={21} /></span>
            <b>Sahayak AI</b>
          </div>
          <button aria-label="Close sign in" className="icon-button" onClick={onClose} type="button"><X size={20} /></button>
        </header>

        {step === 'mobile' ? (
          <>
            <div className="auth-modal__intro">
              <p className="section-kicker">Sign in or register</p>
              <h2 id="auth-title">Your support starts here.</h2>
              <p>Use your mobile number to access your personal cooperative support space.</p>
            </div>
            <form className="auth-form" onSubmit={(event) => void sendOtp(event)}>
              <IndianNumber onChange={setMobile} value={mobile} />
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Sending OTP…' : 'Continue with mobile'}
              </button>
            </form>
          </>
        ) : (
          <>
            <button className="auth-modal__back" onClick={() => { setStep('mobile'); setError(null); setNotice(null) }} type="button">
              <ArrowLeft size={16} /> Change mobile number
            </button>
            <div className="auth-modal__intro">
              <p className="section-kicker">Verify your number</p>
              <h2 id="auth-title">Enter the 6-digit OTP.</h2>
              <p>We sent it to +91 {mobile}. For testing, use the OTP configured by the server.</p>
            </div>
            <form className="auth-form" onSubmit={(event) => void confirmOtp(event)}>
              <label className="otp-field">
                <span>One-time password</span>
                <input
                  aria-label="6-digit one-time password"
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  maxLength={6}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="••••••"
                  required
                  value={otp}
                />
              </label>
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Verifying…' : 'Verify and continue'}
              </button>
              <button className="text-action" disabled={secondsLeft > 0 || isSubmitting} onClick={() => void sendOtp()} type="button">
                {secondsLeft ? 'Resend OTP in ' + secondsLeft + 's' : 'Resend OTP'}
              </button>
            </form>
          </>
        )}

        {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
        {notice && <p className="form-feedback form-feedback--success" role="status">{notice}</p>}
        <footer className="auth-modal__footer"><ShieldCheck size={16} /> Your mobile number is used only to secure your account.</footer>
      </section>
    </div>
  )
}
