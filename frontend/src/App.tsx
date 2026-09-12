import { useMemo, useState } from 'react'
import { RoomAudioRenderer, SessionProvider, useSession } from '@livekit/components-react'
import { TokenSource } from 'livekit-client'

import { VoiceAssistant } from './components/VoiceAssistant'
import { agentName, getTokenEndpoint } from './lib/api'
import type { SupportedLanguage } from './types/api'
import './App.css'

function App() {
  // This attribute is sent when LiveKit fetches the room token. Keeping it at
  // this level means the backend sees the language chosen before the session
  // begins; the in-room control message handles later changes.
  const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>('hi-IN')
  const tokenSource = useMemo(() => TokenSource.endpoint(getTokenEndpoint()), [])
  const participantAttributes = useMemo(
    () => ({ language: selectedLanguage }),
    [selectedLanguage],
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
      />
      <RoomAudioRenderer />
    </SessionProvider>
  )
}

export default App
