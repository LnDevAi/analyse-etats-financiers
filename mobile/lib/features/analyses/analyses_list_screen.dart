import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class AnalysesListScreen extends ConsumerWidget {
  const AnalysesListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analysesAsync = ref.watch(analysesProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Mes analyses'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualiser',
            onPressed: () => ref.refresh(analysesProvider),
          ),
        ],
      ),
      body: analysesAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Chargement des analyses...'),
            ],
          ),
        ),
        error: (error, _) => _buildError(context, ref, error.toString()),
        data: (analyses) => _buildList(context, analyses),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.go('/analyses/new'),
        icon: const Icon(Icons.add),
        label: const Text('Nouvelle analyse'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
    );
  }

  Widget _buildError(BuildContext context, WidgetRef ref, String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off_outlined,
                size: 64, color: AppColors.textHint),
            const SizedBox(height: 16),
            Text(
              'Impossible de charger les analyses',
              style: GoogleFonts.lato(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style:
                  GoogleFonts.lato(fontSize: 13, color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref.refresh(analysesProvider),
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildList(BuildContext context, List<AnalyseFinanciere> analyses) {
    if (analyses.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppColors.infoLight,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.analytics_outlined,
                  size: 56,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Aucune analyse disponible',
                style: GoogleFonts.lato(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Lancez votre première analyse en uploadant\nun fichier FEC SYSCOHADA.',
                style: GoogleFonts.lato(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () => context.go('/analyses/new'),
                icon: const Icon(Icons.add),
                label: const Text('Lancer une analyse'),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: analyses.length,
        itemBuilder: (context, index) {
          return _AnalyseCard(
            analyse: analyses[index],
            onTap: () => context.go('/analyses/${analyses[index].id}'),
          );
        },
      ),
    );
  }
}

class _AnalyseCard extends StatelessWidget {
  final AnalyseFinanciere analyse;
  final VoidCallback onTap;

  const _AnalyseCard({required this.analyse, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isTermine = analyse.statut.toUpperCase() == 'TERMINE';
    final score = analyse.scoreRisque;
    final couleur = riskColor(score);
    final dateFormat = DateFormat('dd/MM/yyyy', 'fr_FR');

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.divider),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          children: [
            // ─── En-tête de la carte ──────────────────────────────
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.04),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(14),
                  topRight: Radius.circular(14),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          analyse.nomEntreprise,
                          style: GoogleFonts.lato(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Exercice ${analyse.exercice}',
                          style: GoogleFonts.lato(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _StatusBadge(statut: analyse.statut),
                ],
              ),
            ),

            // ─── Corps de la carte ────────────────────────────────
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  // Jauge circulaire
                  if (isTermine)
                    CircularPercentIndicator(
                      radius: 36,
                      lineWidth: 6,
                      percent: score / 100,
                      center: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            '$score',
                            style: GoogleFonts.lato(
                              fontSize: 14,
                              fontWeight: FontWeight.w800,
                              color: couleur,
                            ),
                          ),
                          Text(
                            '/100',
                            style: GoogleFonts.lato(
                              fontSize: 9,
                              color: AppColors.textHint,
                            ),
                          ),
                        ],
                      ),
                      progressColor: couleur,
                      backgroundColor: couleur.withOpacity(0.15),
                      circularStrokeCap: CircularStrokeCap.round,
                    )
                  else
                    Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: statusColor(analyse.statut).withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _statusIcon(analyse.statut),
                        color: statusColor(analyse.statut),
                        size: 32,
                      ),
                    ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Niveau de risque
                        if (isTermine) ...[
                          _RiskBadge(score: score),
                          const SizedBox(height: 8),
                        ],
                        // Stats
                        _InfoRow(
                          icone: Icons.warning_amber_outlined,
                          label:
                              '${analyse.nombreAnomalies} anomalie${analyse.nombreAnomalies > 1 ? 's' : ''} détectée${analyse.nombreAnomalies > 1 ? 's' : ''}',
                          color: analyse.nombreAnomalies > 0
                              ? AppColors.warning
                              : AppColors.textSecondary,
                        ),
                        const SizedBox(height: 4),
                        _InfoRow(
                          icone: Icons.attach_money,
                          label: _formatMontant(analyse.montantTotal),
                          color: AppColors.textSecondary,
                        ),
                        const SizedBox(height: 4),
                        _InfoRow(
                          icone: Icons.calendar_today_outlined,
                          label: dateFormat.format(analyse.dateCreation),
                          color: AppColors.textSecondary,
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: AppColors.textHint),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _statusIcon(String statut) {
    switch (statut.toUpperCase()) {
      case 'EN_COURS':
        return Icons.hourglass_top;
      case 'ERREUR':
        return Icons.error_outline;
      case 'EN_ATTENTE':
      default:
        return Icons.schedule;
    }
  }

  String _formatMontant(double montant) {
    if (montant == 0) return 'Montant non disponible';
    final formatter = NumberFormat.currency(
      locale: 'fr_FR',
      symbol: 'FCFA',
      decimalDigits: 0,
    );
    return formatter.format(montant);
  }
}

class _StatusBadge extends StatelessWidget {
  final String statut;

  const _StatusBadge({required this.statut});

  @override
  Widget build(BuildContext context) {
    final color = statusColor(statut);
    final label = statusLabel(statut);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration:
                BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: GoogleFonts.lato(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _RiskBadge extends StatelessWidget {
  final int score;

  const _RiskBadge({required this.score});

  @override
  Widget build(BuildContext context) {
    final color = riskColor(score);
    final label = riskLabel(score);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: GoogleFonts.lato(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icone;
  final String label;
  final Color color;

  const _InfoRow({
    required this.icone,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icone, size: 14, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            label,
            style: GoogleFonts.lato(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w500,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
