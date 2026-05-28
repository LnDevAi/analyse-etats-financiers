import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/api_client.dart';

// ─── Modèles ────────────────────────────────────────────────────────────────

class UserProfile {
  final String id;
  final String email;
  final String fullName;
  final String role;
  final String tenantName;

  const UserProfile({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.tenantName,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      fullName: json['full_name']?.toString() ??
          json['fullName']?.toString() ??
          json['nom']?.toString() ??
          '',
      role: json['role']?.toString() ?? 'utilisateur',
      tenantName: json['tenant_name']?.toString() ??
          json['tenantName']?.toString() ??
          json['entreprise']?.toString() ??
          '',
    );
  }

  UserProfile copyWith({
    String? id,
    String? email,
    String? fullName,
    String? role,
    String? tenantName,
  }) {
    return UserProfile(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      role: role ?? this.role,
      tenantName: tenantName ?? this.tenantName,
    );
  }

  String get displayRole {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'Administrateur';
      case 'auditeur':
        return 'Auditeur';
      case 'manager':
        return 'Manager';
      case 'analyste':
        return 'Analyste';
      default:
        return role;
    }
  }
}

// ─── État Auth ──────────────────────────────────────────────────────────────

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final String? errorMessage;
  final UserProfile? user;

  const AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.errorMessage,
    this.user,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? errorMessage,
    UserProfile? user,
    bool clearError = false,
    bool clearUser = false,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      user: clearUser ? null : user ?? this.user,
    );
  }
}

// ─── Notifier ───────────────────────────────────────────────────────────────

const String _tokenKey = 'auth_token';

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _apiClient;
  final FlutterSecureStorage _storage;

  AuthNotifier(this._apiClient, this._storage)
      : super(const AuthState(isLoading: true)) {
    _restoreSession();
  }

  /// Restaure la session depuis le stockage sécurisé au démarrage
  Future<void> _restoreSession() async {
    try {
      final token = await _storage.read(key: _tokenKey);
      if (token == null || token.isEmpty) {
        state = const AuthState(isAuthenticated: false, isLoading: false);
        return;
      }

      // Valide le token en récupérant le profil
      final data = await _apiClient.get('/auth/me') as Map<String, dynamic>;
      final user = UserProfile.fromJson(data);
      state = AuthState(
        isAuthenticated: true,
        isLoading: false,
        user: user,
      );
    } catch (_) {
      await _storage.delete(key: _tokenKey);
      state = const AuthState(isAuthenticated: false, isLoading: false);
    }
  }

  /// Connexion utilisateur avec email et mot de passe
  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final data = await _apiClient.post(
        '/auth/login',
        data: {
          'username': email,
          'password': password,
        },
      ) as Map<String, dynamic>;

      final token = data['access_token']?.toString() ?? '';
      if (token.isEmpty) {
        throw ApiException('Réponse invalide du serveur.');
      }

      await _storage.write(key: _tokenKey, value: token);

      // Récupérer le profil utilisateur
      final profileData = await _apiClient.get('/auth/me') as Map<String, dynamic>;
      final user = UserProfile.fromJson(profileData);

      state = AuthState(
        isAuthenticated: true,
        isLoading: false,
        user: user,
      );
    } on ApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: e.message,
      );
      rethrow;
    } catch (e) {
      const message = 'Erreur de connexion. Veuillez réessayer.';
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: false,
        errorMessage: message,
      );
      throw ApiException(message);
    }
  }

  /// Déconnexion de l'utilisateur
  Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
    state = const AuthState(isAuthenticated: false, isLoading: false);
  }

  /// Efface le message d'erreur
  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

// ─── Providers ──────────────────────────────────────────────────────────────

final _secureStorageProvider = Provider<FlutterSecureStorage>(
  (ref) => const FlutterSecureStorage(),
);

final _apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(),
);

final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    ref.watch(_apiClientProvider),
    ref.watch(_secureStorageProvider),
  );
});

/// Provider pour le profil courant (accès simplifié)
final currentUserProvider = Provider<UserProfile?>((ref) {
  return ref.watch(authNotifierProvider).user;
});
