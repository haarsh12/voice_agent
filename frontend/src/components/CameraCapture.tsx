import { useEffect, useRef, useState } from 'react'
import { Camera, RefreshCw, SwitchCamera, X } from 'lucide-react'

type CameraCaptureProps = {
  isOpen: boolean
  onCapture: (image: File) => void
  onClose: () => void
}

const MAX_CAPTURE_DIMENSION = 2_048

/** A user-initiated in-page camera capture, independent from the file picker. */
export function CameraCapture({ isOpen, onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [facingMode, setFacingMode] = useState<'user' | 'environment'>('environment')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    let active = true

    async function startCamera(): Promise<void> {
      setIsLoading(true)
      setError(null)
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            facingMode: { ideal: facingMode },
            height: { ideal: 1_080 },
            width: { ideal: 1_920 },
          },
        })
        if (!active) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          await videoRef.current.play()
        }
      } catch {
        if (active) setError('Camera access is unavailable. Check your browser permission and try again.')
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void startCamera()
    return () => {
      active = false
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [facingMode, isOpen])

  if (!isOpen) return null

  function capturePhoto(): void {
    const video = videoRef.current
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      setError('The camera is still starting. Please wait a moment.')
      return
    }

    const scale = Math.min(1, MAX_CAPTURE_DIMENSION / Math.max(video.videoWidth, video.videoHeight))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale))
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale))
    const context = canvas.getContext('2d')
    if (!context) {
      setError('This browser cannot capture a camera image.')
      return
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob((blob) => {
      if (!blob) {
        setError('The photo could not be captured. Please try again.')
        return
      }
      onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }))
      onClose()
    }, 'image/jpeg', 0.9)
  }

  return (
    <div className="camera-capture" role="dialog" aria-modal="true" aria-label="Take a photo">
      <div className="camera-capture__backdrop" onClick={onClose} />
      <section className="camera-capture__panel">
        <header className="camera-capture__header">
          <h3>Take a photo</h3>
          <button aria-label="Close camera" className="camera-capture__close" onClick={onClose} type="button">
            <X size={20} aria-hidden="true" />
          </button>
        </header>
        <div className="camera-capture__preview">
          <video autoPlay muted playsInline ref={videoRef} />
          {isLoading && <p>Starting camera…</p>}
          {error && <p className="camera-capture__error" role="alert">{error}</p>}
        </div>
        <footer className="camera-capture__controls">
          <button
            className="camera-capture__switch"
            disabled={isLoading}
            onClick={() => setFacingMode((mode) => (mode === 'environment' ? 'user' : 'environment'))}
            type="button"
          >
            <SwitchCamera size={17} aria-hidden="true" />
            Switch camera
          </button>
          <button className="camera-capture__take" disabled={isLoading || Boolean(error)} onClick={capturePhoto} type="button">
            {isLoading ? <RefreshCw className="spin" size={18} /> : <Camera size={18} aria-hidden="true" />}
            Capture
          </button>
        </footer>
      </section>
    </div>
  )
}
