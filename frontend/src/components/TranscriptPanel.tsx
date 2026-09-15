import { type ChangeEvent, type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from 'react'
import { Camera, FileText, ImagePlus, LoaderCircle, Paperclip, Send, X } from 'lucide-react'
import { CameraCapture } from './CameraCapture'
import type { OfficialSourceReference } from '../types/api'

export type TranscriptEntry = {
  id: string
  role: 'user' | 'assistant'
  text: string
  attachmentName?: string
  sources?: OfficialSourceReference[]
  source: 'text' | 'voice'
}

type TranscriptPanelProps = {
  entries: TranscriptEntry[]
  isSendingText: boolean
  disabled: boolean
  onSendText: (message: string, document: File | null) => Promise<void>
}

const MAX_DOCUMENT_BYTES = 5 * 1024 * 1024

export function TranscriptPanel({ entries, isSendingText, disabled, onSendText }: TranscriptPanelProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const lastEntryRef = useRef<HTMLLIElement>(null)
  const documentInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const formRef = useRef<HTMLFormElement>(null)
  const [message, setMessage] = useState('')
  const [document, setDocument] = useState<File | null>(null)
  const [composerError, setComposerError] = useState<string | null>(null)
  const [isCameraOpen, setIsCameraOpen] = useState(false)

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (lastEntryRef.current) {
      lastEntryRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [entries])

  function clearDocument(): void {
    setDocument(null)
    for (const input of [documentInputRef, imageInputRef]) {
      if (input.current) input.current.value = ''
    }
  }

  function chooseAttachment(event: ChangeEvent<HTMLInputElement>): void {
    const selectedDocument = event.target.files?.[0] ?? null
    setSelectedAttachment(selectedDocument)
  }

  function setSelectedAttachment(selectedDocument: File | null): void {
    if (!selectedDocument) return
    if (selectedDocument.size > MAX_DOCUMENT_BYTES) {
      clearDocument()
      setComposerError('Documents must be 5 MB or smaller.')
      return
    }
    setComposerError(null)
    setDocument(selectedDocument)
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!isSendingText && !disabled && (message.trim() || document)) formRef.current?.requestSubmit()
    }
  }

  async function submitTextMessage(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    const trimmedMessage = message.trim()
    if (!trimmedMessage && !document) {
      setComposerError('Write a message or attach a document.')
      return
    }

    setComposerError(null)
    try {
      await onSendText(trimmedMessage, document)
      setMessage('')
      clearDocument()
    } catch (error) {
      setComposerError(
        error instanceof Error ? error.message : 'The text message could not be sent. Please try again.',
      )
    }
  }

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
                  {entry.role === 'assistant' ? 'Sahayak AI' : 'You'}
                </span>
                <p>{entry.text}</p>
                {entry.role === 'assistant' && entry.sources && entry.sources.length > 0 && (
                  <footer className="transcript-entry__sources" aria-label="Official sources">
                    <span>Official source{entry.sources.length > 1 ? 's' : ''}</span>
                    {entry.sources.map((source) => (
                      <a href={source.url} key={source.url} rel="noreferrer" target="_blank">
                        {source.name}<small>{source.url}</small>
                      </a>
                    ))}
                  </footer>
                )}
                {entry.attachmentName && (
                  <span className="transcript-entry__attachment">
                    <FileText size={14} aria-hidden="true" />
                    {entry.attachmentName}
                  </span>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>

      <form className="text-composer" onSubmit={(event) => void submitTextMessage(event)} ref={formRef}>
        {document && (
          <div className="text-composer__attachment">
            <FileText size={15} aria-hidden="true" />
            <span title={document.name}>{document.name}</span>
            <button
              aria-label={`Remove ${document.name}`}
              className="text-composer__remove-file"
              onClick={clearDocument}
              type="button"
            >
              <X size={15} aria-hidden="true" />
            </button>
          </div>
        )}
        <div className="text-composer__row">
          <input
            accept=".txt,.md,.pdf,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            aria-label="Attach a TXT, Markdown, PDF, or DOCX document"
            className="text-composer__file-input"
            onChange={chooseAttachment}
            ref={documentInputRef}
            type="file"
          />
          <input
            accept=".jpg,.jpeg,.png,image/jpeg,image/png"
            aria-label="Upload a JPEG or PNG image"
            className="text-composer__file-input"
            onChange={chooseAttachment}
            ref={imageInputRef}
            type="file"
          />
          <button
            aria-label="Attach document"
            className="text-composer__attach"
            disabled={isSendingText || disabled}
            onClick={() => documentInputRef.current?.click()}
            title="Attach TXT, Markdown, PDF, or DOCX (up to 5 MB)"
            type="button"
          >
            <Paperclip size={19} aria-hidden="true" />
          </button>
          <button
            aria-label="Upload JPEG or PNG image"
            className="text-composer__attach"
            disabled={isSendingText || disabled}
            onClick={() => imageInputRef.current?.click()}
            title="Upload JPEG or PNG (up to 5 MB)"
            type="button"
          >
            <ImagePlus size={19} aria-hidden="true" />
          </button>
          <button
            aria-label="Take a photo"
            className="text-composer__attach"
            disabled={isSendingText || disabled}
            onClick={() => setIsCameraOpen(true)}
            title="Take a photo with your camera"
            type="button"
          >
            <Camera size={19} aria-hidden="true" />
          </button>
          <textarea
            aria-label="Message Sahayak AI"
            className="text-composer__input"
            disabled={isSendingText || disabled}
            maxLength={4_000}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder="Type a message or ask about an attached document…"
            rows={1}
            value={message}
          />
          <button
            aria-label="Send text message"
            className="text-composer__send"
            disabled={isSendingText || disabled || (!message.trim() && !document)}
            type="submit"
          >
            {isSendingText ? <LoaderCircle className="spin" size={18} /> : <Send size={18} aria-hidden="true" />}
          </button>
        </div>
        <p className="text-composer__hint">Enter sends · Shift+Enter adds a line · document, image, or camera · up to 5 MB</p>
        {composerError && <p className="text-composer__error" role="alert">{composerError}</p>}
      </form>
      <CameraCapture
        isOpen={isCameraOpen}
        onCapture={setSelectedAttachment}
        onClose={() => setIsCameraOpen(false)}
      />
    </section>
  )
}
