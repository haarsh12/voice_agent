import { useMemo } from 'react'
import { RoomAudioRenderer, SessionProvider, useSession } from '@livekit/components-react'
import { TokenSource } from 'livekit-client'

import { VoiceAssistant } from './components/VoiceAssistant'
import { agentName, getTokenEndpoint } from './lib/api'
import './App.css'

function App() {
  const tokenSource = useMemo(() => TokenSource.endpoint(getTokenEndpoint()), [])
  const session = useSession(tokenSource, {
    agentConnectTimeoutMilliseconds: 15_000,
    agentName,
  })

  return (
    <SessionProvider session={session}>
      <VoiceAssistant session={session} />
      <RoomAudioRenderer />
    </SessionProvider>
  )
}

export default App
