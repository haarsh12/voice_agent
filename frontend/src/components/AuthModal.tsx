import { type FormEvent, useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Fingerprint, LoaderCircle, LogIn, MapPin, MessageCircleMore, ShieldCheck, UserRoundPlus, X } from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import type { MobileAuthIntent, RegistrationPayload } from '../lib/api'
import { biometricErrorMessage, supportsDeviceBiometrics } from '../lib/webauthn'
import { CASTE_CATEGORIES, CASTE_CATEGORY_LABELS, USER_TYPES, type CasteCategory, type SahayakProfile, type UserType } from '../types/api'
import { getAllStateNames, getDistrictsByState } from '../data/indiaStatesDistricts'

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
  pincode: string
  caste_category: CasteCategory | ''
  user_type: UserType | ''
  cooperative_role: string
}

const emptyRegistration: RegistrationDraft = {
  full_name: '',
  state: '',
  district: '',
  village_or_town: '',
  address: '',
  pincode: '',
  caste_category: '',
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

const ALL_STATES = getAllStateNames()

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
  const [step, setStep] = useState<'choice' | 'login' | 'register' | 'otp' | 'face-id'>('choice')
  const [intent, setIntent] = useState<MobileAuthIntent | null>(null)
  const [mobile, setMobile] = useState('')
  const [registration, setRegistration] = useState<RegistrationDraft>(emptyRegistration)
  const [otp, setOtp] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [verifiedProfile, setVerifiedProfile] = useState<SahayakProfile | null>(null)
  const [deviceBiometricsAvailable, setDeviceBiometricsAvailable] = useState(false)

  // Districts available based on chosen state
  const availableDistricts = registration.state ? getDistrictsByState(registration.state) : []

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
    setVerifiedProfile(null)
  }, [isOpen])

  useEffect(() => {
    setDeviceBiometricsAvailable(supportsDeviceBiometrics())
  }, [isOpen])

  if (!isOpen) return null

  function chooseIntent(nextIntent: MobileAuthIntent): void {
    setIntent(nextIntent)
    setStep(nextIntent === 'register' ? 'register' : 'login')
    setError(null)
    setNotice(null)
  }

  function updateRegistration(field: keyof RegistrationDraft, value: string): void {
    setRegistration((current) => {
      const updated = { ...current, [field]: value }
      // Reset district when state changes
      if (field === 'state') {
        updated.district = ''
      }
      return updated
    })
  }

  function registrationPayload(): RegistrationPayload | null {
    const { full_name, state, district, village_or_town, address, pincode, caste_category, user_type } = registration

    // All fields are mandatory
    if (
      full_name.trim().length < 2 ||
      state.trim().length < 2 ||
      district.trim().length < 2 ||
      village_or_town.trim().length < 2 ||
      address.trim().length < 2 ||
      pincode.trim().length !== 6 ||
      !caste_category ||
      !user_type
    ) {
      return null
    }

    return {
      full_name: full_name.trim(),
      state: state.trim(),
      district: district.trim(),
      village_or_town: village_or_town.trim(),
      address: address.trim(),
      pincode: pincode.trim(),
      caste_category: caste_category as CasteCategory,
      user_type: user_type as UserType,
      ...(registration.cooperative_role.trim() ? { cooperative_role: registration.cooperative_role.trim() } : {}),
    }
  }

  function getMissingFields(): string[] {
    const missing: string[] = []
    const r = registration
    if (mobile.length !== 10) missing.push('mobile number')
    if (r.full_name.trim().length < 2) missing.push('full name')
    if (!r.state) missing.push('state')
    if (!r.district) missing.push('district')
    if (r.village_or_town.trim().length < 2) missing.push('village / town')
    if (r.address.trim().length < 2) missing.push('address')
    if (r.pincode.trim().length !== 6) missing.push('6-digit pincode')
    if (!r.caste_category) missing.push('caste category')
    if (!r.user_type) missing.push('how you use Sahayak')
    return missing
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
    const missing = getMissingFields()
    if (missing.length > 0) {
      setError(`Please fill in: ${missing.join(', ')}.`)
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
      if (intent === 'register' && deviceBiometricsAvailable) {
        setVerifiedProfile(profile)
        setStep('face-id')
        setNotice(null)
      } else {
        completeAccess(profile)
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'We could not verify the OTP.')
    } finally {
      setIsSubmitting(false)
    }
  }

  function completeAccess(profile: SahayakProfile): void {
    onVerified(profile)
    onClose()
  }

  async function setUpFaceId(): Promise<void> {
    setError(null)
    setNotice(null)
    setIsSubmitting(true)
    try {
      const profile = await auth.registerFaceId()
      completeAccess(profile)
    } catch (caughtError) {
      setError(biometricErrorMessage(caughtError, 'We could not set up Face ID. You can try again or skip it for now.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function signInWithFaceId(): Promise<void> {
    setError(null)
    setNotice(null)
    setIsSubmitting(true)
    try {
      const profile = await auth.signInWithFaceId()
      completeAccess(profile)
    } catch (caughtError) {
      setError(biometricErrorMessage(caughtError, 'Face ID sign-in was not completed. You can use mobile OTP instead.'))
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
                <span><b>Create account</b><small>I'm new to Sahayak AI</small></span>
                <ArrowRight aria-hidden="true" size={18} />
              </button>
              {deviceBiometricsAvailable && (
                <button className="auth-choice auth-choice--face" disabled={isSubmitting} onClick={() => void signInWithFaceId()} type="button">
                  <span className="auth-choice__icon auth-choice__icon--face"><Fingerprint size={20} /></span>
                  <span><b>Sign in with Face ID</b><small>Use Face ID, Touch ID, or your device screen lock</small></span>
                  {isSubmitting ? <LoaderCircle className="spin" size={18} /> : <ArrowRight aria-hidden="true" size={18} />}
                </button>
              )}
            </div>
            {!deviceBiometricsAvailable && <p className="auth-biometric-note">Face ID is available on a supported device through a secure HTTPS connection.</p>}
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
              {deviceBiometricsAvailable && (
                <>
                  <p className="auth-divider"><span />or<span /></p>
                  <button className="secondary-action auth-form__submit auth-face-button" disabled={isSubmitting} onClick={() => void signInWithFaceId()} type="button"><Fingerprint size={18} /> Sign in with Face ID</button>
                </>
              )}
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

                {/* Mobile number */}
                <IndianNumber onChange={setMobile} value={mobile} />

                {/* Full name */}
                <label className="auth-text-field auth-text-field--full">
                  <span>Full name <em aria-hidden="true" className="required-mark">*</em></span>
                  <input
                    autoComplete="name"
                    onChange={(event) => updateRegistration('full_name', event.target.value)}
                    placeholder="Your full name"
                    required
                    value={registration.full_name}
                  />
                </label>

                {/* State dropdown */}
                <label className="auth-text-field">
                  <span>State <em aria-hidden="true" className="required-mark">*</em></span>
                  <select
                    onChange={(event) => updateRegistration('state', event.target.value)}
                    required
                    value={registration.state}
                  >
                    <option value="">Select your state</option>
                    {ALL_STATES.map((state) => (
                      <option key={state} value={state}>{state}</option>
                    ))}
                  </select>
                </label>

                {/* District dropdown — only enabled after state is chosen */}
                <label className="auth-text-field">
                  <span>District <em aria-hidden="true" className="required-mark">*</em></span>
                  <select
                    disabled={!registration.state}
                    onChange={(event) => updateRegistration('district', event.target.value)}
                    required
                    value={registration.district}
                  >
                    <option value="">{registration.state ? 'Select your district' : 'Select state first'}</option>
                    {availableDistricts.map((district) => (
                      <option key={district} value={district}>{district}</option>
                    ))}
                  </select>
                </label>

                {/* Village / Town / City — typed */}
                <label className="auth-text-field">
                  <span>Village / Town / City <em aria-hidden="true" className="required-mark">*</em></span>
                  <input
                    onChange={(event) => updateRegistration('village_or_town', event.target.value)}
                    placeholder="Your village, town or city"
                    required
                    value={registration.village_or_town}
                  />
                </label>

                {/* Pincode */}
                <label className="auth-text-field">
                  <span>Pincode <em aria-hidden="true" className="required-mark">*</em></span>
                  <input
                    inputMode="numeric"
                    maxLength={6}
                    onChange={(event) => updateRegistration('pincode', event.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="6-digit pincode"
                    pattern="\d{6}"
                    required
                    value={registration.pincode}
                  />
                </label>

                {/* Address — typed, mandatory */}
                <label className="auth-text-field auth-text-field--full">
                  <span>Address <em aria-hidden="true" className="required-mark">*</em></span>
                  <input
                    autoComplete="street-address"
                    onChange={(event) => updateRegistration('address', event.target.value)}
                    placeholder="House number, street, landmark"
                    required
                    value={registration.address}
                  />
                </label>

                {/* Caste category dropdown */}
                <label className="auth-text-field">
                  <span>Caste category <em aria-hidden="true" className="required-mark">*</em></span>
                  <select
                    onChange={(event) => updateRegistration('caste_category', event.target.value)}
                    required
                    value={registration.caste_category}
                  >
                    <option value="">Select your category</option>
                    {CASTE_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>{CASTE_CATEGORY_LABELS[cat]}</option>
                    ))}
                  </select>
                </label>

                {/* How do you use Sahayak */}
                <label className="auth-text-field">
                  <span>How do you use Sahayak? <em aria-hidden="true" className="required-mark">*</em></span>
                  <select
                    onChange={(event) => updateRegistration('user_type', event.target.value)}
                    required
                    value={registration.user_type}
                  >
                    <option value="">Choose your role</option>
                    {USER_TYPES.map((type) => (
                      <option key={type} value={type}>{userTypeLabels[type]}</option>
                    ))}
                  </select>
                </label>

                {/* Cooperative role — optional */}
                <label className="auth-text-field auth-text-field--full">
                  <span>Cooperative role <em className="optional-mark">optional</em></span>
                  <input
                    onChange={(event) => updateRegistration('cooperative_role', event.target.value)}
                    placeholder="e.g. Secretary or member"
                    value={registration.cooperative_role}
                  />
                </label>

              </div>

              {/* Required fields legend */}
              <p className="auth-required-note">
                <MapPin size={13} aria-hidden="true" />
                Fields marked <em className="required-mark">*</em> are required
              </p>

              <button className="primary-action auth-form__submit" disabled={isSubmitting} type="submit">
                {isSubmitting ? <LoaderCircle className="spin" size={18} /> : null}
                {isSubmitting ? 'Sending OTP…' : 'Continue to phone verification'}
              </button>
            </form>
          </>
        ) : step === 'otp' ? (
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
        ) : (
          <>
            <div className="auth-modal__intro auth-face-setup">
              <span className="auth-face-setup__icon"><Fingerprint size={27} /></span>
              <p className="section-kicker">Optional security step</p>
              <h2 id="auth-title">Set up Face ID?</h2>
              <p>Use your device's Face ID, Touch ID, or screen lock for a faster, private sign-in next time.</p>
              <p className="auth-biometric-note">Your face data and private key stay on your device. Sahayak stores only a public sign-in credential.</p>
            </div>
            <div className="auth-face-setup__actions">
              <button className="primary-action auth-form__submit" disabled={isSubmitting} onClick={() => void setUpFaceId()} type="button">{isSubmitting ? <LoaderCircle className="spin" size={18} /> : <Fingerprint size={18} />}{isSubmitting ? 'Setting up…' : 'Set up Face ID'}</button>
              <button className="text-action" disabled={isSubmitting} onClick={() => verifiedProfile && completeAccess(verifiedProfile)} type="button">Skip for now</button>
            </div>
          </>
        )}

        {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
        {notice && <p className="form-feedback form-feedback--success" role="status">{notice}</p>}
        <footer className="auth-modal__footer"><ShieldCheck size={16} /> Your phone and profile are used only to provide your support services.</footer>
      </section>
    </div>
  )
}
