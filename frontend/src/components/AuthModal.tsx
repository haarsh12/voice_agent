import { type FormEvent, useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, LoaderCircle, LogIn, MessageCircleMore, ShieldCheck, UserRoundPlus, X } from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import type { MobileAuthIntent } from '../lib/api'
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
          aria-describedby="mobile-number-hint"
          autoComplete="tel-national"
          inputMode="numeric"
          maxLength={10}
          onChange={(event) => onChange(event.target.value.replace(/\D/g, '').slice(0, 10))}
          placeholder="Enter your 10-digit number"
          required
          value={value}
        />
      </div>
      <small id="mobile-number-hint">We use this only to secure your Sahayak account.</small>
    </label>
  )
}

export function AuthModal({ auth, isOpen, onClose, onVerified }: AuthModalProps) {
  const [step, setStep] = useState<'choice' | 'mobile' | 'otp'>('choice')
  const [intent, setIntent] = useState<MobileAuthIntent | null>(null)
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
    setStep('choice')
    setIntent(null)
    setMobile('')
    setOtp('')
    setError(null)
    setNotice(null)
    setIsSubmitting(false)
    setSecondsLeft(0)
  }, [isOpen])

  if (!isOpen) return null

  const accountCopy = intent === 'register'
    ? {
        kicker: 'Create account',
        title: 'Create your Sahayak account.',
        description: 'Start with your mobile number, then set up your cooperative support profile.',
        button: 'Create account with mobile',
      }
    : {
        kicker: 'Log in',
        title: 'Welcome back.',
        description: 'Use the mobile number linked to your Sahayak account.',
        button: 'Continue to log in',
      }

  function chooseIntent(nextIntent: MobileAuthIntent): void {
    setIntent(nextIntent)
    setStep('mobile')
    setError(null)
    setNotice(null)
  }

  async function sendOtp(event?: FormEvent<HTMLFormElement>): Promise<void> {
    event?.preventDefault()
    setError(null)
    setNotice(null)
    if (!intent) {
      setStep('choice')
      return
    }
    if (mobile.length !== 10) {
      setError('Enter your 10-digit mobile number.')
      return
    }
    setIsSubmitting(true)
    try {
      await auth.requestOtp(mobile, intent)
      setStep('otp')
      setSecondsLeft(30)
      setNotice('A 6-digit OTP has been sent to your mobile number.')
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

  function backToChoice(): void {
    setStep('choice')
    setIntent(null)
    setOtp('')
    setError(null)
    setNotice(null)
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

        {step === 'choice' ? (
          <>
            <div className="auth-modal__intro auth-modal__intro--choice">
              <p className="section-kicker">Personal support space</p>
              <h2 id="auth-title">How would you like to continue?</h2>
              <p>Choose an option to securely access your cooperative services, documents and updates.</p>
            </div>
            <div className="auth-choice-grid">
              <button className="auth-choice" onClick={() => chooseIntent('login')} type="button">
                <span className="auth-choice__icon"><LogIn size={19} /></span>
                <span><b>Log in</b><small>I already have a Sahayak account</small></span>
                <ArrowRight aria-hidden="true" size={18} />
              </button>
              <button className="auth-choice" onClick={() => chooseIntent('register')} type="button">
                <span className="auth-choice__icon auth-choice__icon--accent"><UserRoundPlus size={19} /></span>
                <span><b>Create account</b><small>I’m new to Sahayak AI</small></span>
                <ArrowRight aria-hidden="true" size={18} />
              </button>
            </div>
          </>
        ) : step === 'mobile' ? (
          <>
            <button className="auth-modal__back" onClick={backToChoice} type="button">
              <ArrowLeft size={16} /> Back to options
            </button>
            <div className="auth-modal__intro">
              <p className="section-kicker">{accountCopy.kicker}</p>
              <h2 id="auth-title">{accountCopy.title}</h2>
              <p>{accountCopy.description}</p>
            </div>
            <form className="auth-form" onSubmit={(event) => void sendOtp(event)}>
              <IndianNumber onChange={setMobile} value={mobile} />
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Sending OTP…' : accountCopy.button}
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
              <p>We sent it to +91 {mobile}. Check your messages, then enter the code below.</p>
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
