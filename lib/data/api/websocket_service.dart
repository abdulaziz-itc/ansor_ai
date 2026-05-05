import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../models/api_response.dart';
import 'package:logger/logger.dart';

final webSocketServiceProvider = Provider<WebSocketService>((ref) {
  return WebSocketService();
});

class WebSocketService {
  WebSocketChannel? _channel;
  final _logger = Logger();
  
  // StreamController orqali natijalarni UI'ga uzatamiz
  final _resultController = StreamController<AIProcessingResult>.broadcast();
  Stream<AIProcessingResult> get results => _resultController.stream;

  void connect(int userId) {
    final url = ApiConstants.wsUrl(userId);
    _logger.d('Connecting to WebSocket: $url');
    
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      
      _channel!.stream.listen(
        (message) {
          _logger.d('WebSocket Message Received: $message');
          _handleMessage(message);
        },
        onError: (error) {
          _logger.e('WebSocket Error: $error');
          _reconnect(userId);
        },
        onDone: () {
          _logger.w('WebSocket Connection Closed');
          _reconnect(userId);
        },
      );
    } catch (e) {
      _logger.e('WebSocket Connection Exception: $e');
    }
  }

  void _handleMessage(dynamic message) {
    try {
      final data = jsonDecode(message);
      final type = data['type'];
      
      if (type == 'ai_processing_complete') {
        final result = AIProcessingResult.fromJson(data['data']);
        _resultController.add(result);
      }
    } catch (e) {
      _logger.e('Error handling WebSocket message: $e');
    }
  }

  void _reconnect(int userId) {
    Future.delayed(const Duration(seconds: 5), () {
      _logger.i('Attempting to reconnect WebSocket...');
      connect(userId);
    });
  }

  void disconnect() {
    _channel?.sink.close();
    _resultController.close();
  }
}
