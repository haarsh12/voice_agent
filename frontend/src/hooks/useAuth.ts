import { useCallback, useEffect, useState } from 'react'

import { getProfile, requestOtp, signOut, updateProfile, verifyOtp } from '../lib/api'
import type { ProfileUpdate, SahayakProfile, VerifiedProfile } from '../types/api'

export type AuthStatus = 'loading' | 'guest' | 'authenticated'

export type SahayakAuth = {
  status: AuthStatus
  user: SahayakProfile | null
  requestOtp: (phoneNumber: string) => Promise<void>
  verifyOtp: (phoneNumber: string, otpCode: string) => Promise<VerifiedProfile>
  saveProfile: (payload: ProfileUpdate) => Promise<SahayakProfile>
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

  const sendOtp = useCallback(async (phoneNumber: string): Promise<void> => {
    await requestOtp(phoneNumber)
  }, [])

  const confirmOtp = useCallback(async (phoneNumber: string, otpCode: string): Promise<VerifiedProfile> => {
    const profile = await verifyOtp(phoneNumber, otpCode)
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

  const logout = useCallback(async (): Promise<void> => {
    try {
      await signOut()
    } finally {
      setUser(null)
      setStatus('guest')
    }
  }, [])

  return { status, user, requestOtp: sendOtp, verifyOtp: confirmOtp, saveProfile, signOut: logout, refresh }
}
