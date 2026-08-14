import type { VoiceState } from '../lib/voice-state'
import { voiceStateDetails } from '../lib/voice-state'

type StatusChipProps = {
  state: VoiceState
}

export function StatusChip({ state }: StatusChipProps) {
  const details = voiceStateDetails[state]

  return (
    <span className={`status-chip status-chip--${details.tone}`}>
      <span className="status-chip__dot" aria-hidden="true" />
      {details.label}
    </span>
  )
}
