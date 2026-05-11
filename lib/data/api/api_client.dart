import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import 'package:logger/logger.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final dioProvider = Provider<Dio>((ref) {
  const storage = FlutterSecureStorage();
  
  final dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: const Duration(seconds: 120),
    receiveTimeout: const Duration(seconds: 120),
  ));

  // Token Injector Interceptor
  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      final token = await storage.read(key: 'auth_token');
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      return handler.next(options);
    },
    onError: (DioException e, handler) {
      Logger().e('API Error: ${e.type} - ${e.message}\n'
          'URL: ${e.requestOptions.uri}\n'
          'Data: ${e.requestOptions.data}');
      return handler.next(e);
    },
  ));

  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
    logPrint: (obj) => Logger().d(obj),
  ));

  return dio;
});

class ApiClient {
  final Dio _dio;

  ApiClient(this._dio);

  Future<Response> uploadVideo(int chatId, String filePath) async {
    final file = File(filePath);
    final bytes = await file.readAsBytes();

    return await _dio.post(
      ApiConstants.uploadVideo(chatId), 
      data: bytes,
      options: Options(
        headers: {
          Headers.contentTypeHeader: 'application/octet-stream',
          Headers.contentLengthHeader: bytes.length,
        },
      ),
    );
  }

  Future<Response> register(Map<String, dynamic> data) async {
    return await _dio.post('${ApiConstants.baseApiUrl}/auth/register', data: data);
  }

  Future<Response> login(String username, String password) async {
    // Standard OAuth2 application/x-www-form-urlencoded request format for FastAPI
    final data = {
      'username': username,
      'password': password,
    };
    return await _dio.post(
      '${ApiConstants.baseApiUrl}/auth/login',
      data: data,
      options: Options(
        contentType: Headers.formUrlEncodedContentType,
      ),
    );
  }

  Future<Response> loginWithGoogle(String idToken) async {
    return await _dio.post(
      '${ApiConstants.baseApiUrl}/auth/google',
      data: {'id_token': idToken},
    );
  }

  Future<Response> getChats() async {
    return await _dio.get(ApiConstants.getChats);
  }

  Future<Response> getMessages(int chatId) async {
    return await _dio.get(ApiConstants.getMessages(chatId));
  }

  Future<Response> share(Map<String, dynamic> data) async {
    return await _dio.post(ApiConstants.share, data: data);
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiClient(dio);
});
