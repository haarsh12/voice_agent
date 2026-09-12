# Language Selector Feature Documentation

## Overview
Users can now select their preferred language (Hindi, Marathi, English, Tamil, Telugu, Kannada, Malayalam, Gujarati, Bengali, Punjabi) before starting a voice conversation. The selected language sets the primary language for Text-to-Speech (TTS) while Speech-to-Text (STT) maintains multilingual support for automatic code-switching.

## Features Implemented

### 1. **Backend API Changes**

#### `/api/token` Endpoint Enhancement
- **Added `language` parameter** to `TokenRequest` model
- **Type-safe validation** using Python `Literal` type for supported languages
- **Supported languages**: `hi-IN`, `mr-IN`, `en-IN`, `ta-IN`, `te-IN`, `kn-IN`, `ml-IN`, `gu-IN`, `bn-IN`, `pa-IN`

#### Token Issuer Updates
- Language preference is **embedded in JWT token** via participant attributes
- Accessible to agent through `participant.attributes['language']`
- **Secure transmission** - no additional API calls needed

#### Agent Runner Intelligence
- **Reads language preference** from participant metadata on connection
- **Dynamically creates TTS provider** with user's chosen language
- **Maintains multilingual STT** for code-switching support
- **Logs language preference** for debugging and monitoring

### 2. **Frontend UI Components**

#### Language Selector Component
- **Beautiful dropdown** with 10 Indian languages
- Shows both **English and native script** names (e.g., "Hindi (हिन्दी)")
- **Disabled during connection** to prevent mid-session changes
- **Accessible** with proper ARIA labels
- **Visual feedback** with hint text

#### Integration with Voice Assistant
- Positioned above "Connect" button
- **State management** with React hooks
- **Default language**: Marathi (`mr-IN`)
- Language passed to token creation on connection

### 3. **Security & Best Practices**

✅ **Type-safe validation** at API level (Pydantic + Literal types)  
✅ **Secure token transmission** (embedded in JWT, not query params)  
✅ **Input validation** prevents invalid language codes  
✅ **No API key exposure** (uses Vertex AI service account)  
✅ **Graceful fallbacks** if no language specified  

## How It Works

### Flow Diagram
```
User Selects Language → Frontend creates token with language
                                ↓
                    Token embedded with language preference
                                ↓
                    Agent reads from participant.attributes
                                ↓
                    Creates TTS with selected language
                                ↓
                Agent speaks in user's language + STT detects all languages
```

## Testing Instructions

### Step 1: Start Backend Services
```bash
# From project root
.\start_complete_backend.bat
```

Wait for both services to start:
- ✅ FastAPI backend on port 8000
- ✅ LiveKit agent worker

### Step 2: Start Frontend
```bash
cd frontend
npm run dev
```

Frontend should be available at: `http://localhost:5173`

### Step 3: Test Language Switching

#### Test 1: Hindi Language
1. Open browser to `http://localhost:5173`
2. Select **"Hindi (हिन्दी)"** from language dropdown
3. Click **"Start conversation"**
4. **Speak in Hindi**: "नमस्ते, आप कैसे हैं?"
5. **Expected**: Agent responds in Hindi with Hindi voice

#### Test 2: Marathi Language (Default)
1. Disconnect if connected
2. Select **"Marathi (मराठी)"** from language dropdown
3. Click **"Start conversation"**
4. **Speak in Marathi**: "नमस्कार, तुम्ही कसे आहात?"
5. **Expected**: Agent responds in Marathi with Marathi voice

#### Test 3: English Language
1. Disconnect if connected
2. Select **"English (English)"** from language dropdown
3. Click **"Start conversation"**
4. **Speak in English**: "Hello, how are you?"
5. **Expected**: Agent responds in English with English voice

#### Test 4: Code-Switching (Multilingual)
1. Connect with **any language selected** (e.g., Hindi)
2. **Speak mixed**: "Hello, मैं अच्छा हूँ, thank you"
3. **Expected**: 
   - STT correctly transcribes mixed languages
   - Agent responds in the **selected primary language**

#### Test 5: Other Indian Languages
Try Tamil, Telugu, Kannada, Malayalam, Gujarati, Bengali, or Punjabi:
1. Select the language
2. Connect and speak in that language
3. Verify agent responds with appropriate voice

