import { type FormEvent, useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, LoaderCircle, MapPin, UserRound } from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import { USER_TYPES, type SahayakProfile, type UserType } from '../types/api'

type OnboardingProps = {
  auth: SahayakAuth
  profile: SahayakProfile
  onComplete: () => void
}

const ROLE_LABELS: Record<UserType, string> = {
  cooperative_member: 'Cooperative member',
  farmer: 'Farmer',
  pacs_member: 'PACS member',
  cooperative_official: 'Cooperative official',
  rural_stakeholder: 'Rural stakeholder',
  other: 'Other',
}

export function Onboarding({ auth, profile, onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1)
  const [fullName, setFullName] = useState(profile.full_name ?? '')
  const [state, setState] = useState(profile.state ?? '')
  const [district, setDistrict] = useState(profile.district ?? '')
  const [village, setVillage] = useState(profile.village_or_town ?? '')
  const [address, setAddress] = useState(profile.address ?? '')
  const [userType, setUserType] = useState<UserType | ''>(profile.user_type ?? '')
  const [cooperativeRole, setCooperativeRole] = useState(profile.cooperative_role ?? '')
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const stepTitle = useMemo(() => step === 1 ? 'Tell us where to support you.' : 'Help us personalise your experience.', [step])

  function nextStep(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    if (!fullName.trim() || !state.trim() || !district.trim() || !village.trim()) {
      setError('Add your name, state, district and town or village to continue.')
      return
    }
    setError(null)
    setStep(2)
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!userType) {
      setError('Choose the option that best describes you.')
      return
    }
    setError(null)
    setIsSaving(true)
    try {
      await auth.saveProfile({
        full_name: fullName.trim(),
        state: state.trim(),
        district: district.trim(),
        village_or_town: village.trim(),
        ...(address.trim() ? { address: address.trim() } : {}),
        user_type: userType,
        ...(cooperativeRole.trim() ? { cooperative_role: cooperativeRole.trim() } : {}),
      })
      onComplete()
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'We could not save your profile. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <main className="onboarding-page">
      <section className="onboarding-card">
        <div className="onboarding-card__progress" aria-label={'Step ' + step + ' of 2'}><span className={step === 1 ? 'is-active' : 'is-done'} /><span className={step === 2 ? 'is-active' : ''} /></div>
        <p className="section-kicker">Set up your Sahayak space</p>
        <h1>{stepTitle}</h1>
        <p className="onboarding-card__lead">You can update these details later. Your mobile number, {profile.phone_number}, remains your verified identity.</p>

        {step === 1 ? (
          <form className="onboarding-form" onSubmit={nextStep}>
            <label><span><UserRound size={15} /> Your name</span><input autoComplete="name" onChange={(event) => setFullName(event.target.value)} required value={fullName} /></label>
            <div className="form-grid">
              <label><span><MapPin size={15} /> State</span><input autoComplete="address-level1" onChange={(event) => setState(event.target.value)} required value={state} /></label>
              <label><span>District / city</span><input autoComplete="address-level2" onChange={(event) => setDistrict(event.target.value)} required value={district} /></label>
            </div>
            <label><span>Town / village</span><input onChange={(event) => setVillage(event.target.value)} required value={village} /></label>
            <label><span>Address <em>Optional</em></span><textarea onChange={(event) => setAddress(event.target.value)} rows={3} value={address} /></label>
            {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
            <button className="primary-action onboarding-card__submit" type="submit">Continue <ArrowRight size={17} /></button>
          </form>
        ) : (
          <form className="onboarding-form" onSubmit={(event) => void submitProfile(event)}>
            <label><span>Which best describes you?</span>
              <select onChange={(event) => setUserType(event.target.value as UserType)} required value={userType}>
                <option disabled value="">Select your role</option>
                {USER_TYPES.map((type) => <option key={type} value={type}>{ROLE_LABELS[type]}</option>)}
              </select>
            </label>
            <label><span>Your cooperative role <em>Optional</em></span><input onChange={(event) => setCooperativeRole(event.target.value)} placeholder="For example, member, office bearer or volunteer" value={cooperativeRole} /></label>
            <p className="onboarding-card__note">This helps Sahayak AI organise your service space. It does not determine access to government benefits or services.</p>
            {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
            <div className="onboarding-card__actions"><button className="text-action" onClick={() => setStep(1)} type="button"><ArrowLeft size={16} /> Back</button><button className="primary-action" disabled={isSaving} type="submit">{isSaving ? <LoaderCircle className="spin" size={17} /> : null}{isSaving ? 'Saving…' : 'Complete setup'}</button></div>
          </form>
        )}
      </section>
    </main>
  )
}
