import '../../core/constants/api_constants.dart';

class VideoUploadResponse {
  final String status;
  final int messageId;

  VideoUploadResponse({
    required this.status,
    required this.messageId,
  });

  factory VideoUploadResponse.fromJson(Map<String, dynamic> json) {
    return VideoUploadResponse(
      status: json['status'] ?? '',
      messageId: json['message_id'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'message_id': messageId,
    };
  }
}

class AIProcessingResult {
  final int messageId;
  final int chatId;
  final String text;
  final String audioUrl;
  final DateTime createdAt;

  AIProcessingResult({
    required this.messageId,
    required this.chatId,
    required this.text,
    required this.audioUrl,
    required this.createdAt,
  });

  factory AIProcessingResult.fromJson(Map<String, dynamic> json) {
    String url = json['audio_url'] ?? '';
    if (url.startsWith('/')) {
      url = '${ApiConstants.baseUrl}$url';
    }

    return AIProcessingResult(
      messageId: json['message_id'] ?? 0,
      chatId: json['chat_id'] ?? 0,
      text: json['text'] ?? '',
      audioUrl: url,
      createdAt: json['created_at'] != null 
        ? DateTime.parse(json['created_at']) 
        : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message_id': messageId,
      'chat_id': chatId,
      'text': text,
      'audio_url': audioUrl,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
