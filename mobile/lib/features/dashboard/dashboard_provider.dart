import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';

// ─── Modèles ────────────────────────────────────────────────────────────────

class AnalyseMois {
  final String mois;
  final int nombre;

  const AnalyseMois({required this.mois, required this.nombre});

  factory AnalyseMois.fromJson(Map<String, dynamic> json) {
    return AnalyseMois(
      mois: json['mois']?.toString() ?? json['month']?.toString() ?? '',
      nombre: (json['nombre'] ?? json['count'] ?? 0) as int,
    );
  }
}

class AnalyseResume {
  final String id;
  final String nomEntreprise;
  final String exercice;
  final String statut;
  final int scoreRisque;
  final String niveauRisque;
  final int nombreAnomalies;

  const AnalyseResume({
    required this.id,
    required this.nomEntreprise,
    required this.exercice,
    required this.statut,
    required this.scoreRisque,
    required this.niveauRisque,
    required this.nombreAnomalies,
  });

  factory AnalyseResume.fromJson(Map<String, dynamic> json) {
    return AnalyseResume(
      id: json['id']?.toString() ?? '',
      nomEntreprise: json['nom_entreprise']?.toString() ??
          json['nomEntreprise']?.toString() ??
          '',
      exercice: json['exercice']?.toString() ?? '',
      statut: json['statut']?.toString() ?? 'EN_ATTENTE',
      scoreRisque: (json['score_risque'] ?? json['scoreRisque'] ?? 0) as int,
      niveauRisque: json['niveau_risque']?.toString() ??
          json['niveauRisque']?.toString() ??
          'VERT',
      nombreAnomalies:
          (json['nombre_anomalies'] ?? json['nombreAnomalies'] ?? 0) as int,
    );
  }
}

class DashboardStats {
  final int totalAnalyses;
  final int analysesEnCours;
  final int anomaliesCritiques;
  final double scoreRisqueMoyen;
  final List<AnalyseMois> analysesParMois;
  final List<AnalyseResume> dernieresAnalyses;

  const DashboardStats({
    required this.totalAnalyses,
    required this.analysesEnCours,
    required this.anomaliesCritiques,
    required this.scoreRisqueMoyen,
    required this.analysesParMois,
    required this.dernieresAnalyses,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    final moisList = (json['analyses_par_mois'] ??
            json['analysesParMois'] ??
            json['par_mois'] ??
            []) as List;

    final dernieresList = (json['dernieres_analyses'] ??
            json['dernieresAnalyses'] ??
            json['recent_analyses'] ??
            []) as List;

    return DashboardStats(
      totalAnalyses:
          (json['total_analyses'] ?? json['totalAnalyses'] ?? 0) as int,
      analysesEnCours:
          (json['analyses_en_cours'] ?? json['analysesEnCours'] ?? 0) as int,
      anomaliesCritiques: (json['anomalies_critiques'] ??
              json['anomaliesCritiques'] ??
              0) as int,
      scoreRisqueMoyen: ((json['score_risque_moyen'] ??
                  json['scoreRisqueMoyen'] ??
                  0) as num)
          .toDouble(),
      analysesParMois: moisList
          .map((e) => AnalyseMois.fromJson(e as Map<String, dynamic>))
          .toList(),
      dernieresAnalyses: dernieresList
          .map((e) => AnalyseResume.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  /// Données de démonstration si l'API ne répond pas
  factory DashboardStats.demo() {
    return DashboardStats(
      totalAnalyses: 24,
      analysesEnCours: 3,
      anomaliesCritiques: 7,
      scoreRisqueMoyen: 62.5,
      analysesParMois: [
        const AnalyseMois(mois: 'Jan', nombre: 2),
        const AnalyseMois(mois: 'Fév', nombre: 3),
        const AnalyseMois(mois: 'Mar', nombre: 5),
        const AnalyseMois(mois: 'Avr', nombre: 4),
        const AnalyseMois(mois: 'Mai', nombre: 6),
        const AnalyseMois(mois: 'Juin', nombre: 4),
      ],
      dernieresAnalyses: [
        const AnalyseResume(
          id: '1',
          nomEntreprise: 'SARL TechBurkina',
          exercice: '2024',
          statut: 'TERMINE',
          scoreRisque: 78,
          niveauRisque: 'VERT',
          nombreAnomalies: 2,
        ),
        const AnalyseResume(
          id: '2',
          nomEntreprise: 'SA Commerce Mali',
          exercice: '2023',
          statut: 'TERMINE',
          scoreRisque: 45,
          niveauRisque: 'ORANGE',
          nombreAnomalies: 8,
        ),
        const AnalyseResume(
          id: '3',
          nomEntreprise: 'GIE Agro Sénégal',
          exercice: '2024',
          statut: 'EN_COURS',
          scoreRisque: 0,
          niveauRisque: 'VERT',
          nombreAnomalies: 0,
        ),
      ],
    );
  }
}

// ─── Providers ──────────────────────────────────────────────────────────────

final _apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final dashboardProvider = FutureProvider<DashboardStats>((ref) async {
  final api = ref.watch(_apiClientProvider);
  try {
    final data = await api.get('/dashboard') as Map<String, dynamic>;
    return DashboardStats.fromJson(data);
  } catch (_) {
    rethrow;
  }
});
