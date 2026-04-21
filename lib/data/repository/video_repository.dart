import '../api/api_client.dart';
import '../models/api_response.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final videoRepositoryProvider = Provider<VideoRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return VideoRepository(apiClient);
});

class VideoRepository {
  final ApiClient _apiClient;

  VideoRepository(this._apiClient);

  Future<VideoUploadResponse> uploadVideo(String filePath) async {
    final response = await _apiClient.uploadVideo(filePath);
    return VideoUploadResponse.fromJson(response.data);
  }
}
