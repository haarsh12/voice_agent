# Vyamit Voice Assistant - Flutter Android App

Flutter mobile app for Vyamit Voice Assistant with LiveKit integration.

## Features

✅ Real-time voice conversation
✅ LiveKit integration
✅ Same backend as web app
✅ Beautiful UI matching web frontend
✅ Hindi, Marathi, and English support
✅ Microphone permissions handling
✅ Connection status indicators

## Prerequisites

- Flutter SDK (3.0+)
- Android device or emulator
- Backend server running

## Setup

### 1. Backend Must Be Running

Make sure your backend is running:
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start agent worker
python -m app.agent.runner start
```

### 2. Update API URL (For Real Device)

If testing on a real Android device, update the API URL in `lib/services/api_service.dart`:

```dart
// Find your computer's IP address:
// Windows: ipconfig
// Look for "IPv4 Address" (e.g., 192.168.1.100)

static const String baseUrl = 'http://192.168.1.XXX:8000';
```

For emulator, use:
- Android Emulator: `http://10.0.2.2:8000`
- iOS Simulator: `http://127.0.0.1:8000`

### 3. Install Dependencies

```bash
flutter pub get
```

## Running the App

### On Android Emulator

```bash
# Start emulator first, then:
flutter run
```

### On Real Android Device

1. Enable Developer Options on your phone
2. Enable USB Debugging
3. Connect phone via USB
4. Run:
```bash
flutter devices  # Check device is connected
flutter run
```

### On Chrome (Web)

```bash
flutter run -d chrome
```

## Project Structure

```
android_app/
├── lib/
│   ├── main.dart                          # App entry point
│   ├── screens/
│   │   └── voice_assistant_screen.dart   # Main UI
│   └── services/
│       └── api_service.dart              # Backend API calls
├── android/
│   └── app/src/main/AndroidManifest.xml # Permissions
└── pubspec.yaml                          # Dependencies
```

## How It Works

1. **Health Check**: App checks if backend is running
2. **Connect**: User clicks connect button
3. **Token Request**: App requests LiveKit token from backend
4. **LiveKit Connection**: Connects to LiveKit room
5. **Voice Session**: Real-time conversation starts
6. **Transcription**: Deepgram transcribes speech
7. **AI Response**: Mistral generates response
8. **Speech Output**: Cartesia speaks the response

## Dependencies

- **livekit_client**: LiveKit Flutter SDK for real-time communication
- **http**: HTTP requests to backend API
- **permission_handler**: Microphone permission handling

## Permissions

Required Android permissions (already configured):
- `INTERNET` - Network access
- `RECORD_AUDIO` - Microphone access
- `MODIFY_AUDIO_SETTINGS` - Audio settings
- `BLUETOOTH` - Bluetooth audio
- `BLUETOOTH_CONNECT` - Bluetooth connection

## Troubleshooting

### "Backend not reachable"

**Solution**: Make sure backend is running and accessible:
```bash
# Test from your phone's browser:
http://YOUR_PC_IP:8000/api/health
```

### "Microphone permission denied"

**Solution**: Go to phone Settings → Apps → Vyamit → Permissions → Allow Microphone

### "Connection failed"

**Checklist**:
1. ✅ Backend running on port 8000
2. ✅ Agent worker running
3. ✅ Phone and PC on same WiFi network
4. ✅ Firewall allows port 8000
5. ✅ Correct IP address in api_service.dart

### Finding Your PC's IP Address

**Windows**:
```bash
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
```

**Mac/Linux**:
```bash
ifconfig
# Look for "inet" under your WiFi interface
```

## Testing

### 1. Test on Emulator First

```bash
flutter run
```

### 2. Test Backend Connection

```bash
# In Dart DevTools console:
await ApiService().getHealth();
```

### 3. Test on Real Device

1. Update API URL with your PC's IP
2. Connect phone via USB
3. Run `flutter run`

## Building APK

### Debug APK
```bash
flutter build apk --debug
```

### Release APK
```bash
flutter build apk --release
```

APK location: `build/app/outputs/flutter-apk/app-release.apk`

## Next Steps

- [ ] Add transcript display
- [ ] Add audio visualization
- [ ] Add settings screen
- [ ] Add language selection
- [ ] Add voice selection
- [ ] Add conversation history
- [ ] Add push notifications

## Notes

- Backend API stays exactly the same
- No changes needed to agent worker
- Uses same LiveKit room system
- Same STT/LLM/TTS providers
- Same multi-language support

## Support

Same backend configuration as web app. See main project README for provider setup.
