import 'dart:io';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:open_file/open_file.dart';
import 'package:path_provider/path_provider.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import '../../core/api_client.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class AnalysisDetailScreen extends ConsumerWidget {
  final String analyseId;

  const AnalysisDetailScreen({super.key, required this.analyseId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyseAsync = ref.watch(analyseDetailProvider(analyseId));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: analyseAsync.when(
        loading: () => const Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Chargement de l\'analyse...'),
              ],
            ),
          ),
        ),
        error: (error, _) => Scaffold(
          appBar: AppBar(
            title: const Text('Détail analyse'),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => context.go('/analyses'),
            ),
          ),
          body: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline,
                      size: 64, color: AppColors.error),
                  const SizedBox(height: 16),
                  Text(
                    'Impossible de charger l\'analyse',
                    style: GoogleFonts.lato(
                        fontSize: 16, fontWeight: FontWeight.w700),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    error.toString(),
                    style: GoogleFonts.lato(
                        fontSize: 13, color: AppColors.textSecondary),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () =>
                        ref.refresh(analyseDetailProvider(analyseId)),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Réessayer'),
                  ),
                ],
              ),
            ),
          ),
        ),
        data: (analyse) => _AnalyseDetailView(analyse: analyse),
      ),
    );
  }
}

class _AnalyseDetailView extends ConsumerStatefulWidget {
  final AnalyseDetail analyse;

  const _AnalyseDetailView({required this.analyse});

  @override
  ConsumerState<_AnalyseDetailView> createState() => _AnalyseDetailViewState();
}

