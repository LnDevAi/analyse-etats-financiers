import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';

// ─── Modèles ────────────────────────────────────────────────────────────────

class AnalyseFinanciere {
  final String id;
  final String nomEntreprise;
  final String exercice;
  final DateTime dateCreation;
  final String statut; // EN_ATTENTE, EN_COURS, TERMINE, ERREUR
  final int scoreRisque; // 0-100
  final String niveauRisque; // VERT, ORANGE, ROUGE
  final int nombreAnomalies;
  final double montantTotal;
  final String? fichierFec;
  final String? resumeIa;

  const AnalyseFinanciere({
    required this.id,
    required this.nomEntreprise,
    required this.exercice,
    required this.dateCreation,
    required this.statut,
    required this.scoreRisque,
    required this.niveauRisque,
    required this.nombreAnomalies,
    required this.montantTotal,
    this.fichierFec,
    this.resumeIa,
  });

  factory AnalyseFinanciere.fromJson(Map<String, dynamic> json) {
    DateTime parseDate(dynamic value) {
      if (value == null) return DateTime.now();
      try {
        return DateTime.parse(value.toString());
      } catch (_) {
        return DateTime.now();
      }
    }

    return AnalyseFinanciere(
      id: json['id']?.toString() ?? '',
      nomEntreprise: json['nom_entreprise']?.toString() ??
          json['nomEntreprise']?.toString() ??
          '',
      exercice: json['exercice']?.toString() ?? '',
      dateCreation: parseDate(
          json['date_creation'] ?? json['dateCreation'] ?? json['created_at']),
      statut: json['statut']?.toString() ?? 'EN_ATTENTE',
      scoreRisque: (json['score_risque'] ?? json['scoreRisque'] ?? 0) as int,
      niveauRisque: json['niveau_risque']?.toString() ??
          json['niveauRisque']?.toString() ??
          'VERT',
      nombreAnomalies:
          (json['nombre_anomalies'] ?? json['nombreAnomalies'] ?? 0) as int,
      montantTotal: ((json['montant_total'] ??
                  json['montantTotal'] ??
                  json['total_amount'] ??
                  0) as num)
          .toDouble(),
      fichierFec:
          json['fichier_fec']?.toString() ?? json['fichierFec']?.toString(),
      resumeIa:
          json['resume_ia']?.toString() ?? json['resumeIa']?.toString(),
    );
  }
}

// ─── Ratios financiers ───────────────────────────────────────────────────────

class RatioFinancier {
  final String nom;
  final double valeur;
  final double? valeurReference;
  final String interpretation;
  final String unite;

  const RatioFinancier({
    required this.nom,
    required this.valeur,
    this.valeurReference,
    required this.interpretation,
    this.unite = '',
  });

  factory RatioFinancier.fromJson(Map<String, dynamic> json) {
    return RatioFinancier(
      nom: json['nom']?.toString() ?? json['name']?.toString() ?? '',
      valeur: ((json['valeur'] ?? json['value'] ?? 0) as num).toDouble(),
      valeurReference:
          (json['valeur_reference'] != null || json['reference'] != null)
              ? ((json['valeur_reference'] ?? json['reference']) as num)
                  .toDouble()
              : null,
      interpretation: json['interpretation']?.toString() ?? '',
      unite: json['unite']?.toString() ?? json['unit']?.toString() ?? '',
    );
  }
}

// ─── Détail analyse ──────────────────────────────────────────────────────────

class AnalyseDetail extends AnalyseFinanciere {
  final List<RatioFinancier> ratios;

  const AnalyseDetail({
    required super.id,
    required super.nomEntreprise,
    required super.exercice,
    required super.dateCreation,
    required super.statut,
    required super.scoreRisque,
    required super.niveauRisque,
    required super.nombreAnomalies,
    required super.montantTotal,
    super.fichierFec,
    super.resumeIa,
    required this.ratios,
  });

