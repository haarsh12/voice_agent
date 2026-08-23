# Google Cloud TTS Voice Configuration

## Overview

This project now uses **Google Cloud Text-to-Speech (TTS)** for natural-sounding Hindi, Marathi, and English voice synthesis. Google Cloud TTS provides significantly more natural voices for Indic languages compared to other providers.

## Voice Quality Tiers

Google Cloud TTS offers several voice quality tiers:

1. **Neural2** - Highest quality, most natural-sounding (recommended)
2. **Wavenet** - High quality, natural-sounding
3. **Standard** - Basic quality, lower cost

## Available Voices

### Hindi (hi-IN)

#### Neural2 Voices (Best Quality)
- `hi-IN-Neural2-A` - Female voice (default)
- `hi-IN-Neural2-B` - Male voice
- `hi-IN-Neural2-C` - Male voice
- `hi-IN-Neural2-D` - Female voice

#### Wavenet Voices (High Quality)
- `hi-IN-Wavenet-A` - Female voice
- `hi-IN-Wavenet-B` - Male voice
- `hi-IN-Wavenet-C` - Male voice
- `hi-IN-Wavenet-D` - Female voice

#### Standard Voices (Basic Quality)
- `hi-IN-Standard-A` - Female voice
- `hi-IN-Standard-B` - Male voice
- `hi-IN-Standard-C` - Male voice
- `hi-IN-Standard-D` - Female voice

### Marathi (mr-IN)

#### Wavenet Voices (Best Available for Marathi)
- `mr-IN-Wavenet-A` - Female voice (default)
- `mr-IN-Wavenet-B` - Male voice
- `mr-IN-Wavenet-C` - Female voice

#### Standard Voices
- `mr-IN-Standard-A` - Female voice
- `mr-IN-Standard-B` - Male voice
- `mr-IN-Standard-C` - Female voice

Note: Neural2 voices are not yet available for Marathi. Wavenet provides excellent quality.

### English (India) - en-IN

#### Neural2 Voices (Best Quality)
- `en-IN-Neural2-A` - Female voice (default for Indian English)
- `en-IN-Neural2-B` - Male voice
- `en-IN-Neural2-C` - Male voice
- `en-IN-Neural2-D` - Female voice

#### Wavenet Voices
- `en-IN-Wavenet-A` - Female voice
- `en-IN-Wavenet-B` - Male voice
- `en-IN-Wavenet-C` - Male voice
- `en-IN-Wavenet-D` - Female voice

### English (US) - en-US

#### Neural2 Voices
- `en-US-Neural2-A` - Male voice
- `en-US-Neural2-C` - Female voice
- `en-US-Neural2-D` - Male voice
- `en-US-Neural2-E` - Female voice
- `en-US-Neural2-F` - Female voice
- `en-US-Neural2-G` - Female voice
- `en-US-Neural2-H` - Female voice
- `en-US-Neural2-I` - Male voice
- `en-US-Neural2-J` - Male voice

## Configuration

### Environment Variables

```env
# Google Cloud TTS Configuration
GOOGLE_TTS_LANGUAGE=hi-IN
GOOGLE_TTS_VOICE=hi-IN-Neural2-A
GOOGLE_TTS_SPEED=1.0
GOOGLE_TTS_PITCH=0.0
```

### Voice Selection Parameters

- **GOOGLE_TTS_LANGUAGE**: Language code (hi-IN, mr-IN, en-IN, en-US)
- **GOOGLE_TTS_VOICE**: Specific voice name (see lists above)
- **GOOGLE_TTS_SPEED**: Speaking rate (0.25 to 4.0, default: 1.0)
  - 0.5 = Half speed (slower)
  - 1.0 = Normal speed
  - 1.5 = 1.5x speed (faster)
- **GOOGLE_TTS_PITCH**: Voice pitch (-20.0 to 20.0, default: 0.0)
  - Negative values = Lower pitch
  - 0 = Normal pitch
  - Positive values = Higher pitch

## Automatic Language Switching

