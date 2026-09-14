import { type FormEvent, useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, LoaderCircle, LogIn, MessageCircleMore, ShieldCheck, UserRoundPlus, X } from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import type { MobileAuthIntent, RegistrationPayload } from '../lib/api'
import { USER_TYPES, type SahayakProfile, type UserType } from '../types/api'

type AuthModalProps = {
  auth: SahayakAuth
  isOpen: boolean
  onClose: () => void
  onVerified: (profile: SahayakProfile) => void
}

type RegistrationDraft = {
  full_name: string
  state: string
  district: string
  village_or_town: string
  address: string
  user_type: UserType | ''
  cooperative_role: string
}

const emptyRegistration: RegistrationDraft = {
  full_name: '',
  state: '',
  district: '',
  village_or_town: '',
  address: '',
  user_type: '',
  cooperative_role: '',
}

const userTypeLabels: Record<UserType, string> = {
  cooperative_member: 'Cooperative member',
  farmer: 'Farmer',
  pacs_member: 'PACS member',
  cooperative_official: 'Cooperative official',
  rural_stakeholder: 'Rural stakeholder',
  other: 'Other rural service user',
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
  const [step, setStep] = useState<'choice' | 'login' | 'register' | 'otp'>('choice')
  const [intent, setIntent] = useState<MobileAuthIntent | null>(null)
  const [mobile, setMobile] = useState('')
  const [registration, setRegistration] = useState<RegistrationDraft>(emptyRegistration)
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
    setRegistration(emptyRegistration)
    setOtp('')
    setError(null)
    setNotice(null)
    setIsSubmitting(false)
    setSecondsLeft(0)
  }, [isOpen])

  if (!isOpen) return null

  function chooseIntent(nextIntent: MobileAuthIntent): void {
    setIntent(nextIntent)
    setStep(nextIntent === 'register' ? 'register' : 'login')
    setError(null)
    setNotice(null)
  }

  function updateRegistration(field: keyof RegistrationDraft, value: string): void {
    setRegistration((current) => ({ ...current, [field]: value }))
  }

  function registrationPayload(): RegistrationPayload | null {
    const requiredFields = [
      registration.full_name,
      registration.state,
      registration.district,
      registration.village_or_town,
    ]
    if (requiredFields.some((field) => field.trim().length < 2) || !registration.user_type) return null
    return {
      full_name: registration.full_name.trim(),
      state: registration.state.trim(),
      district: registration.district.trim(),
      village_or_town: registration.village_or_town.trim(),
      user_type: registration.user_type,
      ...(registration.address.trim() ? { address: registration.address.trim() } : {}),
      ...(registration.cooperative_role.trim() ? { cooperative_role: registration.cooperative_role.trim() } : {}),
    }
  }

  async function requestOtp(activeIntent: MobileAuthIntent, event?: FormEvent<HTMLFormElement>): Promise<void> {
    event?.preventDefault()
    setError(null)
    setNotice(null)
    if (mobile.length !== 10) {
      setError('Enter your 10-digit mobile number.')
      return
    }
    setIsSubmitting(true)
    try {
      await auth.requestOtp(mobile, activeIntent)
      setIntent(activeIntent)
      setStep('otp')
      setSecondsLeft(30)
      setNotice('A 6-digit OTP has been sent to your mobile number.')
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'We could not send an OTP. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function continueRegistration(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!registrationPayload()) {
      setError('Complete your name, location and service role before continuing.')
      return
    }
    await requestOtp('register')
  }

  async function confirmOtp(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setError(null)
    const completedRegistration = intent === 'register' ? registrationPayload() : undefined
    if (!intent) {
      setStep('choice')
      return
    }
    if (intent === 'register' && !completedRegistration) {
      setStep('register')
      setError('Your profile details need to be completed before verification.')
      return
    }
    if (otp.length !== 6) {
      setError('Enter the 6-digit OTP.')
      return
    }
    setIsSubmitting(true)
    try {
      const profile = await auth.verifyOtp(mobile, otp, intent, completedRegistration ?? undefined)
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
        ) : step === 'login' ? (
          <>
            <button className="auth-modal__back" onClick={backToChoice} type="button"><ArrowLeft size={16} /> Back to options</button>
            <div className="auth-modal__intro">
              <p className="section-kicker">Log in</p>
              <h2 id="auth-title">Welcome back.</h2>
              <p>Use the mobile number linked to your Sahayak account.</p>
            </div>
            <form className="auth-form" onSubmit={(event) => void requestOtp('login', event)}>
              <IndianNumber onChange={setMobile} value={mobile} />
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Sending OTP…' : 'Continue to log in'}
              </button>
            </form>
          </>
        ) : step === 'register' ? (
          <>
            <button className="auth-modal__back" onClick={backToChoice} type="button"><ArrowLeft size={16} /> Back to options</button>
            <div className="auth-modal__intro auth-modal__intro--register">
              <p className="section-kicker">Create account · Step 1 of 2</p>
              <h2 id="auth-title">Tell us how Sahayak can support you.</h2>
              <p>Complete your profile now. Your account is created only after your mobile number is verified.</p>
            </div>
            <form className="auth-form auth-form--registration" onSubmit={(event) => void continueRegistration(event)}>
              <div className="auth-form__grid">
                <IndianNumber onChange={setMobile} value={mobile} />
                <label className="auth-text-field"><span>Full name</span><input autoComplete="name" onChange={(event) => updateRegistration('full_name', event.target.value)} placeholder="Your full name" required value={registration.full_name} /></label>
                <label className="auth-text-field"><span>State</span><input autoComplete="address-level1" onChange={(event) => updateRegistration('state', event.target.value)} placeholder="e.g. Maharashtra" required value={registration.state} /></label>
                <label className="auth-text-field"><span>District / city</span><input autoComplete="address-level2" onChange={(event) => updateRegistration('district', event.target.value)} placeholder="Your district or city" required value={registration.district} /></label>
                <label className="auth-text-field"><span>Village / town</span><input onChange={(event) => updateRegistration('village_or_town', event.target.value)} placeholder="Your village or town" required value={registration.village_or_town} /></label>
                <label className="auth-text-field"><span>How do you use Sahayak?</span><select onChange={(event) => updateRegistration('user_type', event.target.value)} required value={registration.user_type}><option value="">Choose your role</option>{USER_TYPES.map((type) => <option key={type} value={type}>{userTypeLabels[type]}</option>)}</select></label>
                <label className="auth-text-field"><span>Cooperative role <em>optional</em></span><input onChange={(event) => updateRegistration('cooperative_role', event.target.value)} placeholder="e.g. Secretary or member" value={registration.cooperative_role} /></label>
                <label className="auth-text-field"><span>Address <em>optional</em></span><input autoComplete="street-address" onChange={(event) => updateRegistration('address', event.target.value)} placeholder="House, street or landmark" value={registration.address} /></label>
              </div>
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Sending OTP…' : 'Continue to phone verification'}
              </button>
            </form>
          </>
        ) : (
          <>
            <button className="auth-modal__back" onClick={() => { setStep(intent === 'register' ? 'register' : 'login'); setError(null); setNotice(null) }} type="button"><ArrowLeft size={16} /> Edit your details</button>
            <div className="auth-modal__intro">
              <p className="section-kicker">Step 2 of 2 · Verify your number</p>
              <h2 id="auth-title">Enter the 6-digit OTP.</h2>
              <p>We sent it to +91 {mobile}. Once verified, your secure Sahayak account will be ready.</p>
            </div>
            <form className="auth-form" onSubmit={(event) => void confirmOtp(event)}>
              <label className="otp-field"><span>One-time password</span><input aria-label="6-digit one-time password" autoComplete="one-time-code" inputMode="numeric" maxLength={6} onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="••••••" required value={otp} /></label>
              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">{isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}{isSubmitting ? 'Verifying…' : intent === 'register' ? 'Verify and create account' : 'Verify and log in'}</button>
              <button className="text-action" disabled={secondsLeft > 0 || isSubmitting} onClick={() => intent && void requestOtp(intent)} type="button">{secondsLeft ? 'Resend OTP in ' + secondsLeft + 's' : 'Resend OTP'}</button>
            </form>
          </>
        )}

        {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
        {notice && <p className="form-feedback form-feedback--success" role="status">{notice}</p>}
        <footer className="auth-modal__footer"><ShieldCheck size={16} /> Your phone and profile are used only to provide your support services.</footer>
      </section>
    </div>
  )
}
