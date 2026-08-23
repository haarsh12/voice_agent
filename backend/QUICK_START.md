# Quick Start - Google Cloud TTS

## ⚡ Start the Agent

```bash
cd backend
.venv\Scripts\activate
python -m app.agent.runner dev
```

## 🎤 Current Voice Configuration

| Language | Voice | Quality |
|----------|-------|---------|
| Hindi | hi-IN-Neural2-A (Female) | ⭐⭐⭐⭐⭐ |
| Marathi | mr-IN-Wavenet-A (Female) | ⭐⭐⭐⭐☆ |
| English | en-IN-Neural2-A (Female) | ⭐⭐⭐⭐⭐ |

**Automatic switching** - Just speak in any language!

## 🔧 Change Voice (Optional)

Edit `backend/.env`:

```env
# For Male Voices:
GOOGLE_TTS_VOICE=hi-IN-Neural2-B  # Hindi Male
# or
GOOGLE_TTS_VOICE=mr-IN-Wavenet-B  # Marathi Male

# Adjust Speed (0.5-2.0):
GOOGLE_TTS_SPEED=1.1  # Slightly faster

# Adjust Pitch (-20 to +20):
GOOGLE_TTS_PITCH=-1.0  # Slightly deeper
```

Then restart the agent.

## ✅ Test Everything

```bash
# Test TTS voices
python test_google_tts.py

# Test all providers
python -c "from app.agent.providers import *; from app.config.settings import get_settings; s=get_settings(); create_tts(s); create_stt(s); create_llm(s); print('✅ All working!')"
```

## 🎯 What to Expect

**Speak Hindi** → Hear natural Hindi voice  
**Speak Marathi** → Hear natural Marathi voice  
**Speak English** → Hear natural English voice  
**Mix languages** → Seamless switching!

## 📚 Documentation

- **Complete Setup**: `GOOGLE_TTS_SETUP.md`
- **All Voices**: `GOOGLE_TTS_VOICES.md`
- **Migration Details**: `../MIGRATION_TO_GOOGLE_TTS.md`

## 🆘 Common Issues

**No audio?**
```bash
gcloud services enable texttospeech.googleapis.com
```

**Robotic voice?**
- Use Neural2 or Wavenet (not Standard)
- Check: `GOOGLE_TTS_VOICE=hi-IN-Neural2-A`

**Wrong language?**
- Check logs for language detection
- Verify STT is detecting correctly

---

**Ready?** Run `python -m app.agent.runner dev` and start talking! 🎤
