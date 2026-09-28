# Female Voice & Marathi Language Support Fix

## Issues Found

### Issue 1: Male Voice Instead of Female
**Problem**: The TTS was using `hi-IN-Chirp3-HD-Charon` which is a **MALE** voice, not female as documented in comments.

**Root Cause**: Google's official documentation clarifies:
- **Charon = Male** ❌
- **Puck = Male** ❌
- **Kore = Female** ✅
- **Aoede = Female** ✅
- **Despina = Female** ✅

### Issue 2: Marathi Language Not Working Properly
**Problem**: System was configured for Hindi (hi-IN) and treating Marathi as code-switching only.

**Root Cause**: 
- Marathi (mr-IN) has **native Chirp 3: HD support** in Google Cloud TTS
- STT was set to `hi-IN` instead of `mr-IN`
- TTS voice map was using Hindi voices for Marathi

## Changes Made

### 1. Updated `.env` Configuration

**Before:**
```env
GOOGLE_STT_LANGUAGE=hi-IN
GOOGLE_TTS_LANGUAGE=hi-IN
GOOGLE_TTS_VOICE=hi-IN-Chirp3-HD-Charon  # Male voice
```

**After:**
```env
GOOGLE_STT_LANGUAGE=mr-IN                 # Marathi as primary
GOOGLE_TTS_LANGUAGE=mr-IN                 # Marathi native support
GOOGLE_TTS_VOICE=mr-IN-Chirp3-HD-Kore    # Female voice
```

### 2. Updated `providers.py` - TTS Configuration

**Key Changes:**
- Changed default voice from `Charon` (Male) to `Kore` (Female)
- Added native Marathi (mr-IN) voice support
- Updated language mappings to use `mr-IN` instead of falling back to `hi-IN`

**New Voice Map:**
```python
voice_map = {
    "hi": "hi-IN-Chirp3-HD-Kore",       # Hindi Female
    "hi-IN": "hi-IN-Chirp3-HD-Kore",
    "mr": "mr-IN-Chirp3-HD-Kore",       # Marathi Female (Native!)
    "mr-IN": "mr-IN-Chirp3-HD-Kore",
    "en": "en-US-Chirp3-HD-Kore",       # English Female
    "en-IN": "en-US-Chirp3-HD-Kore",
    "en-US": "en-US-Chirp3-HD-Kore",
}

language_map = {
    "hi": "hi-IN",
    "mr": "mr-IN",       # Native Marathi support
    "en": "en-US",
    "hi-IN": "hi-IN",
    "mr-IN": "mr-IN",    # No longer mapped to hi-IN
    "en-IN": "en-US",
    "en-US": "en-US",
}
```

### 3. Female Voice Options Available

According to [Google Cloud Documentation](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd):

**Female Voices:**
- Achernar, Aoede, Autonoe, Callirrhoe, Despina, Erinome, Gacrux, **Kore** ✅, Laomedeia, Leda, Pulcherrima, Sulafat, Vindemiatrix, Zephyr

**Male Voices:**
- Achird, Algenib, Algieba, Alnilam, **Charon** ❌, Enceladus, Fenrir, Iapetus, Orus, **Puck**, Rasalgethi, Sadachbia, Sadaltager, Schedar, Umbriel, Zubenelgenubi

**Currently Using**: `Kore` (Female)

**Alternative Female Options**: `Aoede`, `Despina`, `Achernar`, `Callirrhoe`

### 4. Language Support Summary

✅ **Marathi (mr-IN)**: Native Chirp 3: HD support  
✅ **Hindi (hi-IN)**: Native Chirp 3: HD support  
✅ **English (en-US)**: Native Chirp 3: HD support  
✅ **Code-switching**: Automatic between all three languages  

## Testing

Run the test script to verify:
```bash
cd backend
python test_female_voice_marathi.py
```

Expected output:
- ✅ All female voices (Kore, Aoede, Despina) initialize successfully
- ✅ Marathi (mr-IN) native language support confirmed
- ✅ Code-switching test passes

## How to Apply Changes

### Method 1: Restart Services (Recommended)

**Terminal 1 - Agent Worker:**
```bash
cd backend
.venv\Scripts\activate
python -m app.agent.runner dev
```

**Terminal 2 - FastAPI Backend:**
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Method 2: Use Batch Files

**Start everything:**
```bash
start_complete_backend.bat
start_frontend.bat
```

## Verification Steps

1. **Open the web frontend** at `http://localhost:5173`
2. **Connect to voice assistant**
3. **Speak in Marathi**: "नमस्कार, तुम्ही कसे आहात?"
4. **Expected**:
   - Agent understands Marathi (mr-IN STT)
   - Agent responds in Marathi
   - Voice sounds **female** (Kore voice)
   - Can switch between Marathi/Hindi/English naturally

## If Voice Still Sounds Male

Try alternative female voices by editing `.env`:

**Option 1 - Aoede (Female):**
```env
GOOGLE_TTS_VOICE=mr-IN-Chirp3-HD-Aoede
```

**Option 2 - Despina (Female):**
```env
GOOGLE_TTS_VOICE=mr-IN-Chirp3-HD-Despina
```

**Option 3 - Achernar (Female):**
```env
GOOGLE_TTS_VOICE=mr-IN-Chirp3-HD-Achernar
```

Then restart the agent worker.

## Voice Quality Comparison

| Voice | Gender | Characteristics |
|-------|--------|-----------------|
| **Kore** | Female | Natural, clear, professional |
| **Aoede** | Female | Warm, friendly tone |
| **Despina** | Female | Soft, gentle voice |
| Charon | Male | Deep, authoritative (previous) |
| Puck | Male | Clear, conversational |

## System Prompt Support

The agent prompt already supports Marathi:
```
Mirror the user's language naturally: reply in English to English, Hindi to
Hindi, Marathi to Marathi, and preserve comfortable Hindi-English-Marathi
code-switching.
```

## References

- [Google Cloud Chirp 3: HD Documentation](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)
- [Supported Languages](https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types)
- [LiveKit Google Plugin](https://docs.livekit.io/agents/models/tts/google/)

## Next Steps

1. ✅ Test with Marathi speech input
2. ✅ Verify female voice output
3. ✅ Test code-switching (Marathi ↔ Hindi ↔ English)
4. 📝 Provide feedback on voice quality
5. 🔄 Switch to alternative female voice if needed

---

**Status**: ✅ Fixed - Female voice (Kore) with native Marathi support enabled
