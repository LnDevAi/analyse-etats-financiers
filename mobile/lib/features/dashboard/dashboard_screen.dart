import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import '../../core/theme.dart';
import '../auth/auth_provider.dart';
import 'dashboard_provider.dart';

class DashboardContent extends ConsumerWidget {
  const DashboardContent({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Tableau de bord'),
            if (user != null)
              Text(
                'Bonjour, ${user.fullName.split(' ').first}',
                style: GoogleFonts.lato(
                  fontSize: 12,
                  fontWeight: FontWeight.w400,
                  color: Colors.white.withOpacity(0.85),
                ),
              ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualiser',
            onPressed: () => ref.refresh(dashboardProvider),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: dashboardAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Chargement du tableau de bord...'),
            ],
          ),
        ),
        error: (error, _) => _buildErrorView(context, ref, error.toString()),
        data: (stats) => _buildDashboard(context, ref, stats),
      ),
    );
  }

  Widget _buildErrorView(BuildContext context, WidgetRef ref, String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.errorLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.cloud_off_outlined,
                size: 48,
                color: AppColors.error,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Impossible de charger les données',
              style: GoogleFonts.lato(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: GoogleFonts.lato(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref.refresh(dashboardProvider),
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboard(
      BuildContext context, WidgetRef ref, DashboardStats stats) {
    return RefreshIndicator(
      onRefresh: () async => ref.refresh(dashboardProvider),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ─── KPI Cards ────────────────────────────────────────────
          _buildKpiSection(stats),
          const SizedBox(height: 20),

          // ─── Graphique analyses par mois ──────────────────────────
          if (stats.analysesParMois.isNotEmpty) ...[
            _buildSectionTitle('Analyses par mois'),
            const SizedBox(height: 12),
            _buildBarChart(stats.analysesParMois),
            const SizedBox(height: 20),
          ],

          // ─── Dernières analyses ───────────────────────────────────
          if (stats.dernieresAnalyses.isNotEmpty) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildSectionTitle('Dernières analyses'),
                TextButton(
                  onPressed: () => context.go('/analyses'),
                  child: const Text('Voir tout'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...stats.dernieresAnalyses
                .take(3)
                .map((a) => _buildAnalyseCard(context, a)),
          ],
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildKpiSection(DashboardStats stats) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                titre: 'Total analyses',
                valeur: stats.totalAnalyses.toString(),
                icone: Icons.analytics_outlined,
                couleurIcone: AppColors.primary,
                couleurFond: AppColors.infoLight,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _KpiCard(
                titre: 'En cours',
                valeur: stats.analysesEnCours.toString(),
                icone: Icons.hourglass_top_outlined,
                couleurIcone: AppColors.statusEnCours,
                couleurFond: AppColors.infoLight,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                titre: 'Anomalies critiques',
                valeur: stats.anomaliesCritiques.toString(),
                icone: Icons.warning_amber_outlined,
                couleurIcone: AppColors.error,
                couleurFond: AppColors.errorLight,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _KpiCard(
                titre: 'Score risque moyen',
                valeur: '${stats.scoreRisqueMoyen.toStringAsFixed(0)}%',
                icone: Icons.shield_outlined,
                couleurIcone: riskColor(stats.scoreRisqueMoyen.toInt()),
                couleurFond: riskBackgroundColor(stats.scoreRisqueMoyen.toInt()),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSectionTitle(String titre) {
    return Text(
      titre,
      style: GoogleFonts.lato(
        fontSize: 17,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
      ),
    );
  }

  Widget _buildBarChart(List<AnalyseMois> data) {
    final maxY = data
            .map((e) => e.nombre)
            .reduce((a, b) => a > b ? a : b)
            .toDouble() +
        2;

    return Container(
      height: 200,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: maxY,
          minY: 0,
          barTouchData: BarTouchData(
            touchTooltipData: BarTouchTooltipData(
              tooltipBgColor: AppColors.primary,
              getTooltipItem: (group, groupIndex, rod, rodIndex) {
                return BarTooltipItem(
                  '${rod.toY.toInt()} analyse${rod.toY > 1 ? 's' : ''}',
                  GoogleFonts.lato(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 12,
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
                getTitlesWidget: (value, meta) {
                  final index = value.toInt();
                  if (index >= 0 && index < data.length) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        data[index].mois,
                        style: GoogleFonts.lato(
                          fontSize: 11,
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                },
                reservedSize: 28,
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 30,
                getTitlesWidget: (value, meta) {
                  if (value == value.floorToDouble() && value >= 0) {
                    return Text(
                      value.toInt().toString(),
                      style: GoogleFonts.lato(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                },
              ),
            ),
            topTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            rightTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
          ),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 1,
            getDrawingHorizontalLine: (value) => FlLine(
              color: AppColors.divider,
              strokeWidth: 1,
              dashArray: [4, 4],
            ),
          ),
          borderData: FlBorderData(show: false),
          barGroups: List.generate(
            data.length,
            (index) => BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: data[index].nombre.toDouble(),
                  color: index % 2 == 0
                      ? AppColors.primary
                      : AppColors.primaryLight,
                  width: 20,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(4),
                    topRight: Radius.circular(4),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAnalyseCard(BuildContext context, AnalyseResume analyse) {
    final score = analyse.scoreRisque;
    final couleur = riskColor(score);

    return GestureDetector(
      onTap: () => context.go('/analyses/${analyse.id}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.divider),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Jauge circulaire score risque
            if (analyse.statut == 'TERMINE')
              CircularPercentIndicator(
                radius: 28,
                lineWidth: 5,
                percent: score / 100,
                center: Text(
                  '$score',
                  style: GoogleFonts.lato(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: couleur,
                  ),
                ),
                progressColor: couleur,
                backgroundColor: couleur.withOpacity(0.15),
                circularStrokeCap: CircularStrokeCap.round,
              )
            else
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: statusColor(analyse.statut).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  analyse.statut == 'EN_COURS'
                      ? Icons.hourglass_top
                      : Icons.error_outline,
                  color: statusColor(analyse.statut),
                  size: 24,
                ),
              ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    analyse.nomEntreprise,
                    style: GoogleFonts.lato(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    'Exercice ${analyse.exercice}',
                    style: GoogleFonts.lato(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      _StatusChip(statut: analyse.statut),
                      if (analyse.nombreAnomalies > 0) ...[
                        const SizedBox(width: 6),
                        Text(
                          '${analyse.nombreAnomalies} anomalie${analyse.nombreAnomalies > 1 ? 's' : ''}',
                          style: GoogleFonts.lato(
                            fontSize: 11,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: AppColors.textHint,
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Widgets internes ─────────────────────────────────────────────────────────

class _KpiCard extends StatelessWidget {
  final String titre;
  final String valeur;
  final IconData icone;
  final Color couleurIcone;
  final Color couleurFond;

  const _KpiCard({
    required this.titre,
    required this.valeur,
    required this.icone,
    required this.couleurIcone,
    required this.couleurFond,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: couleurFond,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icone, color: couleurIcone, size: 22),
          ),
          const SizedBox(height: 10),
          Text(
            valeur,
            style: GoogleFonts.lato(
              fontSize: 26,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            titre,
            style: GoogleFonts.lato(
              fontSize: 12,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String statut;

  const _StatusChip({required this.statut});

  @override
  Widget build(BuildContext context) {
    final color = statusColor(statut);
    final label = statusLabel(statut);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: GoogleFonts.lato(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