The system automatically detects the language you're speaking (Hindi, Marathi, or English) and switches to the appropriate voice:

- **Hindi detected** → Uses Hindi Neural2 voice (`hi-IN-Neural2-A`)
- **Marathi detected** → Uses Marathi Wavenet voice (`mr-IN-Wavenet-A`)
- **English detected** → Uses Indian English Neural2 voice (`en-IN-Neural2-A`)

This happens automatically based on Google Cloud STT's language detection.

## Voice Customization

### Changing Default Voice

To change the default voice, update your `.env` file:

```env
# For Hindi Male voice
GOOGLE_TTS_VOICE=hi-IN-Neural2-B

# For Marathi Male voice
GOOGLE_TTS_VOICE=mr-IN-Wavenet-B

# For English (India) Male voice
GOOGLE_TTS_VOICE=en-IN-Neural2-B
```

### Adjusting Speed and Pitch

```env
# Slower, deeper voice (good for clarity)
GOOGLE_TTS_SPEED=0.9
GOOGLE_TTS_PITCH=-2.0

# Faster, higher voice (good for quick responses)
GOOGLE_TTS_SPEED=1.2
GOOGLE_TTS_PITCH=2.0
```

## Testing Different Voices

To test different voices, you can modify the `voice_map` in `app/agent/providers.py`:

```python
voice_map = {
    "hi": "hi-IN-Neural2-B",      # Change to Male Hindi voice
    "mr": "mr-IN-Wavenet-B",      # Change to Male Marathi voice
    "en": "en-IN-Neural2-C",      # Change to different English voice
}
```

## Voice Quality Comparison

| Feature | Neural2 | Wavenet | Standard |
|---------|---------|---------|----------|
| Naturalness | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Emotional Expression | ★★★★★ | ★★★★☆ | ★★☆☆☆ |
| Pronunciation | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Latency | Low | Low | Very Low |
| Cost | Higher | Medium | Lower |

## Recommendations

### For Production (Best Quality)
```env
GOOGLE_TTS_VOICE=hi-IN-Neural2-A
GOOGLE_TTS_SPEED=1.0
GOOGLE_TTS_PITCH=0.0
```

### For Development (Balance of Quality & Cost)
```env
GOOGLE_TTS_VOICE=hi-IN-Wavenet-A
GOOGLE_TTS_SPEED=1.0
GOOGLE_TTS_PITCH=0.0
```

### For Testing (Lower Cost)
```env
GOOGLE_TTS_VOICE=hi-IN-Standard-A
GOOGLE_TTS_SPEED=1.0
GOOGLE_TTS_PITCH=0.0
```

## Troubleshooting

### Voice Sounds Robotic
- Ensure you're using Neural2 or Wavenet voices
- Check that `GOOGLE_TTS_SPEED` is between 0.9 and 1.1
- Verify `GOOGLE_TTS_PITCH` is between -5 and 5

### Wrong Language Voice
- Check that language detection is working in STT
- Verify the `voice_map` in `providers.py` has correct mappings
- Check logs for language detection: `stt_transcript language=hi`

### No Audio Output
- Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Check that the Google Cloud project has Text-to-Speech API enabled
- Verify credentials file has necessary permissions

## API Costs

Google Cloud TTS pricing (as of 2024):
- **Neural2 voices**: ~$16.00 per 1M characters
- **Wavenet voices**: ~$16.00 per 1M characters  
- **Standard voices**: ~$4.00 per 1M characters

Typical usage:
- 1 minute of speech ≈ 500-800 characters
- 1 hour conversation ≈ 30,000-50,000 characters
- Cost per hour: ~$0.50-0.80 (Neural2/Wavenet) or ~$0.12-0.20 (Standard)

## Additional Resources

- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)
- [Supported Voices List](https://cloud.google.com/text-to-speech/docs/voices)
- [LiveKit Google Plugin](https://docs.livekit.io/agents/models/tts/google/)
- [SSML for Voice Customization](https://cloud.google.com/text-to-speech/docs/ssml)
