import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import 'package:logger/logger.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ));

  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
    logPrint: (obj) => Logger().d(obj),
  ));

  dio.interceptors.add(InterceptorsWrapper(
    onError: (DioException e, handler) {
      Logger().e('API Error: ${e.type} - ${e.message}\n'
          'URL: ${e.requestOptions.uri}\n'
          'Data: ${e.requestOptions.data}');
      return handler.next(e);
    },
  ));

  return dio;
});

class ApiClient {
  final Dio _dio;

  ApiClient(this._dio);

  Future<Response> uploadVideo(String filePath) async {
    final formData = FormData.fromMap({
      'video': await MultipartFile.fromFile(filePath, filename: 'upload.mp4'),
    });

    return await _dio.post(ApiConstants.uploadVideo, data: formData);
  }

  Future<Response> getAudio(String id) async {
    return await _dio.get('${ApiConstants.getAudio}/$id');
  }

  Future<Response> share(Map<String, dynamic> data) async {
    return await _dio.post(ApiConstants.share, data: data);
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiClient(dio);
});
