import { Languages } from 'lucide-react'
import type { SupportedLanguage } from '../types/api'

type LanguageSelectorProps = {
  selectedLanguage: SupportedLanguage
  onLanguageChange: (language: SupportedLanguage) => void
  disabled?: boolean
  isConnected?: boolean
  isUpdating?: boolean
}

const LANGUAGE_OPTIONS: Array<{ code: SupportedLanguage; label: string; native: string; emoji: string }> = [
  { code: 'hi-IN', label: 'Hindi', native: 'हिन्दी', emoji: '🇮🇳' },
  { code: 'mr-IN', label: 'Marathi', native: 'मराठी', emoji: '🇮🇳' },
  { code: 'en-IN', label: 'English', native: 'English', emoji: '🇬🇧' },
  { code: 'ta-IN', label: 'Tamil', native: 'தமிழ்', emoji: '🇮🇳' },
  { code: 'te-IN', label: 'Telugu', native: 'తెలుగు', emoji: '🇮🇳' },
  { code: 'kn-IN', label: 'Kannada', native: 'ಕನ್ನಡ', emoji: '🇮🇳' },
  { code: 'ml-IN', label: 'Malayalam', native: 'മലയാളം', emoji: '🇮🇳' },
  { code: 'gu-IN', label: 'Gujarati', native: 'ગુજરાતી', emoji: '🇮🇳' },
  { code: 'bn-IN', label: 'Bengali', native: 'বাংলা', emoji: '🇮🇳' },
  { code: 'pa-IN', label: 'Punjabi', native: 'ਪੰਜਾਬੀ', emoji: '🇮🇳' },
]

export function LanguageSelector({
  selectedLanguage,
  onLanguageChange,
  disabled = false,
  isConnected = false,
  isUpdating = false,
}: LanguageSelectorProps) {
  return (
    <div className="language-bar">
      <div className="language-bar__header">
        <Languages size={16} aria-hidden="true" />
        <span>Select Language</span>
        {isConnected ? (
          <span className="language-bar__hint" aria-live="polite">
            {isUpdating ? 'Switching language…' : 'Live · using selected language'}
          </span>
        ) : (
          <span className="language-bar__hint">Choose a preferred language before you start</span>
        )}
      </div>
      <div className="language-bar__options" role="radiogroup" aria-label="Language selection">
        {LANGUAGE_OPTIONS.map((option) => {
          const isSelected = option.code === selectedLanguage
          return (
            <button
              key={option.code}
              type="button"
              role="radio"
              aria-checked={isSelected}
              className={`language-box ${isSelected ? 'language-box--active' : ''}`}
              onClick={() => onLanguageChange(option.code)}
              disabled={disabled || isUpdating}
              aria-label={`Select ${option.label}`}
            >
              <span className="language-box__emoji" aria-hidden="true">{option.emoji}</span>
              <span className="language-box__native">{option.native}</span>
              <span className="language-box__label">{option.label}</span>
              {isSelected && <span className="language-box__indicator" aria-hidden="true" />}
            </button>
          )
        })}
      </div>
    </div>
  )
}
