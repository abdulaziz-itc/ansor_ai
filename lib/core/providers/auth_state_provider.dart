import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../data/repository/auth_repository.dart';

enum AuthStatus { initial, authenticated, unauthenticated, loading }

class AuthState {
  final AuthStatus status;
  final String? errorMessage;

  AuthState({required this.status, this.errorMessage});

  factory AuthState.initial() => AuthState(status: AuthStatus.initial);
  factory AuthState.loading() => AuthState(status: AuthStatus.loading);
  factory AuthState.authenticated() => AuthState(status: AuthStatus.authenticated);
  factory AuthState.unauthenticated({String? error}) => AuthState(status: AuthStatus.unauthenticated, errorMessage: error);
}

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(AuthState.initial()) {
    checkAuth();
  }

  Future<void> checkAuth() async {
    final token = await _repository.getToken();
    if (token != null) {
      state = AuthState.authenticated();
    } else {
      state = AuthState.unauthenticated();
    }
  }

  Future<void> login(String username, String password) async {
    state = AuthState.loading();
    try {
      final success = await _repository.login(username, password);
      if (success) {
        state = AuthState.authenticated();
      } else {
        state = AuthState.unauthenticated(error: "Failed to retrieve token");
      }
    } on DioException catch (e) {
      String errorMessage = "Failed to login";
      if (e.response?.data != null) {
        if (e.response?.data is Map && e.response?.data['detail'] != null) {
          errorMessage = e.response?.data['detail'];
        } else if (e.response?.statusCode == 500) {
          errorMessage = "Serverda ichki xatolik yuz berdi (500).";
        }
      }
      state = AuthState.unauthenticated(error: errorMessage);
    } catch (e) {
      state = AuthState.unauthenticated(error: e.toString());
    }
  }

  Future<void> register(String username, String email, String password, String? fullName) async {
    state = AuthState.loading();
    try {
      final success = await _repository.register(username, email, password, fullName: fullName);
      if (success) {
        state = AuthState.authenticated();
      } else {
        state = AuthState.unauthenticated(error: "Failed to create account");
      }
    } on DioException catch (e) {
      String errorMessage = "Failed to create account";
      if (e.response?.data != null) {
        if (e.response?.data is Map && e.response?.data['detail'] != null) {
          errorMessage = e.response?.data['detail'];
        } else if (e.response?.statusCode == 500) {
          errorMessage = "Serverda ichki xatolik yuz berdi (500).";
        }
      }
      state = AuthState.unauthenticated(error: errorMessage);
    } catch (e) {
      state = AuthState.unauthenticated(error: e.toString());
    }
  }

  Future<void> signInWithGoogle() async {
    state = AuthState.loading();
    try {
      final success = await _repository.signInWithGoogle();
      if (success) {
        state = AuthState.authenticated();
      } else {
        state = AuthState.unauthenticated(error: "Sign-in was canceled.");
      }
    } on DioException catch (e) {
      String errorMessage = "Sign-in failed";
      if (e.response?.data != null) {
        if (e.response?.data is Map && e.response?.data['detail'] != null) {
          errorMessage = e.response?.data['detail'];
        } else if (e.response?.statusCode == 500) {
          errorMessage = "Serverda ichki xatolik yuz berdi (500).";
        }
      }
      state = AuthState.unauthenticated(error: errorMessage);
    } catch (e) {
      state = AuthState.unauthenticated(error: e.toString());
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = AuthState.unauthenticated();
  }
}
