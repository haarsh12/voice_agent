import { useEffect, useMemo, useRef, useState } from 'react'
import {
  BarVisualizer,
  useAgent,
  useTranscriptions,
  type UseSessionReturn,
} from '@livekit/components-react'
import { ParticipantEvent, RoomEvent, type RemoteParticipant } from 'livekit-client'
import {
  AlertCircle,
  Mic,
  MicOff,
  Radio,
  RefreshCw,
  Volume2,
  WifiOff,
} from 'lucide-react'

import { StatusChip } from './StatusChip'
import { TranscriptPanel, type TranscriptEntry } from './TranscriptPanel'
import { LanguageSelector } from './LanguageSelector'
import { getHealth } from '../lib/api'
import { type VoiceState, voiceStateDetails } from '../lib/voice-state'
import { isSupportedLanguage, type SupportedLanguage } from '../types/api'

type VoiceAssistantProps = {
  onLanguageChange: (language: SupportedLanguage) => void
  selectedLanguage: SupportedLanguage
  session: UseSessionReturn
}

type ServiceReadiness = 'checking' | 'ready' | 'setup-required' | 'offline'

const microphoneConstraints = {
  autoGainControl: true,
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
  voiceIsolation: true,
}

const languageControlTopic = 'vyamit.language.v1'
const internalVoiceTagPattern = /<\s*(?:analysis|reasoning|thought|thinking)\b[^>]*>[\s\S]*?(?:<\s*\/\s*(?:analysis|reasoning|thought|thinking)\s*>|$)/gi

function cleanAssistantTranscript(text: string): string {
  return text
    .replace(internalVoiceTagPattern, '')
    .replace(/<\/?[^>]+>/g, '')
    .trim()
}

function toVoiceState(
  connectionState: string,
  agentState: string,
  userIsSpeaking: boolean,
  wasInterrupted: boolean,
  hasError: boolean,
): VoiceState {
  if (hasError || agentState === 'failed') return 'error'
  if (connectionState === 'connecting' || connectionState === 'reconnecting') {
    return 'connecting'
  }
  if (connectionState === 'disconnected') return 'disconnected'
  if (wasInterrupted) return 'interrupted'
  if (userIsSpeaking) return 'user-speaking'
  if (agentState === 'speaking') return 'agent-speaking'
  if (agentState === 'thinking') return 'thinking'
  if (agentState === 'listening') return 'listening'
  return 'idle'
}

