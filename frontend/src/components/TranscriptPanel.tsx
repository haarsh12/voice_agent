import { useEffect, useRef } from 'react'

export type TranscriptEntry = {
  id: string
  role: 'user' | 'assistant'
  text: string
}

type TranscriptPanelProps = {
  entries: TranscriptEntry[]
}

export function TranscriptPanel({ entries }: TranscriptPanelProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const lastEntryRef = useRef<HTMLLIElement>(null)

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (lastEntryRef.current) {
      lastEntryRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [entries])

  return (
    <section className="transcript-panel" aria-label="Live conversation transcript">
      <div className="transcript-panel__header">
        <div>
          <p className="eyebrow">Conversation</p>
          <h2>Live transcript</h2>
        </div>
        <span className="live-indicator">Live</span>
      </div>

      <div className="transcript-scroll-container" ref={scrollContainerRef}>
        {entries.length === 0 ? (
          <p className="transcript-panel__empty">
            Your conversation will appear here as speech is transcribed.
          </p>
        ) : (
          <ol className="transcript-list">
            {entries.map((entry, index) => (
              <li 
                className={`transcript-entry transcript-entry--${entry.role}`} 
                key={entry.id}
                ref={index === entries.length - 1 ? lastEntryRef : null}
              >
                <span className="transcript-entry__role">
                  {entry.role === 'assistant' ? 'Vyamit' : 'You'}
                </span>
                <p>{entry.text}</p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  )
}
