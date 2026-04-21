class VideoUploadResponse {
  final String text;
  final String audioUrl;
  final DateTime createdAt;

  VideoUploadResponse({
    required this.text,
    required this.audioUrl,
    required this.createdAt,
  });

  factory VideoUploadResponse.fromJson(Map<String, dynamic> json) {
    return VideoUploadResponse(
      text: json['text'] ?? '',
      audioUrl: json['audio_url'] ?? '',
      createdAt: json['created_at'] != null 
        ? DateTime.parse(json['created_at']) 
        : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'text': text,
      'audio_url': audioUrl,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
