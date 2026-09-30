export type VoiceState =
  | 'idle'
  | 'connecting'
  | 'listening'
  | 'user-speaking'
  | 'thinking'
  | 'agent-speaking'
  | 'interrupted'
  | 'error'
  | 'disconnected'

export type VoiceStateDetails = {
  label: string
  description: string
  tone: 'quiet' | 'active' | 'warning' | 'danger'
}

export const voiceStateDetails: Record<VoiceState, VoiceStateDetails> = {
  idle: { label: 'Ready', description: 'Connect to begin a voice session.', tone: 'quiet' },
  connecting: { label: 'Connecting', description: 'Joining your private voice room.', tone: 'active' },
  listening: { label: 'Listening', description: 'Speak whenever you are ready.', tone: 'active' },
  'user-speaking': { label: 'Listening', description: 'Vyamit is receiving your voice.', tone: 'active' },
  thinking: { label: 'Thinking', description: 'Preparing a response.', tone: 'active' },
  'agent-speaking': { label: 'Speaking', description: 'You can interrupt at any time.', tone: 'active' },
  interrupted: { label: 'Interrupted', description: 'Your new turn takes priority.', tone: 'warning' },
  error: { label: 'Needs attention', description: 'Check the connection and try again.', tone: 'danger' },
  disconnected: { label: 'Disconnected', description: 'Connect when you are ready.', tone: 'quiet' },
}
