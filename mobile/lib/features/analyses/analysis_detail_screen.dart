import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:percent_indicator/percent_indicator.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class AnalysisDetailScreen extends ConsumerWidget {
  final String analyseId;
  const AnalysisDetailScreen({super.key, required this.analyseId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyseAsync = ref.watch(analyseDetailProvider(analyseId));
    return analyseAsync.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(appBar: AppBar(title: const Text('Détail')), body: Center(child: Text('Erreur : $e'))),
      data: (analyse) => _AnalyseDetailView(analyse: analyse),
    );
  }
}

class _AnalyseDetailView extends StatelessWidget {
  final AnalyseFinanciere analyse;
  const _AnalyseDetailView({required this.analyse});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: Text(analyse.nomEntreprise, overflow: TextOverflow.ellipsis),
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white60,
            indicatorColor: Colors.white,
            tabs: [
              Tab(text: 'Résumé'),
              Tab(text: 'Ratios'),
              Tab(text: 'Rapport'),
            ],
          ),
        ),
        body: TabBarView(children: [
          _ResumTab(analyse: analyse),
          _RatiosTab(analyse: analyse),
          _RapportTab(analyseId: analyse.id),
        ]),
      ),
    );
  }
}

class _ResumTab extends StatelessWidget {
  final AnalyseFinanciere analyse;
  const _ResumTab({required this.analyse});

  @override
  Widget build(BuildContext context) {
    final riskColor = AppTheme.riskColor(analyse.scoreRisque);
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Center(
          child: CircularPercentIndicator(
            radius: 70,
            lineWidth: 10,
            percent: analyse.statut == 'TERMINE' ? analyse.scoreRisque / 100 : 0,
            center: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('${analyse.scoreRisque}', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: riskColor)),
              const Text('/100', style: TextStyle(fontSize: 12, color: Colors.grey)),
            ]),
            progressColor: riskColor,
            backgroundColor: Colors.grey.shade200,
          ),
        ),
        const SizedBox(height: 16),
        Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(color: riskColor.withOpacity(0.15), borderRadius: BorderRadius.circular(20)),
            child: Text('Risque ${analyse.niveauRisque}', style: TextStyle(color: riskColor, fontWeight: FontWeight.bold, fontSize: 16)),
          ),
        ),
        const SizedBox(height: 24),
        _StatRow(label: 'Exercice', value: analyse.exercice),
        _StatRow(label: 'Statut', value: analyse.statut.replaceAll('_', ' ')),
        _StatRow(label: 'Anomalies détectées', value: '${analyse.nombreAnomalies}'),
        _StatRow(label: 'Montant total analysé', value: '${analyse.montantTotal.toStringAsFixed(0)} FCFA'),
        const SizedBox(height: 20),
        ElevatedButton.icon(
          onPressed: () => context.push('/analyses/${analyse.id}/anomalies'),
          icon: const Icon(Icons.warning_amber),
          label: Text('Voir les ${analyse.nombreAnomalies} anomalie(s)'),
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: Colors.white, padding: const EdgeInsets.all(14)),
        ),
      ],
    );
  }
}

class _StatRow extends StatelessWidget {
  final String label, value;
  const _StatRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _RatiosTab extends StatelessWidget {
  final AnalyseFinanciere analyse;
  const _RatiosTab({required this.analyse});

  static const _ratiosLabels = ['Liquidité', 'Solvabilité', 'Rentabilité', 'Autonomie'];
  static const _ratiosValues = [1.8, 0.65, 0.12, 0.48];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('Ratios financiers clés', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 16),
        SizedBox(
          height: 220,
          child: BarChart(BarChartData(
            barGroups: _ratiosValues.asMap().entries.map((e) => BarChartGroupData(x: e.key, barRods: [
              BarChartRodData(toY: e.value, color: AppColors.primary, width: 30, borderRadius: BorderRadius.circular(4)),
            ])).toList(),
            titlesData: FlTitlesData(
              bottomTitles: AxisTitles(sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (v, _) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(_ratiosLabels[v.toInt()], style: const TextStyle(fontSize: 10)),
                ),
              )),
              leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 32)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            ),
            gridData: const FlGridData(show: false),
            borderData: FlBorderData(show: false),
          )),
        ),
        const SizedBox(height: 20),
        ..._ratiosLabels.asMap().entries.map((e) => ListTile(
          leading: Icon(Icons.show_chart, color: AppColors.primary),
          title: Text(e.value),
          trailing: Text(_ratiosValues[e.key].toStringAsFixed(2), style: const TextStyle(fontWeight: FontWeight.bold)),
        )),
      ],
    );
  }
}

class _RapportTab extends StatelessWidget {
  final String analyseId;
  const _RapportTab({required this.analyseId});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('Télécharger le rapport', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Téléchargement rapport Word...'))),
          icon: const Icon(Icons.description, color: Colors.blue),
          label: const Text('Rapport Word (.docx)'),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.all(14)),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Téléchargement rapport Excel...'))),
          icon: const Icon(Icons.table_chart, color: Colors.green),
          label: const Text('Rapport Excel (.xlsx)'),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.all(14)),
        ),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
          child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [Icon(Icons.auto_awesome, color: Colors.blue), SizedBox(width: 8), Text('Synthèse IA', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue))]),
            SizedBox(height: 8),
            Text('L\'analyse IA a examiné les écritures comptables et identifié des zones de risque. Le score global reflète la conformité aux normes SYSCOHADA et la cohérence des flux financiers détectés par les algorithmes de Benford et Isolation Forest.', style: TextStyle(fontSize: 13, color: Colors.black87)),
          ]),
        ),
      ],
    );
  }
}
