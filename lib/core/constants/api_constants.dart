class ApiConstants {
  // Live server URL
  static const String baseUrl = 'https://ansor.joida.uz'; 
  static const String baseApiUrl = '$baseUrl/api/v1';
  
  // Endpoints
  static String uploadVideo(int chatId) => '/api/v1/chats/$chatId/upload-video';
  static String getMessages(int chatId) => '/api/v1/chats/$chatId/messages';
  static const String getChats = '/api/v1/chats';
  static const String share = '/api/v1/share';
  
  // WebSocket
  static String wsUrl(int userId) => 'wss://ansor.joida.uz/api/v1/ws/$userId';
  
  // Static files
  static String audioUrl(String filename) => '$baseUrl/static/audio/$filename';
}
