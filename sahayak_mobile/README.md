# Sahayak Mobile

Flutter Android application for Sahayak AI - A multilingual voice assistant supporting Hindi, Marathi, and English.

## Project Structure

```
sahayak_mobile/
├── android/          # Android-specific configuration
├── lib/             # Dart source code
│   └── main.dart    # Application entry point
├── test/            # Unit and widget tests
└── pubspec.yaml     # Project dependencies
```

## Prerequisites

- Flutter SDK 3.11.4 or higher
- Dart 3.11.4 or higher
- Android Studio or VS Code with Flutter extensions
- Android SDK (API level 21 or higher)
- Physical Android device or emulator

## Getting Started

### 1. Install Dependencies

```bash
cd sahayak_mobile
flutter pub get
```

### 2. Check Flutter Doctor

```bash
flutter doctor
```

Fix any issues reported by Flutter doctor.

### 3. Run on Android Device/Emulator

```bash
# List available devices
flutter devices

# Run the app
flutter run
```

Or use Android Studio's run button.

## Development

### Hot Reload

While the app is running:
- Press `r` to hot reload
- Press `R` to hot restart
- Press `q` to quit

### Build APK

```bash
# Debug APK
flutter build apk --debug

# Release APK
flutter build apk --release
```

The APK will be located at `build/app/outputs/flutter-apk/app-release.apk`

## Backend Integration

The mobile app connects to the Sahayak backend running at:
- Local development: `http://10.0.2.2:8000` (Android emulator)
- Physical device: `http://YOUR_LOCAL_IP:8000`

Make sure the backend server is running before testing the mobile app.

## Project Details

- **Package Name**: `com.sahayak.sahayak_mobile`
- **Minimum SDK**: Android API 21 (Lollipop)
- **Target SDK**: Latest stable

## Features (Coming Soon)

- [ ] Phone authentication with OTP
- [ ] Voice recording and streaming
- [ ] Real-time AI voice responses
- [ ] Multi-language support (Hindi, Marathi, English)
- [ ] LiveKit integration for voice communication
- [ ] Guest mode support

## Useful Commands

```bash
# Check dependencies
flutter pub outdated

# Update dependencies
flutter pub upgrade

# Clean build
flutter clean

# Analyze code
flutter analyze

# Run tests
flutter test
```

## Troubleshooting

### Gradle Build Issues

```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

### Device Not Detected

```bash
# Check USB debugging is enabled
adb devices

# Restart adb server
adb kill-server
adb start-server
```

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Flutter Android Setup](https://docs.flutter.dev/get-started/install/windows#android-setup)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
