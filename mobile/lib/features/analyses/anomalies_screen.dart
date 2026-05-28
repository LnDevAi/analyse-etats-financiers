import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class AnomaliesScreen extends ConsumerStatefulWidget {
  final String analyseId;
  const AnomaliesScreen({super.key, required this.analyseId});

  @override
  ConsumerState<AnomaliesScreen> createState() => _AnomaliesScreenState();
}

class _AnomaliesScreenState extends ConsumerState<AnomaliesScreen> {
  String _filtre = 'Tout';
  final _filtres = ['Tout', 'CRITIQUE', 'ELEVEE', 'MOYENNE', 'FAIBLE'];

  Color _graviteColor(String gravite) => switch (gravite) {
    'CRITIQUE' => AppColors.accent,
    'ELEVEE' => Colors.orange,
    'MOYENNE' => Colors.amber,
    _ => Colors.green,
  };

  @override
  Widget build(BuildContext context) {
    final anomaliesAsync = ref.watch(anomaliesProvider(widget.analyseId));
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Anomalies détectées'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: _filtres.map((f) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(f),
                  selected: _filtre == f,
                  onSelected: (_) => setState(() => _filtre = f),
                  selectedColor: AppColors.primary,
                  labelStyle: TextStyle(color: _filtre == f ? Colors.white : Colors.black),
                ),
              )).toList(),
            ),
          ),
          Expanded(
            child: anomaliesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Erreur : $e')),
              data: (anomalies) {
                final filtered = _filtre == 'Tout' ? anomalies : anomalies.where((a) => a.gravite == _filtre).toList();
                if (filtered.isEmpty) return const Center(child: Text('Aucune anomalie pour ce filtre.'));
                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: filtered.length,
                  itemBuilder: (_, i) {
                    final a = filtered[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                            Expanded(child: Text(a.type, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14))),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(color: _graviteColor(a.gravite).withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                              child: Text(a.gravite, style: TextStyle(color: _graviteColor(a.gravite), fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                          ]),
                          const SizedBox(height: 6),
                          Text(a.description, style: const TextStyle(color: Colors.black87, fontSize: 13)),
                          if (a.montant > 0) ...[
                            const SizedBox(height: 6),
                            Text('Montant : ${a.montant.toStringAsFixed(0)} FCFA', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                          ],
                        ]),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
