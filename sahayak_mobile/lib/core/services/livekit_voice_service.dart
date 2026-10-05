import 'dart:async';
import 'dart:convert';

import 'package:livekit_client/livekit_client.dart';
import 'package:logger/logger.dart';

import 'api_client.dart';
import '../config/api_config.dart';

/// Voice UI event published by the Sahayak LiveKit agent
class VoiceUiEvent {
  final String type;
  final Map<String, dynamic> payload;

  const VoiceUiEvent(this.type, this.payload);

  @override
  String toString() => 'VoiceUiEvent(type: $type, payload: $payload)';
}

/// LiveKit voice connection service for Sahayak AI
class LiveKitVoiceService {
  static final Logger _logger = Logger(printer: PrettyPrinter(methodCount: 0));

  final ApiClient _api;
  final StreamController<VoiceUiEvent> _uiEvents =
      StreamController<VoiceUiEvent>.broadcast();

  Room? _room;
  EventsListener<RoomEvent>? _listener;
  bool _initialized = false;
  bool _connecting = false;

  LiveKitVoiceService({ApiClient? api}) : _api = api ?? ApiClient();

  Stream<VoiceUiEvent> get events => _uiEvents.stream;
  bool get isConnected => _room?.connectionState == ConnectionState.connected;
  bool get isConnecting => _connecting;
  ConnectionState? get connectionState => _room?.connectionState;

  bool get isMicrophoneEnabled {
    final participant = _room?.localParticipant;
    return participant?.isMicrophoneEnabled() ?? false;
  }

  /// Connect to LiveKit room
  Future<void> connect({
    String? participantName,
    String? language,
  }) async {
    if (_connecting || isConnected) {
      _logger.w('Already connecting or connected');
      return;
    }

    _connecting = true;
    _logger.i('Connecting to LiveKit voice service...');

    try {
      // Request guest session to enable contextual memory for the agent
      final guestSession = await _api.post('/api/guest-sessions', {});
      final guestSessionId = guestSession['session_id'];
      final guestSessionSecret = guestSession['session_secret'];

      // Request credentials from backend
      final credentials = await _api.post(ApiConfig.voiceToken, {
        if (participantName != null && participantName.trim().isNotEmpty)
          'participant_name': participantName.trim(),
        if (language != null && language.isNotEmpty) 'language': language,
        'participant_attributes': {
          'guest_session_id': guestSessionId,
          'guest_session_secret': guestSessionSecret,
        },
      });

      final url = credentials['server_url']?.toString() ?? '';
      final token = credentials['participant_token']?.toString() ?? '';

      if (url.isEmpty || token.isEmpty) {
        throw StateError('Voice service returned incomplete credentials.');
      }

      _logger.d('LiveKit credentials received: $url');

      // Initialize LiveKit once
      if (!_initialized) {
        await LiveKitClient.initialize();
        _initialized = true;
      }

      // Clean up any stale connection
      await disconnect();

      // Create room and listener
      final room = Room();
      final listener = room.createListener();

      listener
        ..on<DataReceivedEvent>(_onDataReceived)
        ..on<RoomDisconnectedEvent>((event) {
          _logger.w('Room disconnected: ${event.reason}');
          _uiEvents.add(const VoiceUiEvent('disconnected', {}));
        })
        ..on<ParticipantConnectedEvent>((event) {
          _logger.d('Participant connected: ${event.participant.identity}');
        })
        ..on<TrackPublishedEvent>((event) {
          _logger.d('Track published: ${event.publication.sid}');
        })
        ..on<TrackSubscribedEvent>((event) {
          _logger.d('Track subscribed: ${event.track.sid}');
        })
        ..on<TranscriptionEvent>((event) {
          _onTranscriptionReceived(event);
        });

      _room = room;
      _listener = listener;

      // Connect to LiveKit room (WebRTC handshake)
      await room.connect(url, token);

      final participant = room.localParticipant;
      if (participant == null) {
        throw StateError('No local participant after room connect.');
      }

      // ✅ Fire connected event BEFORE enabling mic so UI updates immediately
      _uiEvents.add(VoiceUiEvent('connected', {
        'room_name': credentials['room_name']?.toString(),
        'session_id': credentials['session_id']?.toString(),
      }));

      // Enable microphone with retry — do NOT throw if this fails
      await _enableMicrophoneWithRetry(participant);

      _logger.i('✅ Voice session ready');
    } catch (error) {
      _logger.e('Failed to connect: $error');
      _uiEvents.add(VoiceUiEvent('error', {'message': '$error'}));
      await disconnect();
      rethrow;
    } finally {
      _connecting = false;
    }
  }

