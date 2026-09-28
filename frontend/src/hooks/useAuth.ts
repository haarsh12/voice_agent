import { useCallback, useEffect, useState } from 'react'

import {
  getProfile,
  finishFaceIdAuthentication,
  finishFaceIdRegistration,
  removeFaceId,
  requestOtp,
  signOut,
  startFaceIdAuthentication,
  startFaceIdRegistration,
  updateProfile,
  verifyOtp,
  type MobileAuthIntent,
  type RegistrationPayload,
} from '../lib/api'
import { createDeviceCredential, requestDeviceCredential } from '../lib/webauthn'
import type { ProfileUpdate, SahayakProfile, VerifiedProfile } from '../types/api'

export type AuthStatus = 'loading' | 'guest' | 'authenticated'

export type SahayakAuth = {
  status: AuthStatus
  user: SahayakProfile | null
  requestOtp: (phoneNumber: string, intent: MobileAuthIntent) => Promise<void>
  verifyOtp: (
    phoneNumber: string,
    otpCode: string,
    intent: MobileAuthIntent,
    registration?: RegistrationPayload,
  ) => Promise<VerifiedProfile>
  saveProfile: (payload: ProfileUpdate) => Promise<SahayakProfile>
  registerFaceId: () => Promise<SahayakProfile>
  signInWithFaceId: () => Promise<SahayakProfile>
  removeFaceId: () => Promise<SahayakProfile>
  signOut: () => Promise<void>
  refresh: () => Promise<SahayakProfile | null>
}

export function useAuth(): SahayakAuth {
  const [user, setUser] = useState<SahayakProfile | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  const refresh = useCallback(async (): Promise<SahayakProfile | null> => {
    try {
      const profile = await getProfile()
      setUser(profile)
      setStatus('authenticated')
      return profile
    } catch {
      setUser(null)
      setStatus('guest')
      return null
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const sendOtp = useCallback(async (phoneNumber: string, intent: MobileAuthIntent): Promise<void> => {
    await requestOtp(phoneNumber, intent)
  }, [])

  const confirmOtp = useCallback(async (
    phoneNumber: string,
    otpCode: string,
    intent: MobileAuthIntent,
    registration?: RegistrationPayload,
  ): Promise<VerifiedProfile> => {
    const profile = await verifyOtp(phoneNumber, otpCode, intent, registration)
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const saveProfile = useCallback(async (payload: ProfileUpdate): Promise<SahayakProfile> => {
    const profile = await updateProfile(payload)
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const registerFaceId = useCallback(async (): Promise<SahayakProfile> => {
    const options = await startFaceIdRegistration()
    const credential = await createDeviceCredential(options.public_key)
    const profile = await finishFaceIdRegistration(options.ceremony_id, credential)
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const signInWithFaceId = useCallback(async (): Promise<SahayakProfile> => {
    const options = await startFaceIdAuthentication()
    const credential = await requestDeviceCredential(options.public_key)
    const profile = await finishFaceIdAuthentication(options.ceremony_id, credential)
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const forgetFaceId = useCallback(async (): Promise<SahayakProfile> => {
    const profile = await removeFaceId()
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const logout = useCallback(async (): Promise<void> => {
    try {
      await signOut()
    } finally {
      setUser(null)
      setStatus('guest')
    }
  }, [])

  return {
    status,
    user,
    requestOtp: sendOtp,
    verifyOtp: confirmOtp,
    saveProfile,
    registerFaceId,
    signInWithFaceId,
    removeFaceId: forgetFaceId,
    signOut: logout,
    refresh,
  }
}