### Step 4: Verify in Backend Logs

Check agent worker logs for language detection:
```
[INFO] participant_language_preference participant=web-xxx language=hi-IN
[INFO] switching_tts_voice language=hi
```

## Configuration

### Backend Environment (.env)
```bash
# Default language if user doesn't select (currently Marathi)
GOOGLE_STT_LANGUAGE=mr-IN
GOOGLE_TTS_LANGUAGE=mr-IN
GOOGLE_TTS_VOICE=mr-IN-Chirp3-HD-Kore
```

### Frontend Default Language
Located in `frontend/src/components/VoiceAssistant.tsx`:
```typescript
const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>('mr-IN')
```

Change `'mr-IN'` to any supported language code to change the default.

## Supported Languages

| Language | Code | TTS Voice | STT Support |
|----------|------|-----------|-------------|
| Hindi | `hi-IN` | Chirp 3 HD | ✅ |
| Marathi | `mr-IN` | Chirp 3 HD | ✅ |
| English | `en-IN` | Chirp 3 HD | ✅ |
| Tamil | `ta-IN` | Chirp 3 HD | ✅ |
| Telugu | `te-IN` | Chirp 3 HD | ✅ |
| Kannada | `kn-IN` | Chirp 3 HD | ✅ |
| Malayalam | `ml-IN` | Chirp 3 HD | ✅ |
| Gujarati | `gu-IN` | Chirp 3 HD | ✅ |
| Bengali | `bn-IN` | Chirp 3 HD | ✅ |
| Punjabi | `pa-IN` | Chirp 3 HD | ✅ |

## Architecture

### Backend Stack
- **FastAPI** - Token API with language validation
- **LiveKit** - Real-time communication
- **Google Cloud STT** - Multilingual speech recognition
- **Google Cloud TTS Chirp 3 HD** - Natural voice synthesis
- **Gemini 3.5 Flash** - LLM via Vertex AI

### Frontend Stack
- **React + TypeScript** - UI components
- **LiveKit Components React** - Voice session management
- **Lucide React** - Icons

## Troubleshooting

### Issue: Language selector not showing
- **Check**: Browser console for component errors
- **Verify**: `LanguageSelector.tsx` was created correctly
- **Solution**: Refresh page, clear browser cache

### Issue: Agent not speaking in selected language
- **Check**: Backend logs for `participant_language_preference`
- **Verify**: Token includes language attribute
- **Solution**: Restart agent worker

### Issue: "Language not supported" error
- **Check**: Language code matches exactly (e.g., `hi-IN` not `hi`)
- **Verify**: Backend SUPPORTED_LANGUAGES list in `routes.py`
- **Solution**: Use exact language codes from the list

### Issue: Code-switching not working
- **Check**: STT is using multilingual model (it should by default)
- **Verify**: Google Cloud STT credentials are valid
- **Solution**: STT maintains multilingual support regardless of TTS language

## Files Modified

### Backend
- `backend/app/api/routes.py` - Added language parameter and validation
- `backend/app/services/token_issuer.py` - Embed language in token attributes
- `backend/app/agent/runner.py` - Read language and create TTS dynamically

### Frontend
- `frontend/src/components/LanguageSelector.tsx` - New language selector component
- `frontend/src/components/VoiceAssistant.tsx` - Integration with language selector
- `frontend/src/types/api.ts` - Type definitions for languages
- `frontend/src/lib/api.ts` - API call with language parameter
- `frontend/src/App.css` - Language selector styling

## Future Enhancements

### Potential Improvements
- 💾 **Remember last selected language** (localStorage)
- 🔄 **Mid-session language switching** (requires reconnection)
- 🎭 **Voice gender selection** (male/female voices)
- 📊 **Language usage analytics**
- 🌐 **Add more regional languages** (Assamese, Urdu, etc.)
- 🎨 **Language-specific UI themes**
- 🔊 **Adjust speech rate per language**

## Credits
- **Google Cloud Speech-to-Text** - Multilingual STT
- **Google Cloud Text-to-Speech Chirp 3 HD** - Natural voices
- **LiveKit** - Real-time communication platform
- **Gemini 3.5 Flash** - Conversational AI

---

**Created**: 2026-09-07  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