  /// Try to enable microphone up to 2 times with a delay between attempts
  Future<void> _enableMicrophoneWithRetry(LocalParticipant participant) async {
    for (int attempt = 1; attempt <= 2; attempt++) {
      try {
        await participant.setMicrophoneEnabled(true);
        _logger.i('Microphone enabled (attempt $attempt)');
        return;
      } catch (e) {
        _logger.w('Mic enable attempt $attempt failed: $e');
        if (attempt < 2) {
          await Future.delayed(const Duration(milliseconds: 1000));
        } else {
          _logger.e('Microphone could not be enabled — staying connected (listen-only)');
        }
      }
    }
  }

  /// Enable or disable microphone
  Future<void> setMicrophoneEnabled(bool enabled) async {
    final participant = _room?.localParticipant;
    if (participant == null || !isConnected) return;
    try {
      await participant.setMicrophoneEnabled(enabled);
    } catch (e) {
      _logger.e('Failed to toggle microphone: $e');
    }
  }

  /// Send text data via LiveKit data channel
  Future<void> sendText(String text) async {
    final participant = _room?.localParticipant;
    if (participant == null || !isConnected) return;
    try {
      final payload = jsonEncode({
        'id': DateTime.now().millisecondsSinceEpoch.toString(),
        'message': text,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });
      await participant.publishData(
        utf8.encode(payload),
        topic: 'lk-chat',
      );
      _logger.d('Sent text data: $text');
    } catch (e) {
      _logger.e('Failed to send text data: $e');
    }
  }

  /// Disconnect from LiveKit room
  Future<void> disconnect() async {
    _logger.i('Disconnecting from voice service...');

    final listener = _listener;
    final room = _room;

    _listener = null;
    _room = null;

    if (listener != null) {
      await listener.dispose();
    }

    if (room != null) {
      await room.disconnect();
      await room.dispose();
    }

    _logger.d('Disconnected from voice service');
  }

  /// Handle transcription received from LiveKit room
  void _onTranscriptionReceived(TranscriptionEvent event) {
    try {
      final segments = event.segments;
      if (segments.isEmpty) return;

      // Get the participant who is speaking
      final participantIdentity = event.participant.identity;
      final isAgent = participantIdentity.contains('agent') || participantIdentity.contains('sahayak');
      
      // Combine all segments into one text
      final text = segments.map((s) => s.text).join(' ').trim();
      
      if (text.isEmpty) return;

      _logger.i('📝 Transcription: ${isAgent ? "AGENT" : "USER"} -> $text');
      
      // Emit transcript event
      final eventType = isAgent ? 'agent_transcript' : 'user_transcript';
      _uiEvents.add(VoiceUiEvent(eventType, {
        'text': text,
        'participant': participantIdentity,
      }));
    } catch (e) {
      _logger.e('Error processing transcription: $e');
    }
  }

  /// Handle data received from LiveKit
  void _onDataReceived(DataReceivedEvent event) {
    _logger.d('📡 Data received on topic: ${event.topic}');

    // Handle UI control events
    if (event.topic == 'sahayak.ui' || event.topic == 'vyamit.ui') {
      try {
        final decoded = jsonDecode(utf8.decode(event.data));
        if (decoded is! Map) return;

        final payload = Map<String, dynamic>.from(decoded);
        final type = payload.remove('type')?.toString();

        if (type == null || type.isEmpty) return;

        _logger.d('📡 Publishing VoiceUiEvent: type=$type');
        _uiEvents.add(VoiceUiEvent(type, payload));
      } on FormatException catch (e) {
        _logger.e('Failed to parse data: $e');
      } catch (e) {
        _logger.e('Error processing data: $e');
      }
      return;
    }
  }

  Future<void> dispose() async {
    _logger.d('Disposing LiveKitVoiceService');
    await disconnect();
    await _uiEvents.close();
  }
}