export function VoiceAssistant({
  onLanguageChange,
  selectedLanguage,
  session,
}: VoiceAssistantProps) {
  const agent = useAgent(session)
  const transcriptions = useTranscriptions({ room: session.room })
  const [isMicrophoneEnabled, setIsMicrophoneEnabled] = useState(false)
  const [isUserSpeaking, setIsUserSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [isInterrupted, setIsInterrupted] = useState(false)
  const [serviceReadiness, setServiceReadiness] = useState<ServiceReadiness>('checking')
  const [isLanguageUpdating, setIsLanguageUpdating] = useState(false)
  const interruptionTimeout = useRef<number | undefined>(undefined)
  const languageUpdateTimeout = useRef<number | undefined>(undefined)
  const lastConfirmedLanguage = useRef<SupportedLanguage>(selectedLanguage)
  const latestLanguageRevision = useRef(-1)

  useEffect(() => {
    const participant = session.room.localParticipant
    const syncSpeakingState = () => setIsUserSpeaking(participant.isSpeaking)

    syncSpeakingState()
    participant.on(ParticipantEvent.IsSpeakingChanged, syncSpeakingState)
    return () => {
      participant.off(ParticipantEvent.IsSpeakingChanged, syncSpeakingState)
    }
  }, [session.room])

  useEffect(() => {
    if (!session.isConnected) {
      setIsMicrophoneEnabled(false)
      setIsUserSpeaking(false)
    }
  }, [session.isConnected])

  useEffect(() => {
    if (!session.room) return

    const handleDataReceived = (
      payload: Uint8Array,
      participant?: RemoteParticipant,
      _kind?: unknown,
      topic?: string,
    ) => {
      if (topic !== languageControlTopic) return
      if (agent.identity && participant?.identity !== agent.identity) return

      try {
        const data: unknown = JSON.parse(new TextDecoder().decode(payload))
        if (
          !data ||
          typeof data !== 'object' ||
          !('type' in data) ||
          !('language' in data) ||
          data.type !== 'language_change' ||
          !isSupportedLanguage(data.language)
        ) {
          return
        }

        const revision = 'revision' in data && typeof data.revision === 'number'
          ? data.revision
          : null
        if (revision !== null && revision < latestLanguageRevision.current) return
        if (revision !== null) latestLanguageRevision.current = revision

        window.clearTimeout(languageUpdateTimeout.current)
        lastConfirmedLanguage.current = data.language
        onLanguageChange(data.language)
        setIsLanguageUpdating(false)
      } catch {
        // Ignore arbitrary data messages; only the agent's small validated
        // language protocol is consumed by this view.
      }
    }

    session.room.on(RoomEvent.DataReceived, handleDataReceived)

    return () => {
      session.room.off(RoomEvent.DataReceived, handleDataReceived)
    }
  }, [agent.identity, onLanguageChange, session.room])

  useEffect(() => {
    let cancelled = false

    void getHealth()
      .then((health) => {
        if (cancelled) return
        setServiceReadiness(health.configured ? 'ready' : 'setup-required')
      })
      .catch(() => {
        if (!cancelled) setServiceReadiness('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (isUserSpeaking && agent.state === 'speaking') {
      setIsInterrupted(true)
      window.clearTimeout(interruptionTimeout.current)
      interruptionTimeout.current = window.setTimeout(() => setIsInterrupted(false), 1100)
    }
  }, [agent.state, isUserSpeaking])

  useEffect(
    () => () => {
      // Do not call session.end() from a React effect cleanup. In development,
      // StrictMode deliberately runs that cleanup once after mount, which
      // looked like a user disconnect before they pressed the first button.
      window.clearTimeout(interruptionTimeout.current)
      window.clearTimeout(languageUpdateTimeout.current)
    },
    [],
  )

  const transcriptEntries = useMemo<TranscriptEntry[]>(
    () =>
      transcriptions
        .map((entry, index) => {
          const role = entry.participantInfo.identity === agent.identity ? 'assistant' : 'user'
          const text = role === 'assistant' ? cleanAssistantTranscript(entry.text) : entry.text.trim()
          if (!text) return null
          return {
            id: `${entry.participantInfo.identity}-${index}-${entry.text}`,
            role,
            text,
          }
        })
        .filter((entry): entry is TranscriptEntry => entry !== null),
    [agent.identity, transcriptions],
  )

  const agentFailure = agent.state === 'failed' ? agent.failureReasons.join(' ') : null
  const voiceState = toVoiceState(
    session.connectionState,
    agent.state,
    isUserSpeaking,
    isInterrupted,
    Boolean(error || agentFailure),
  )
  const stateDetails = voiceStateDetails[voiceState]
  const readinessMessage = {
    checking: 'Checking the local voice service…',
    ready: 'Voice service ready. Connect and allow microphone access to begin.',
    'setup-required':
      'Voice assistant is ready. Click to connect and allow microphone access.',
    offline: 'The local voice API is offline. Start FastAPI on port 8000, then refresh this page.',
  }[serviceReadiness]

  function friendlyConnectionError(caughtError: unknown): string {
    const message = caughtError instanceof Error ? caughtError.message : ''
    if (/503|token service is not configured/i.test(message)) {
      return 'LiveKit credentials are missing from the server environment. Configure the token API, then try again.'
    }
    if (/failed to fetch|networkerror|network request failed/i.test(message)) {
      return 'The local voice API cannot be reached. Start FastAPI on port 8000, then try again.'
    }
    if (/agent.*timeout|agent.*not.*available/i.test(message)) {
      return 'Connected to LiveKit, but the Vyamit voice worker is not available yet. Start the agent worker and try again.'
    }
    return 'Unable to start the voice session. Check the service status below and try again.'
  }

  async function selectLanguage(language: SupportedLanguage): Promise<void> {
    if (!session.isConnected) {
      lastConfirmedLanguage.current = language
      onLanguageChange(language)
      return
    }

    const previouslyConfirmedLanguage = lastConfirmedLanguage.current
    window.clearTimeout(languageUpdateTimeout.current)
    onLanguageChange(language)
    setIsLanguageUpdating(true)
    setError(null)

    try {
      await session.room.localParticipant.publishData(
        new TextEncoder().encode(JSON.stringify({ type: 'set_language', language })),
        { reliable: true, topic: languageControlTopic },
      )
      languageUpdateTimeout.current = window.setTimeout(() => {
        onLanguageChange(lastConfirmedLanguage.current)
        setIsLanguageUpdating(false)
        setError('The assistant did not confirm the language change. Please try again.')
      }, 5_000)
    } catch {
      onLanguageChange(previouslyConfirmedLanguage)
      setIsLanguageUpdating(false)
      setError('The language change could not be sent. Please try again.')
    }
  }

  async function connect(): Promise<void> {
    setIsStarting(true)
    setError(null)

    try {
      // TokenSource.endpoint fetches the token itself. Its participant
      // attributes include the selected language from App, so the agent starts
      // with matching STT and TTS rather than applying it after speech begins.
      await session.start({
        tracks: { microphone: { enabled: false } },
      })
      await session.room.startAudio()
      await session.room.localParticipant.setMicrophoneEnabled(true, microphoneConstraints)
      setIsMicrophoneEnabled(true)
    } catch (caughtError) {
      setError(friendlyConnectionError(caughtError))
      await session.end()
    } finally {
      setIsStarting(false)
    }
  }

  async function disconnect(): Promise<void> {
    setError(null)
    setIsMicrophoneEnabled(false)
    await session.end()
  }

  async function toggleMicrophone(): Promise<void> {
    if (!session.isConnected) return

    try {
      const nextEnabled = !isMicrophoneEnabled
      await session.room.localParticipant.setMicrophoneEnabled(
        nextEnabled,
        microphoneConstraints,
      )
      setIsMicrophoneEnabled(nextEnabled)
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : 'Microphone access was not available.'
      setError(message)
    }
  }

  return (
    <main className="voice-app">
      <header className="voice-app__header">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">
            <Radio size={18} strokeWidth={2.5} />
          </span>
          <span>Vyamit</span>
        </div>
        <StatusChip state={voiceState} />
      </header>

      <LanguageSelector
        selectedLanguage={selectedLanguage}
        onLanguageChange={(language) => void selectLanguage(language)}
        disabled={isStarting}
        isConnected={session.isConnected}
        isUpdating={isLanguageUpdating}
      />

      <div className="split-layout">
        <section className="voice-stage" aria-label="Vyamit voice session">
          <div className={`voice-orb voice-orb--${voiceState}`}>
            <div className="voice-orb__core">
              {agent.microphoneTrack ? (
                <BarVisualizer
                  barCount={9}
                  className="agent-visualizer"
                  options={{ maxHeight: 86, minHeight: 16 }}
                  state={agent.state}
                  track={agent.microphoneTrack}
                />
              ) : (
                <Volume2 size={42} strokeWidth={1.35} aria-hidden="true" />
              )}
            </div>
          </div>

          <div className="voice-stage__copy">
            <p className="eyebrow">Realtime voice assistant</p>
            <h1>{stateDetails.label}</h1>
            <p>{stateDetails.description}</p>
          </div>

          {!session.isConnected && (
            <p className={`service-notice service-notice--${serviceReadiness}`} role="status">
              {serviceReadiness === 'ready' && <span className="service-notice__dot" aria-hidden="true" />}
              {readinessMessage}
            </p>
          )}

          <div className="controls" aria-label="Voice controls">
            {session.isConnected ? (
              <>
                <button
                  aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
                  className={`round-button ${isMicrophoneEnabled ? 'round-button--active' : ''}`}
                  onClick={() => void toggleMicrophone()}
                  type="button"
                >
                  {isMicrophoneEnabled ? <Mic size={21} /> : <MicOff size={21} />}
                </button>
                <button className="disconnect-button" onClick={() => void disconnect()} type="button">
                  <WifiOff size={18} />
                  Disconnect
                </button>
              </>
            ) : (
              <button
                className="connect-button"
                disabled={isStarting || serviceReadiness === 'offline'}
                onClick={() => void connect()}
                type="button"
              >
                {isStarting ? <RefreshCw className="spin" size={18} /> : <Mic size={18} />}
                {isStarting ? 'Connecting…' : serviceReadiness === 'ready' ? 'Start conversation' : 'Connect to voice assistant'}
              </button>
            )}
          </div>

          <div className="input-meter" aria-live="polite">
            <span className="input-meter__label">Your microphone</span>
            {session.local.microphoneTrack ? (
              <BarVisualizer
                barCount={18}
                className="user-visualizer"
                options={{ maxHeight: 68, minHeight: 8 }}
                track={session.local.microphoneTrack}
              />
            ) : (
              <span className="input-meter__inactive">Microphone is off</span>
            )}
          </div>

          {(error || agentFailure) && (
            <div className="error-banner" role="alert">
              <AlertCircle size={19} />
              <span>{error || agentFailure}</span>
            </div>
          )}
        </section>

        <TranscriptPanel entries={transcriptEntries} />
      </div>
    </main>
  )
}
