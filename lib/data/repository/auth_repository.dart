import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../core/constants/api_constants.dart';
import '../api/api_client.dart';

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthRepository(apiClient, secureStorage);
});

class AuthRepository {
  final ApiClient _apiClient;
  final FlutterSecureStorage _secureStorage;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );

  static const String _tokenKey = 'auth_token';

  AuthRepository(this._apiClient, this._secureStorage);

  Future<String?> getToken() async {
    return await _secureStorage.read(key: _tokenKey);
  }

  Future<void> _saveToken(String token) async {
    await _secureStorage.write(key: _tokenKey, value: token);
  }

  Future<void> clearToken() async {
    await _secureStorage.delete(key: _tokenKey);
  }

  Future<bool> login(String username, String password) async {
    try {
      final response = await _apiClient.login(username, password);
      final token = response.data['access_token'];
      if (token != null) {
        await _saveToken(token);
        return true;
      }
      return false;
    } catch (e) {
      rethrow;
    }
  }

  Future<bool> register(String username, String email, String password, {String? fullName}) async {
    try {
      await _apiClient.register({
        'username': username,
        'email': email,
        'password': password,
        'full_name': fullName,
      });
      // Auto login right after registration
      return await login(username, password);
    } catch (e) {
      rethrow;
    }
  }

  Future<bool> signInWithGoogle() async {
    try {
      // Trigger initial interaction
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        // The user canceled the sign-in
        return false;
      }

      // Obtain authentication details
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      final String? idToken = googleAuth.idToken;

      if (idToken == null) {
        throw Exception('Could not retrieve Google ID token');
      }

      // Send this to the backend
      final response = await _apiClient.loginWithGoogle(idToken);
      final token = response.data['access_token'];
      
      if (token != null) {
        await _saveToken(token);
        return true;
      }
      return false;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> logout() async {
    await clearToken();
    try {
      await _googleSignIn.signOut();
    } catch (_) {}
  }
}
