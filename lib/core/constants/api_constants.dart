class ApiConstants {
  // Live server URL
  static const String baseUrl = 'https://ansor.joida.uz'; 
  
  // Endpoints
  static String uploadVideo(int chatId) => '/chats/$chatId/upload';
  static String getMessages(int chatId) => '/chats/$chatId/messages';
  static const String getChats = '/chats';
  static const String share = '/share';
  
  // WebSocket
  static String wsUrl(int userId) => 'wss://ansor.joida.uz/ws/$userId';
  
  // Static files
  static String audioUrl(String filename) => '$baseUrl/static/audio/$filename';
}