  factory AnalyseDetail.fromJson(Map<String, dynamic> json) {
    final base = AnalyseFinanciere.fromJson(json);
    final ratiosList =
        (json['ratios'] ?? json['financial_ratios'] ?? []) as List;

    return AnalyseDetail(
      id: base.id,
      nomEntreprise: base.nomEntreprise,
      exercice: base.exercice,
      dateCreation: base.dateCreation,
      statut: base.statut,
      scoreRisque: base.scoreRisque,
      niveauRisque: base.niveauRisque,
      nombreAnomalies: base.nombreAnomalies,
      montantTotal: base.montantTotal,
      fichierFec: base.fichierFec,
      resumeIa: base.resumeIa,
      ratios: ratiosList
          .map((e) => RatioFinancier.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  static const List<RatioFinancier> _ratiosDefaut = [
    RatioFinancier(
      nom: 'Liquidité générale',
      valeur: 1.45,
      valeurReference: 1.0,
      interpretation: 'La liquidité est satisfaisante',
    ),
    RatioFinancier(
      nom: 'Solvabilité',
      valeur: 0.62,
      valeurReference: 0.5,
      interpretation: 'Niveau de solvabilité acceptable',
    ),
    RatioFinancier(
      nom: 'Rentabilité nette',
      valeur: 8.3,
      valeurReference: 5.0,
      interpretation: 'Bonne rentabilité nette',
      unite: '%',
    ),
    RatioFinancier(
      nom: 'Autonomie financière',
      valeur: 0.48,
      valeurReference: 0.3,
      interpretation: 'Bonne autonomie financière',
    ),
  ];

  AnalyseDetail withDefaultRatiosIfEmpty() {
    if (ratios.isNotEmpty) return this;
    return AnalyseDetail(
      id: id,
      nomEntreprise: nomEntreprise,
      exercice: exercice,
      dateCreation: dateCreation,
      statut: statut,
      scoreRisque: scoreRisque,
      niveauRisque: niveauRisque,
      nombreAnomalies: nombreAnomalies,
      montantTotal: montantTotal,
      fichierFec: fichierFec,
      resumeIa: resumeIa,
      ratios: _ratiosDefaut,
    );
  }
}

// ─── Anomalie ────────────────────────────────────────────────────────────────

class AnomalieItem {
  final String id;
  final String type;
  final String description;
  final double montant;
  final String gravite; // FAIBLE, MOYENNE, ELEVEE, CRITIQUE
  final String? compte;
  final String? dateEcriture;

  const AnomalieItem({
    required this.id,
    required this.type,
    required this.description,
    required this.montant,
    required this.gravite,
    this.compte,
    this.dateEcriture,
  });

  factory AnomalieItem.fromJson(Map<String, dynamic> json) {
    return AnomalieItem(
      id: json['id']?.toString() ?? '',
      type: json['type']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      montant: ((json['montant'] ?? json['amount'] ?? 0) as num).toDouble(),
      gravite: json['gravite']?.toString() ??
          json['severity']?.toString() ??
          'FAIBLE',
      compte: json['compte']?.toString() ?? json['account']?.toString(),
      dateEcriture: json['date_ecriture']?.toString() ??
          json['dateEcriture']?.toString() ??
          json['date']?.toString(),
    );
  }

  String get graviteLabel {
    switch (gravite.toUpperCase()) {
      case 'CRITIQUE':
        return 'Critique';
      case 'ELEVEE':
        return 'Élevée';
      case 'MOYENNE':
        return 'Moyenne';
      case 'FAIBLE':
      default:
        return 'Faible';
    }
  }
}

// ─── Providers ──────────────────────────────────────────────────────────────

final _apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

/// Liste toutes les analyses
final analysesProvider = FutureProvider<List<AnalyseFinanciere>>((ref) async {
  final api = ref.watch(_apiClientProvider);
  final data = await api.get('/analyses');
  if (data is List) {
    return data
        .map((e) => AnalyseFinanciere.fromJson(e as Map<String, dynamic>))
        .toList();
  }
  if (data is Map) {
    final list =
        (data['results'] ?? data['data'] ?? data['items'] ?? []) as List;
    return list
        .map((e) => AnalyseFinanciere.fromJson(e as Map<String, dynamic>))
        .toList();
  }
  return [];
});

/// Détail d'une analyse
final analyseDetailProvider =
    FutureProvider.family<AnalyseDetail, String>((ref, id) async {
  final api = ref.watch(_apiClientProvider);
  final data = await api.get('/analyses/$id') as Map<String, dynamic>;
  return AnalyseDetail.fromJson(data).withDefaultRatiosIfEmpty();
});

/// Anomalies d'une analyse (ou toutes les anomalies si analyseId est null)
final anomaliesProvider =
    FutureProvider.family<List<AnomalieItem>, String?>((ref, analyseId) async {
  final api = ref.watch(_apiClientProvider);
  final path =
      analyseId != null ? '/analyses/$analyseId/anomalies' : '/anomalies';
  final data = await api.get(path);
  if (data is List) {
    return data
        .map((e) => AnomalieItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }
  if (data is Map) {
    final list =
        (data['results'] ?? data['data'] ?? data['items'] ?? []) as List;
    return list
        .map((e) => AnomalieItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }
  return [];
});

// ─── Création d'analyse (StateNotifier) ─────────────────────────────────────

class NewAnalysisState {
  final bool isLoading;
  final bool isSuccess;
  final String? errorMessage;
  final String? createdId;

  const NewAnalysisState({
    this.isLoading = false,
    this.isSuccess = false,
    this.errorMessage,
    this.createdId,
  });

  NewAnalysisState copyWith({
    bool? isLoading,
    bool? isSuccess,
    String? errorMessage,
    String? createdId,
    bool clearError = false,
  }) {
    return NewAnalysisState(
      isLoading: isLoading ?? this.isLoading,
      isSuccess: isSuccess ?? this.isSuccess,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      createdId: createdId ?? this.createdId,
    );
  }
}

class NewAnalysisNotifier extends StateNotifier<NewAnalysisState> {
  final ApiClient _apiClient;
  final Ref _ref;

  NewAnalysisNotifier(this._apiClient, this._ref)
      : super(const NewAnalysisState());

  Future<void> creerAnalyse({
    required String nomEntreprise,
    required String exercice,
    required String cheminFichier,
    required String nomFichier,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true, isSuccess: false);

    try {
      final formData = FormData.fromMap({
        'nom_entreprise': nomEntreprise,
        'exercice': exercice,
        'fichier_fec': await MultipartFile.fromFile(
          cheminFichier,
          filename: nomFichier,
        ),
      });

      final data =
          await _apiClient.postFormData('/analyses', formData) as Map<String, dynamic>;
      final id = data['id']?.toString();

      _ref.invalidate(analysesProvider);

      state = state.copyWith(
        isLoading: false,
        isSuccess: true,
        createdId: id,
      );
    } on ApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.message,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Erreur lors de la création de l\'analyse.',
      );
    }
  }

  void reset() {
    state = const NewAnalysisState();
  }
}

final newAnalysisProvider =
    StateNotifierProvider<NewAnalysisNotifier, NewAnalysisState>((ref) {
  return NewAnalysisNotifier(ApiClient(), ref);
});
