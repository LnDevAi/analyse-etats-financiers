import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const String _baseUrl = 'http://api.analyses.edefence.tech/api/v1';
const String _tokenKey = 'auth_token';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiClient {
  static ApiClient? _instance;
  late final Dio _dio;
  final FlutterSecureStorage _storage;

  ApiClient._internal(this._storage) {
    _dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
        sendTimeout: const Duration(seconds: 60),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: _tokenKey);
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onResponse: (response, handler) {
          handler.next(response);
        },
        onError: (error, handler) {
          handler.next(error);
        },
      ),
    );
  }

  factory ApiClient({FlutterSecureStorage? storage}) {
    _instance ??= ApiClient._internal(
      storage ?? const FlutterSecureStorage(),
    );
    return _instance!;
  }

  Dio get dio => _dio;

  Future<String?> getToken() => _storage.read(key: _tokenKey);

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<void> deleteToken() => _storage.delete(key: _tokenKey);

  /// GET request
  Future<dynamic> get(String path, {Map<String, dynamic>? queryParams}) async {
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParams,
      );
      return response.data;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// POST request JSON
  Future<dynamic> post(String path, {dynamic data}) async {
    try {
      final response = await _dio.post(path, data: data);
      return response.data;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// POST multipart/form-data
  Future<dynamic> postFormData(String path, FormData formData) async {
    try {
      final response = await _dio.post(
        path,
        data: formData,
        options: Options(
          contentType: 'multipart/form-data',
        ),
      );
      return response.data;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// GET file bytes (rapport PDF/Word)
  Future<List<int>> getBytes(String path) async {
    try {
      final response = await _dio.get<List<int>>(
        path,
        options: Options(responseType: ResponseType.bytes),
      );
      return response.data ?? [];
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  ApiException _handleDioError(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return ApiException(
        'Délai de connexion dépassé. Vérifiez votre connexion internet.',
        statusCode: null,
      );
    }

    if (error.type == DioExceptionType.connectionError) {
      return ApiException(
        'Impossible de se connecter au serveur. Vérifiez votre connexion internet.',
        statusCode: null,
      );
    }

    final statusCode = error.response?.statusCode;
    final responseData = error.response?.data;

    String message;
    switch (statusCode) {
      case 400:
        message = _extractErrorMessage(responseData) ??
            'Données invalides. Veuillez vérifier vos informations.';
        break;
      case 401:
        message = 'Session expirée. Veuillez vous reconnecter.';
        break;
      case 403:
        message = 'Accès refusé. Vous n\'avez pas les droits nécessaires.';
        break;
      case 404:
        message = 'Ressource introuvable.';
        break;
      case 409:
        message = _extractErrorMessage(responseData) ??
            'Conflit de données. Cet élément existe déjà.';
        break;
      case 422:
        message = _extractValidationError(responseData) ??
            'Données non valides. Veuillez corriger les erreurs.';
        break;
      case 500:
        message = 'Erreur interne du serveur. Veuillez réessayer plus tard.';
        break;
      case 502:
      case 503:
      case 504:
        message = 'Service temporairement indisponible. Veuillez réessayer.';
        break;
      default:
        message = _extractErrorMessage(responseData) ??
            'Une erreur inattendue est survenue.';
    }

    return ApiException(message, statusCode: statusCode);
  }

  String? _extractErrorMessage(dynamic data) {
    if (data == null) return null;
    if (data is Map) {
      return data['detail']?.toString() ??
          data['message']?.toString() ??
          data['error']?.toString();
    }
    return data.toString();
  }

  String? _extractValidationError(dynamic data) {
    if (data == null) return null;
    if (data is Map && data['detail'] is List) {
      final errors = data['detail'] as List;
      if (errors.isNotEmpty) {
        final first = errors.first;
        if (first is Map) {
          return first['msg']?.toString();
        }
      }
    }
    return _extractErrorMessage(data);
  }
}