class _AnalyseDetailViewState extends ConsumerState<_AnalyseDetailView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isDownloadingWord = false;
  bool _isDownloadingExcel = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _telechargerRapport(String format) async {
    final isWord = format == 'word';
    if (isWord) {
      setState(() => _isDownloadingWord = true);
    } else {
      setState(() => _isDownloadingExcel = true);
    }

    try {
      final api = ApiClient();
      final path = '/analyses/${widget.analyse.id}/rapport';
      final queryParam = isWord ? 'format=docx' : 'format=xlsx';
      final bytes = await api.getBytes('$path?$queryParam');

      final dir = await getTemporaryDirectory();
      final ext = isWord ? 'docx' : 'xlsx';
      final nomFichier =
          'rapport_${widget.analyse.nomEntreprise.replaceAll(' ', '_')}_${widget.analyse.exercice}.$ext';
      final file = File('${dir.path}/$nomFichier');
      await file.writeAsBytes(bytes);

      await OpenFile.open(file.path);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Rapport ${isWord ? "Word" : "Excel"} téléchargé avec succès.',
            ),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content:
                Text('Erreur lors du téléchargement : ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isDownloadingWord = false;
          _isDownloadingExcel = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final analyse = widget.analyse;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              analyse.nomEntreprise,
              style: GoogleFonts.lato(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              'Exercice ${analyse.exercice}',
              style: GoogleFonts.lato(
                fontSize: 12,
                color: Colors.white.withOpacity(0.8),
              ),
            ),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/analyses'),
        ),
        actions: [
          if (analyse.statut.toUpperCase() == 'TERMINE')
            IconButton(
              icon: const Icon(Icons.warning_amber_outlined),
              tooltip: 'Voir les anomalies',
              onPressed: () =>
                  context.go('/analyses/${analyse.id}/anomalies'),
            ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Résumé'),
            Tab(text: 'Ratios'),
            Tab(text: 'Rapport'),
          ],
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white54,
          indicatorColor: Colors.white,
          indicatorWeight: 3,
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildResumeTab(analyse),
          _buildRatiosTab(analyse),
          _buildRapportTab(analyse),
        ],
      ),
    );
  }

  // ─── Onglet Résumé ─────────────────────────────────────────────────────────

  Widget _buildResumeTab(AnalyseDetail analyse) {
    final score = analyse.scoreRisque;
    final couleur = riskColor(score);
    final isTermine = analyse.statut.toUpperCase() == 'TERMINE';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // ─── Jauge score risque principale ──────────────────────────
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                Text(
                  'Score de risque global',
                  style: GoogleFonts.lato(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 20),
                if (isTermine)
                  CircularPercentIndicator(
                    radius: 80,
                    lineWidth: 12,
                    percent: score / 100,
                    center: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '$score',
                          style: GoogleFonts.lato(
                            fontSize: 36,
                            fontWeight: FontWeight.w900,
                            color: couleur,
                          ),
                        ),
                        Text(
                          '/100',
                          style: GoogleFonts.lato(
                            fontSize: 14,
                            color: AppColors.textHint,
                          ),
                        ),
                      ],
                    ),
                    progressColor: couleur,
                    backgroundColor: couleur.withOpacity(0.15),
                    circularStrokeCap: CircularStrokeCap.round,
                    animation: true,
                    animationDuration: 1200,
                  )
                else
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      color: statusColor(analyse.statut).withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.hourglass_top,
                      color: statusColor(analyse.statut),
                      size: 52,
                    ),
                  ),
                const SizedBox(height: 16),
                // Badge niveau de risque
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  decoration: BoxDecoration(
                    color: isTermine
                        ? couleur.withOpacity(0.12)
                        : AppColors.infoLight,
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(
                      color: isTermine
                          ? couleur.withOpacity(0.4)
                          : AppColors.primary.withOpacity(0.3),
                    ),
                  ),
                  child: Text(
                    isTermine
                        ? riskLabel(score)
                        : statusLabel(analyse.statut),
                    style: GoogleFonts.lato(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: isTermine ? couleur : AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                // Interprétation textuelle
                if (isTermine)
                  Text(
                    _interpretationRisque(score),
                    style: GoogleFonts.lato(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                      fontStyle: FontStyle.italic,
                    ),
                    textAlign: TextAlign.center,
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ─── Statistiques clés ───────────────────────────────────────
          if (isTermine) ...[
            _buildStatsGrid(analyse),
            const SizedBox(height: 16),
          ],

          // ─── Informations générales ──────────────────────────────────
          _buildInfoCard(analyse),
        ],
      ),
    );
  }

  String _interpretationRisque(int score) {
    if (score >= 80) {
      return 'Excellente santé financière. Aucune anomalie significative détectée. Les états financiers sont cohérents et fiables.';
    } else if (score >= 70) {
      return 'Bonne santé financière. Quelques points mineurs à surveiller. Les états financiers présentent une fiabilité satisfaisante.';
    } else if (score >= 55) {
      return 'Santé financière modérée. Des anomalies ont été détectées et nécessitent une attention particulière. Un audit approfondi est recommandé.';
    } else if (score >= 40) {
      return 'Risque modéré détecté. Des incohérences comptables significatives ont été identifiées. Une révision comptable est fortement conseillée.';
    } else if (score >= 25) {
      return 'Risque élevé. De nombreuses anomalies critiques ont été détectées. Un audit externe est urgemment recommandé.';
    } else {
      return 'Risque très élevé. Les états financiers présentent de graves incohérences. Une intervention immédiate est indispensable.';
    }
  }

  Widget _buildStatsGrid(AnalyseDetail analyse) {
    final currency = NumberFormat.currency(
      locale: 'fr_FR',
      symbol: 'FCFA',
      decimalDigits: 0,
    );

    return Row(
      children: [
        Expanded(
          child: _StatCard(
            valeur: analyse.nombreAnomalies.toString(),
            label: 'Anomalies\ntotales',
            couleur: AppColors.warning,
            icone: Icons.warning_amber_outlined,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _StatCard(
            valeur: analyse.montantTotal > 0
                ? currency.format(analyse.montantTotal)
                : 'N/A',
            label: 'Montant\ntotal',
            couleur: AppColors.primary,
            icone: Icons.attach_money,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _StatCard(
            valeur: analyse.niveauRisque,
            label: 'Niveau\nde risque',
            couleur: riskColor(analyse.scoreRisque),
            icone: Icons.shield_outlined,
          ),
        ),
      ],
    );
  }

  Widget _buildInfoCard(AnalyseDetail analyse) {
    final dateFormat = DateFormat('dd MMMM yyyy à HH:mm', 'fr_FR');

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Informations',
            style: GoogleFonts.lato(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 12),
          _InfoLine(label: 'Entreprise', valeur: analyse.nomEntreprise),
          _InfoLine(label: 'Exercice', valeur: analyse.exercice),
          _InfoLine(
            label: 'Date d\'analyse',
            valeur: dateFormat.format(analyse.dateCreation),
          ),
          _InfoLine(label: 'Statut', valeur: statusLabel(analyse.statut)),
          if (analyse.fichierFec != null)
            _InfoLine(label: 'Fichier FEC', valeur: analyse.fichierFec!),
        ],
      ),
    );
  }

  // ─── Onglet Ratios ─────────────────────────────────────────────────────────

  Widget _buildRatiosTab(AnalyseDetail analyse) {
    if (analyse.statut.toUpperCase() != 'TERMINE') {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.hourglass_top,
                  size: 56, color: AppColors.textHint),
              const SizedBox(height: 16),
              Text(
                'Ratios en cours de calcul',
                style: GoogleFonts.lato(
                    fontSize: 16, fontWeight: FontWeight.w700),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Les ratios financiers seront disponibles une fois l\'analyse terminée.',
                style: GoogleFonts.lato(
                    fontSize: 13, color: AppColors.textSecondary),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ─── Graphique barres des ratios ──────────────────────────
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Ratios financiers clés',
                  style: GoogleFonts.lato(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  height: 220,
                  child: _buildRatiosBarChart(analyse.ratios),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ─── Détail de chaque ratio ───────────────────────────────
          ...analyse.ratios.map((ratio) => _RatioCard(ratio: ratio)),
        ],
      ),
    );
  }

  Widget _buildRatiosBarChart(List<RatioFinancier> ratios) {
    if (ratios.isEmpty) return const SizedBox.shrink();

    final maxVal = ratios.map((r) => r.valeur).reduce((a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: maxVal * 1.3,
        minY: 0,
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            tooltipBgColor: AppColors.primary,
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final ratio = ratios[group.x];
              return BarTooltipItem(
                '${ratio.nom}\n${rod.toY.toStringAsFixed(2)}${ratio.unite}',
                GoogleFonts.lato(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 11,
                ),
              );
            },
          ),
        ),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 42,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < ratios.length) {
                  final mots = ratios[index].nom.split(' ');
                  return Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: mots
                          .take(2)
                          .map(
                            (m) => Text(
                              m,
                              style: GoogleFonts.lato(
                                fontSize: 9,
                                color: AppColors.textSecondary,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          )
                          .toList(),
                    ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 36,
              getTitlesWidget: (value, meta) => Text(
                value.toStringAsFixed(1),
                style: GoogleFonts.lato(
                    fontSize: 10, color: AppColors.textSecondary),
              ),
            ),
          ),
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (_) => FlLine(
            color: AppColors.divider,
            strokeWidth: 1,
            dashArray: [4, 4],
          ),
        ),
        borderData: FlBorderData(show: false),
        barGroups: List.generate(
          ratios.length,
          (index) {
            final ratio = ratios[index];
            final isOk = ratio.valeurReference == null ||
                ratio.valeur >= ratio.valeurReference!;
            return BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: ratio.valeur,
                  color: isOk ? AppColors.primary : AppColors.warning,
                  width: 28,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(4),
                    topRight: Radius.circular(4),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  // ─── Onglet Rapport ────────────────────────────────────────────────────────

  Widget _buildRapportTab(AnalyseDetail analyse) {
    final isTermine = analyse.statut.toUpperCase() == 'TERMINE';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ─── Résumé IA ───────────────────────────────────────────
          if (analyse.resumeIa != null && analyse.resumeIa!.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.psychology_outlined,
                          color: AppColors.primary, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Résumé IA',
                        style: GoogleFonts.lato(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  Text(
                    analyse.resumeIa!,
                    style: GoogleFonts.lato(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ─── Téléchargements ─────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.download_outlined,
                        color: AppColors.primary, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Télécharger le rapport',
                      style: GoogleFonts.lato(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Divider(height: 1),
                const SizedBox(height: 16),

                if (!isTermine)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.warningLight,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline,
                            color: AppColors.warning, size: 18),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Le rapport sera disponible une fois l\'analyse terminée.',
                            style: GoogleFonts.lato(
                              fontSize: 13,
                              color: AppColors.warning,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                else ...[
                  _DownloadButton(
                    label: 'Télécharger le rapport Word',
                    icone: Icons.description_outlined,
                    couleur: const Color(0xFF2B579A),
                    isLoading: _isDownloadingWord,
                    onPressed: () => _telechargerRapport('word'),
                  ),
                  const SizedBox(height: 12),
                  _DownloadButton(
                    label: 'Télécharger le rapport Excel',
                    icone: Icons.table_chart_outlined,
                    couleur: const Color(0xFF217346),
                    isLoading: _isDownloadingExcel,
                    onPressed: () => _telechargerRapport('excel'),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ─── Bouton anomalies ─────────────────────────────────────
          if (isTermine && analyse.nombreAnomalies > 0)
            OutlinedButton.icon(
              onPressed: () =>
                  context.go('/analyses/${analyse.id}/anomalies'),
              icon: const Icon(Icons.warning_amber_outlined),
              label: Text(
                'Voir les ${analyse.nombreAnomalies} anomalie${analyse.nombreAnomalies > 1 ? 's' : ''} détectée${analyse.nombreAnomalies > 1 ? 's' : ''}',
              ),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 48),
                foregroundColor: AppColors.warning,
                side: const BorderSide(color: AppColors.warning),
              ),
            ),
        ],
      ),
    );
  }
}

// ─── Widgets internes ─────────────────────────────────────────────────────────

class _StatCard extends StatelessWidget {
  final String valeur;
  final String label;
  final Color couleur;
  final IconData icone;

  const _StatCard({
    required this.valeur,
    required this.label,
    required this.couleur,
    required this.icone,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
      decoration: BoxDecoration(
        color: couleur.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: couleur.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Icon(icone, color: couleur, size: 22),
          const SizedBox(height: 8),
          Text(
            valeur,
            style: GoogleFonts.lato(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: couleur,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: GoogleFonts.lato(
              fontSize: 10,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String label;
  final String valeur;

  const _InfoLine({required this.label, required this.valeur});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: GoogleFonts.lato(
                fontSize: 13,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              valeur,
              style: GoogleFonts.lato(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RatioCard extends StatelessWidget {
  final RatioFinancier ratio;

  const _RatioCard({required this.ratio});

  @override
  Widget build(BuildContext context) {
    final isOk = ratio.valeurReference == null ||
        ratio.valeur >= ratio.valeurReference!;
    final couleur = isOk ? AppColors.success : AppColors.warning;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: couleur.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              isOk
                  ? Icons.check_circle_outline
                  : Icons.warning_amber_outlined,
              color: couleur,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  ratio.nom,
                  style: GoogleFonts.lato(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  ratio.interpretation,
                  style: GoogleFonts.lato(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
                if (ratio.valeurReference != null) ...[
                  const SizedBox(height: 3),
                  Text(
                    'Référence : ${ratio.valeurReference!.toStringAsFixed(2)}${ratio.unite}',
                    style: GoogleFonts.lato(
                      fontSize: 11,
                      color: AppColors.textHint,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 10),
          Text(
            '${ratio.valeur.toStringAsFixed(2)}${ratio.unite}',
            style: GoogleFonts.lato(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: couleur,
            ),
          ),
        ],
      ),
    );
  }
}

class _DownloadButton extends StatelessWidget {
  final String label;
  final IconData icone;
  final Color couleur;
  final bool isLoading;
  final VoidCallback? onPressed;

  const _DownloadButton({
    required this.label,
    required this.icone,
    required this.couleur,
    required this.isLoading,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton.icon(
        onPressed: isLoading ? null : onPressed,
        icon: isLoading
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                  color: Colors.white,
                  strokeWidth: 2,
                ),
              )
            : Icon(icone, size: 20),
        label: Text(
          label,
          style: GoogleFonts.lato(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: couleur,
          foregroundColor: Colors.white,
          disabledBackgroundColor: couleur.withOpacity(0.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
    );
  }
}
