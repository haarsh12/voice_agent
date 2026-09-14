import { useCallback, useEffect, useMemo, useState } from 'react'
import { RoomAudioRenderer, SessionProvider, useSession } from '@livekit/components-react'
import { TokenSource } from 'livekit-client'

import { VoiceAssistant } from './components/VoiceAssistant'
import { agentName, createGuestSession, deleteGuestSession, getTokenEndpoint } from './lib/api'
import type { GuestSession, SupportedLanguage } from './types/api'
import './App.css'

function App() {
  // This attribute is sent when LiveKit fetches the room token. Keeping it at
  // this level means the backend sees the language chosen before the session
  // begins; the in-room control message handles later changes.
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
    return () => {
      active = false
    }
  }, [])

  const startNewGuestSession = useCallback(async (): Promise<void> => {
    const previousSession = guestSession
    setGuestSession(null)
    setGuestSessionError(null)
    try {
      if (previousSession) {
        // Deletion is best-effort: a momentary network failure must not trap a
        // guest in an old conversation. The old in-memory context still has a
        // short idle expiry if this request cannot reach the API.
        await deleteGuestSession(previousSession).catch(() => undefined)
      }
      const created = await createGuestSession()
      setGuestSession(created)
    } catch (error) {
      setGuestSessionError(
        error instanceof Error ? error.message : 'A new guest session could not be started.',
      )
      throw error
    }
  }, [guestSession])

  const participantAttributes = useMemo(
    () => ({
      language: selectedLanguage,
      ...(guestSession
        ? {
            guest_session_id: guestSession.session_id,
            guest_session_secret: guestSession.session_secret,
          }
        : {}),
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
        onLanguageChange={setSelectedLanguage}
        selectedLanguage={selectedLanguage}
        session={session}
        guestSession={guestSession}
        guestSessionError={guestSessionError}
        onStartNewSession={startNewGuestSession}
      />
      <RoomAudioRenderer />
    </SessionProvider>
  )
}

export default App
