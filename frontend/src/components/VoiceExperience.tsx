import { useCallback, useEffect, useMemo, useState } from 'react'
import { RoomAudioRenderer, SessionProvider, useSession } from '@livekit/components-react'
import { TokenSource } from 'livekit-client'

import { agentName, createGuestSession, deleteGuestSession, getTokenEndpoint } from '../lib/api'
import type { GuestSession, SupportedLanguage } from '../types/api'
import { VoiceAssistant } from './VoiceAssistant'

export default function VoiceExperience() {
  const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>('hi-IN')
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null)
  const [guestSessionError, setGuestSessionError] = useState<string | null>(null)
  const tokenSource = useMemo(() => TokenSource.endpoint(getTokenEndpoint()), [])

  useEffect(() => {
    let active = true
    void createGuestSession()
      .then((created) => {
        if (active) setGuestSession(created)
        else void deleteGuestSession(created).catch(() => undefined)
      })
      .catch(() => {
        if (active) setGuestSessionError('A private guest session could not be started. Refresh and try again.')
      })
    return () => { active = false }
  }, [])

  const startNewGuestSession = useCallback(async (): Promise<void> => {
    const previousSession = guestSession
    setGuestSession(null)
    setGuestSessionError(null)
    try {
      if (previousSession) await deleteGuestSession(previousSession).catch(() => undefined)
      setGuestSession(await createGuestSession())
    } catch (error) {
      const message = error instanceof Error ? error.message : 'A new guest session could not be started.'
      setGuestSessionError(message)
      throw error
    }
  }, [guestSession])

  const participantAttributes = useMemo(
    () => ({
      language: selectedLanguage,
      ...(guestSession ? { guest_session_id: guestSession.session_id, guest_session_secret: guestSession.session_secret } : {}),
    }),
    [guestSession, selectedLanguage],
  )
  const session = useSession(tokenSource, {
    agentConnectTimeoutMilliseconds: 15_000,
    agentName,
    participantAttributes,
  })

  return (
    <SessionProvider session={session}>
      <VoiceAssistant
        guestSession={guestSession}
        guestSessionError={guestSessionError}
        onLanguageChange={setSelectedLanguage}
        onStartNewSession={startNewGuestSession}
        selectedLanguage={selectedLanguage}
        session={session}
      />
      <RoomAudioRenderer />
    </SessionProvider>
  )
}
