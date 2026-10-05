import 'package:flutter/material.dart';
import '../../../core/services/livekit_voice_service.dart';

enum VoiceConnectionState {
  disconnected,
  connecting,
  connected,
  error,
}

/// Manages LiveKit voice connection and conversation state
class VoiceProvider extends ChangeNotifier {
  final LiveKitVoiceService _voiceService = LiveKitVoiceService();

  VoiceConnectionState _connectionState = VoiceConnectionState.disconnected;
  bool _isMicEnabled = false;
  String? _errorMessage;
  String? _sessionId;
  String? _roomName;
  final List<Map<String, dynamic>> _transcript = [];
  Map<String, dynamic>? _lastCitations; // Store latest citations

  VoiceConnectionState get connectionState => _connectionState;
  bool get isMicEnabled => _isMicEnabled;
  String? get errorMessage => _errorMessage;
  String? get sessionId => _sessionId;
  String? get roomName => _roomName;
  List<Map<String, dynamic>> get transcript => List.unmodifiable(_transcript);
  Map<String, dynamic>? get lastCitations => _lastCitations;
  bool get isConnected => _connectionState == VoiceConnectionState.connected;

  VoiceProvider() {
    _listenToVoiceEvents();
  }

  /// Listen to LiveKit voice events
  void _listenToVoiceEvents() {
    _voiceService.events.listen((event) {
      debugPrint('Voice event: ${event.type}');

      switch (event.type) {
        case 'connected':
          _connectionState = VoiceConnectionState.connected;
          _sessionId = event.payload['session_id'];
          _roomName = event.payload['room_name'];
          _errorMessage = null;
          break;

        case 'disconnected':
          _connectionState = VoiceConnectionState.disconnected;
          _isMicEnabled = false;
          break;

        case 'error':
          _connectionState = VoiceConnectionState.error;
          _errorMessage = event.payload['message'] ?? 'Unknown error';
          break;

        case 'transcript':
          _addToTranscript(event.payload);
          break;

        case 'agent_response':
          _addToTranscript({
            'speaker': 'agent',
            'text': event.payload['text'],
            'timestamp': DateTime.now().toIso8601String(),
          });
          break;

        case 'citations':
          // Store citations for display with agent messages
          _lastCitations = event.payload;
          notifyListeners();
          break;

        default:
          debugPrint('Unhandled event type: ${event.type}');
      }

      notifyListeners();
    });
  }

  /// Connect to voice service
  Future<void> connect({String? language}) async {
    if (_connectionState == VoiceConnectionState.connecting ||
        _connectionState == VoiceConnectionState.connected) {
      return;
    }

    _connectionState = VoiceConnectionState.connecting;
    _errorMessage = null;
    _transcript.clear();
    _lastCitations = null;
    notifyListeners();

    try {
      await _voiceService.connect(
        participantName: 'Mobile User',
        language: language,
      );

      _isMicEnabled = _voiceService.isMicrophoneEnabled;
      // Connection state will be updated by event listener
    } catch (e) {
      _connectionState = VoiceConnectionState.error;
      _errorMessage = 'Failed to connect: $e';
      notifyListeners();
    }
  }

  /// Disconnect from voice service
  Future<void> disconnect() async {
    try {
      await _voiceService.disconnect();
      _connectionState = VoiceConnectionState.disconnected;
      _isMicEnabled = false;
      _sessionId = null;
      _roomName = null;
      notifyListeners();
    } catch (e) {
      debugPrint('Disconnect error: $e');
    }
  }

  /// Toggle microphone
  Future<void> toggleMicrophone() async {
    if (_connectionState != VoiceConnectionState.connected) {
      return;
    }

    try {
      final newState = !_isMicEnabled;
      await _voiceService.setMicrophoneEnabled(newState);
      _isMicEnabled = newState;
      notifyListeners();
    } catch (e) {
      debugPrint('Toggle microphone error: $e');
    }
  }

  /// Send text message
  Future<void> sendText(String text) async {
    if (_connectionState != VoiceConnectionState.connected || text.trim().isEmpty) {
      return;
    }
    
    // Add to local transcript immediately
    _addToTranscript({
      'speaker': 'user',
      'text': text,
      'timestamp': DateTime.now().toIso8601String(),
    });
    
    await _voiceService.sendText(text);
  }

  /// Add message to transcript
  void _addToTranscript(Map<String, dynamic> message) {
    final entry = {
      'speaker': message['speaker'] ?? 'user',
      'text': message['text'] ?? '',
      'timestamp': message['timestamp'] ?? DateTime.now().toIso8601String(),
    };
    
    // Attach citations to agent messages
    if (entry['speaker'] == 'agent' && _lastCitations != null) {
      entry['citations'] = _lastCitations;
      _lastCitations = null; // Clear after attaching
    }
    
    _transcript.add(entry);

    // Limit transcript size
    if (_transcript.length > 100) {
      _transcript.removeAt(0);
    }
  }

  /// Clear transcript
  void clearTranscript() {
    _transcript.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _voiceService.dispose();
    super.dispose();
  }
}
