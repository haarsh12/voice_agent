# Sahayak Mobile App Setup Guide

## Overview

The `sahayak_mobile` directory contains the Flutter Android application for Sahayak AI.

## Project Structure

```
voice_stream/
├── backend/              # FastAPI backend with LiveKit agent
├── frontend/             # React web application
└── sahayak_mobile/       # Flutter Android application (NEW)
    ├── android/          # Android-specific configuration
    ├── lib/              # Dart source code
    │   └── main.dart     # Application entry point
    ├── test/             # Tests
    ├── pubspec.yaml      # Dependencies
    ├── setup_flutter.bat # Setup script
    └── run_app.bat       # Run script
```

## Prerequisites

### 1. Install Flutter

Download and install Flutter SDK from: https://docs.flutter.dev/get-started/install/windows

Add Flutter to your PATH:
```
C:\path\to\flutter\bin
```

### 2. Install Android Studio

Download from: https://developer.android.com/studio

During installation, make sure to install:
- Android SDK
- Android SDK Platform-Tools
- Android SDK Build-Tools
- Android Emulator

### 3. Accept Android Licenses

```bash
flutter doctor --android-licenses
```

### 4. Verify Installation

```bash
flutter doctor
```

All checks should be green or at least Android toolchain should be ready.

## Quick Start

### Option 1: Using Scripts (Recommended)

1. **Setup the project:**
   ```bash
   cd sahayak_mobile
   setup_flutter.bat
   ```

2. **Connect device or start emulator:**
   - Physical device: Enable USB debugging and connect via USB
   - Emulator: Start from Android Studio (Tools → Device Manager)

3. **Run the app:**
   ```bash
   run_app.bat
   ```

### Option 2: Manual Commands

```bash
cd sahayak_mobile

# Install dependencies
flutter pub get

# Check devices
flutter devices

# Run the app
flutter run
```

## Development Workflow

### 1. Start Backend Server

The mobile app needs the backend server running:

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Configure Backend URL

For development:
- **Android Emulator**: Use `http://10.0.2.2:8000`
- **Physical Device**: Use your computer's local IP (e.g., `http://192.168.1.100:8000`)

### 3. Hot Reload

While the app is running:
- Press `r` in terminal for hot reload (fast)
- Press `R` for hot restart (clears state)
- Press `q` to quit

## Building APK

### Debug APK (for testing)

```bash
cd sahayak_mobile
flutter build apk --debug
```

Output: `build/app/outputs/flutter-apk/app-debug.apk`

### Release APK (for distribution)

```bash
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

**Note**: Release builds require signing configuration in `android/app/build.gradle.kts`

## Testing on Physical Device

### 1. Enable Developer Mode

On your Android phone:
1. Go to Settings → About Phone
2. Tap "Build Number" 7 times
3. Developer options will be enabled

### 2. Enable USB Debugging

1. Go to Settings → Developer Options
2. Enable "USB Debugging"
3. Connect phone via USB
4. Accept the debugging prompt on your phone

### 3. Verify Connection

```bash
adb devices
```

You should see your device listed.

### 4. Run the App

```bash
flutter run
```

## Troubleshooting

### Flutter Doctor Issues

```bash
# Check what's missing
flutter doctor -v

# Accept Android licenses
flutter doctor --android-licenses
```

### Gradle Build Errors

```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

### Device Not Detected

```bash
# Restart ADB
adb kill-server
adb start-server

# Check devices
adb devices
flutter devices
```

### Port Already in Use (Backend)

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <process_id> /F
```

## Project Configuration

### Package Details

- **Package Name**: `com.sahayak.sahayak_mobile`
- **Application ID**: `com.sahayak.sahayak_mobile`
- **Min SDK**: 21 (Android 5.0 Lollipop)
- **Target SDK**: Latest
- **Compile SDK**: Latest

### Dependencies

Main dependencies are defined in `pubspec.yaml`:
- Flutter SDK
- Material Design (built-in)
- Cupertino Icons (iOS-style icons)

Additional dependencies will be added as features are implemented:
- HTTP client for API calls
- LiveKit SDK for voice streaming
- State management (Provider/Riverpod/Bloc)
- Local storage (SharedPreferences/Hive)

## Next Steps

1. ✅ Flutter project created
2. ⏳ Design app architecture
3. ⏳ Implement authentication (OTP)
4. ⏳ Integrate LiveKit for voice
5. ⏳ Add language selection
6. ⏳ Implement voice recording
7. ⏳ Add real-time transcription
8. ⏳ Test on multiple devices

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Flutter Cookbook](https://docs.flutter.dev/cookbook)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
- [Android Developers](https://developer.android.com/)
- [LiveKit Flutter SDK](https://docs.livekit.io/client-sdk-flutter/)

## Support

For issues with:
- Flutter setup: Check Flutter documentation
- Android configuration: Check Android Studio settings
- Backend connection: Ensure backend is running on correct port
- Device detection: Verify USB debugging is enabled

---

**Created**: $(Get-Date -Format "yyyy-MM-dd")
**Project**: Sahayak AI Mobile
**Platform**: Android (Flutter)
