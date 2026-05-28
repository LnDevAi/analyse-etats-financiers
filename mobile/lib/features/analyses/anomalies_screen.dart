import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class AnomaliesScreen extends ConsumerStatefulWidget {
  final String? analyseId;

  const AnomaliesScreen({super.key, required this.analyseId});

  @override
  ConsumerState<AnomaliesScreen> createState() => _AnomaliesScreenState();
}

class _AnomaliesScreenState extends ConsumerState<AnomaliesScreen> {
  String _filtreGravite = 'TOUT';

  static const _filtres = [
    ('TOUT', 'Toutes'),
    ('CRITIQUE', 'Critique'),
    ('ELEVEE', 'Élevée'),
    ('MOYENNE', 'Moyenne'),
    ('FAIBLE', 'Faible'),
  ];

  @override
  Widget build(BuildContext context) {
    final anomaliesAsync = ref.watch(anomaliesProvider(widget.analyseId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          widget.analyseId != null
              ? 'Anomalies détectées'
              : 'Toutes les anomalies',
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (widget.analyseId != null) {
              context.go('/analyses/${widget.analyseId}');
            } else {
              context.go('/dashboard');
            }
          },
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualiser',
            onPressed: () =>
                ref.refresh(anomaliesProvider(widget.analyseId)),
          ),
        ],
      ),
      body: anomaliesAsync.when(
        loading: () => const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Chargement des anomalies...'),
            ],
          ),
        ),
        error: (error, _) => _buildError(ref, error.toString()),
        data: (anomalies) => _buildContent(anomalies),
      ),
    );
  }

  Widget _buildError(WidgetRef ref, String error) {
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
              'Impossible de charger les anomalies',
              style: GoogleFonts.lato(
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: GoogleFonts.lato(
                  fontSize: 13, color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.refresh(anomaliesProvider(widget.analyseId)),
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(List<AnomalieItem> anomalies) {
    final anomaliesFiltrees = _filtreGravite == 'TOUT'
        ? anomalies
        : anomalies
            .where((a) => a.gravite.toUpperCase() == _filtreGravite)
            .toList();

    final counts = {
      'CRITIQUE':
          anomalies.where((a) => a.gravite.toUpperCase() == 'CRITIQUE').length,
      'ELEVEE':
          anomalies.where((a) => a.gravite.toUpperCase() == 'ELEVEE').length,
      'MOYENNE':
          anomalies.where((a) => a.gravite.toUpperCase() == 'MOYENNE').length,
      'FAIBLE':
          anomalies.where((a) => a.gravite.toUpperCase() == 'FAIBLE').length,
    };

    return Column(
      children: [
        // ─── Résumé par gravité ──────────────────────────────────────
        if (anomalies.isNotEmpty) ...[
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${anomalies.length} anomalie${anomalies.length > 1 ? 's' : ''} détectée${anomalies.length > 1 ? 's' : ''}',
                  style: GoogleFonts.lato(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _GraviteCount(
                        gravite: 'CRITIQUE',
                        nombre: counts['CRITIQUE']!),
                    const SizedBox(width: 8),
                    _GraviteCount(
                        gravite: 'ELEVEE', nombre: counts['ELEVEE']!),
                    const SizedBox(width: 8),
                    _GraviteCount(
                        gravite: 'MOYENNE', nombre: counts['MOYENNE']!),
                    const SizedBox(width: 8),
                    _GraviteCount(
                        gravite: 'FAIBLE', nombre: counts['FAIBLE']!),
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1),
        ],

        // ─── Filtres chips ────────────────────────────────────────────
        Container(
          color: Colors.white,
          padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: _filtres.map((filtre) {
                final (code, label) = filtre;
                final isSelected = _filtreGravite == code;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(
                      code == 'TOUT'
                          ? '$label (${anomalies.length})'
                          : '$label (${counts[code] ?? 0})',
                    ),
                    selected: isSelected,
                    onSelected: (_) {
                      setState(() => _filtreGravite = code);
                    },
                    selectedColor: _chipColor(code),
                    checkmarkColor: Colors.white,
                    labelStyle: GoogleFonts.lato(
                      fontSize: 13,
                      fontWeight: isSelected
                          ? FontWeight.w700
                          : FontWeight.normal,
                      color: isSelected
                          ? Colors.white
                          : AppColors.textSecondary,
                    ),
                    backgroundColor: AppColors.background,
                    side: BorderSide(
                      color: isSelected
                          ? _chipColor(code)
                          : AppColors.divider,
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ),
        const Divider(height: 1),

        // ─── Liste anomalies ─────────────────────────────────────────
        Expanded(
          child: anomaliesFiltrees.isEmpty
              ? _buildVide()
              : RefreshIndicator(
                  onRefresh: () async {},
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: anomaliesFiltrees.length,
                    itemBuilder: (context, index) {
                      return _AnomalieCard(
                          anomalie: anomaliesFiltrees[index]);
                    },
                  ),
                ),
        ),
      ],
    );
  }

  Color _chipColor(String gravite) {
    switch (gravite) {
      case 'CRITIQUE':
        return AppColors.error;
      case 'ELEVEE':
        return AppColors.warning;
      case 'MOYENNE':
        return const Color(0xFFF39C12);
      case 'FAIBLE':
        return AppColors.success;
      default:
        return AppColors.primary;
    }
  }

  Widget _buildVide() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.successLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle_outline,
                size: 52,
                color: AppColors.success,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _filtreGravite == 'TOUT'
                  ? 'Aucune anomalie détectée'
                  : 'Aucune anomalie de ce niveau',
              style: GoogleFonts.lato(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              _filtreGravite == 'TOUT'
                  ? 'Excellent ! Les états financiers semblent cohérents.'
                  : 'Aucune anomalie de gravité "${_filtreGravite.toLowerCase()}" trouvée.',
              style: GoogleFonts.lato(
                fontSize: 13,
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Widgets internes ─────────────────────────────────────────────────────────

class _GraviteCount extends StatelessWidget {
  final String gravite;
  final int nombre;

  const _GraviteCount({required this.gravite, required this.nombre});

  @override
  Widget build(BuildContext context) {
    final color = graviteColor(gravite);

    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(
              '$nombre',
              style: GoogleFonts.lato(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
            Text(
              _shortLabel(gravite),
              style: GoogleFonts.lato(
                fontSize: 10,
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _shortLabel(String gravite) {
    switch (gravite) {
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

class _AnomalieCard extends StatelessWidget {
  final AnomalieItem anomalie;

  const _AnomalieCard({required this.anomalie});

  @override
  Widget build(BuildContext context) {
    final color = graviteColor(anomalie.gravite);
    final currency = NumberFormat.currency(
      locale: 'fr_FR',
      symbol: 'FCFA',
      decimalDigits: 0,
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border(
          left: BorderSide(color: color, width: 4),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ─── En-tête ─────────────────────────────────────────
            Row(
              children: [
                Expanded(
                  child: Text(
                    anomalie.type,
                    style: GoogleFonts.lato(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                _GraviteBadge(gravite: anomalie.gravite),
              ],
            ),
            const SizedBox(height: 8),

            // ─── Description ──────────────────────────────────────
            Text(
              anomalie.description,
              style: GoogleFonts.lato(
                fontSize: 13,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 10),
            const Divider(height: 1),
            const SizedBox(height: 10),

            // ─── Métadonnées ──────────────────────────────────────
            Row(
              children: [
                if (anomalie.montant != 0) ...[
                  const Icon(Icons.attach_money,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    currency.format(anomalie.montant.abs()),
                    style: GoogleFonts.lato(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: color,
                    ),
                  ),
                  const SizedBox(width: 16),
                ],
                if (anomalie.compte != null) ...[
                  const Icon(Icons.account_tree_outlined,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    'Compte ${anomalie.compte}',
                    style: GoogleFonts.lato(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(width: 16),
                ],
                if (anomalie.dateEcriture != null) ...[
                  const Icon(Icons.calendar_today_outlined,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    anomalie.dateEcriture!,
                    style: GoogleFonts.lato(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _GraviteBadge extends StatelessWidget {
  final String gravite;

  const _GraviteBadge({required this.gravite});

  @override
  Widget build(BuildContext context) {
    final color = graviteColor(gravite);
    final label = _label(gravite);

    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: GoogleFonts.lato(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }

  String _label(String gravite) {
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
