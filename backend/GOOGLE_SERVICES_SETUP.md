# Google Cloud Services Setup Guide

## ✅ Working Services

### 1. Speech-to-Text (STT) - WORKING ✅
- Status: Fully functional
- Project: project-d8fe05cb-90bb-4815-aca
- No additional setup needed

### 2. Text-to-Speech (TTS) - WORKING ✅
- Status: Fully functional  
- Generated test audio: `test_tts_output.mp3`
- No additional setup needed

### 3. Gemini AI API - NEEDS ACTIVATION ⚠️

## Gemini API Setup Options

You have TWO options to enable Gemini:

### Option A: Enable Vertex AI (Recommended for your service account)

1. Visit: https://console.developers.google.com/apis/api/aiplatform.googleapis.com/overview?project=project-d8fe05cb-90bb-4815-aca

2. Click "Enable" button

3. Wait 2-3 minutes for propagation

4. Re-run test: `python test_google_services.py`

### Option B: Use Standalone Gemini API Key (Simpler)

1. Visit: https://aistudio.google.com/app/apikey

2. Create a new API key OR use existing key

3. Copy the API key

4. Update `backend/.env` file:
   ```
   GEMINI_API_KEY=your-actual-gemini-api-key-here
   ```

5. Re-run test: `python test_google_services.py`

## Current Costs

You mentioned ₹1000 paid for these services. Here's what's included:

- ✅ **STT (Speech-to-Text)**: Paid, working
- ✅ **TTS (Text-to-Speech)**: Paid, working  
- ⚠️ **Gemini API**: Just needs activation (one of the options above)

## Test Command

```bash
cd backend
python test_google_services.py
```

## Generated Files

- `test_tts_output.mp3` - Sample audio from TTS test (safe to delete)

## Security

- ✅ Credentials file protected in `.gitignore`
- ✅ API keys in `.env` (not committed to git)
- ✅ Service account credentials secured
