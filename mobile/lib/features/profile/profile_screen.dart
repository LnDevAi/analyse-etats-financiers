import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme.dart';
import '../auth/auth_provider.dart';
import '../analyses/analyses_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final analysesAsync = ref.watch(analysesProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Mon profil'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Se déconnecter',
            onPressed: () => _confirmerDeconnexion(context, ref),
          ),
        ],
      ),
      body: user == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Column(
                children: [
                  // ─── En-tête profil ──────────────────────────────────
                  _buildHeader(user),

                  // ─── Statistiques personnelles ───────────────────────
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSectionTitle('Mes statistiques'),
                        const SizedBox(height: 12),
                        analysesAsync.when(
                          loading: () => const Center(
                            child: Padding(
                              padding: EdgeInsets.all(16),
                              child: CircularProgressIndicator(),
                            ),
                          ),
                          error: (_, __) => _buildStatsVides(),
                          data: (analyses) =>
                              _buildStats(analyses.length, analyses),
                        ),
                        const SizedBox(height: 20),

                        // ─── Informations du compte ──────────────────
                        _buildSectionTitle('Informations du compte'),
                        const SizedBox(height: 12),
                        _buildInfoCard(user),
                        const SizedBox(height: 20),

                        // ─── Paramètres ──────────────────────────────
                        _buildSectionTitle('Paramètres'),
                        const SizedBox(height: 12),
                        _buildParametresCard(context),
                        const SizedBox(height: 20),

                        // ─── À propos ────────────────────────────────
                        _buildSectionTitle('À propos'),
                        const SizedBox(height: 12),
                        _buildAboutCard(),
                        const SizedBox(height: 20),

                        // ─── Bouton déconnexion ──────────────────────
                        SizedBox(
                          width: double.infinity,
                          height: 50,
                          child: OutlinedButton.icon(
                            onPressed: () =>
                                _confirmerDeconnexion(context, ref),
                            icon: const Icon(Icons.logout),
                            label: const Text('Se déconnecter'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppColors.error,
                              side: const BorderSide(
                                  color: AppColors.error),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildHeader(UserProfile user) {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primary, AppColors.primaryLight],
        ),
      ),
      padding: const EdgeInsets.fromLTRB(24, 32, 24, 32),
      child: Column(
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
              border: Border.all(
                  color: Colors.white.withOpacity(0.5), width: 3),
            ),
            child: Center(
              child: Text(
                _initiales(user.fullName),
                style: GoogleFonts.lato(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            user.fullName.isNotEmpty ? user.fullName : user.email,
            style: GoogleFonts.lato(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            user.email,
            style: GoogleFonts.lato(
              fontSize: 14,
              color: Colors.white.withOpacity(0.85),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _HeaderBadge(
                icone: Icons.badge_outlined,
                label: user.displayRole,
              ),
              if (user.tenantName.isNotEmpty) ...[
                const SizedBox(width: 10),
                _HeaderBadge(
                  icone: Icons.business_outlined,
                  label: user.tenantName,
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  String _initiales(String nom) {
    if (nom.isEmpty) return '?';
    final parts = nom.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return nom[0].toUpperCase();
  }

  Widget _buildStats(int totalAnalyses, List analyses) {
    final terminees =
        analyses.where((a) => a.statut == 'TERMINE').length;
    final totalAnomalies = analyses.fold<int>(
        0, (sum, a) => sum + (a.nombreAnomalies as int));

    return Row(
      children: [
        Expanded(
          child: _StatItem(
            valeur: totalAnalyses.toString(),
            label: 'Analyses\nréalisées',
            icone: Icons.analytics_outlined,
            couleur: AppColors.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatItem(
            valeur: terminees.toString(),
            label: 'Analyses\nterminées',
            icone: Icons.check_circle_outline,
            couleur: AppColors.success,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatItem(
            valeur: totalAnomalies.toString(),
            label: 'Anomalies\ndétectées',
            icone: Icons.warning_amber_outlined,
            couleur: AppColors.warning,
          ),
        ),
      ],
    );
  }

  Widget _buildStatsVides() {
    return Row(
      children: [
        Expanded(
          child: _StatItem(
            valeur: '-',
            label: 'Analyses\nréalisées',
            icone: Icons.analytics_outlined,
            couleur: AppColors.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatItem(
            valeur: '-',
            label: 'Analyses\nterminées',
            icone: Icons.check_circle_outline,
            couleur: AppColors.success,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatItem(
            valeur: '-',
            label: 'Anomalies\ndétectées',
            icone: Icons.warning_amber_outlined,
            couleur: AppColors.warning,
          ),
        ),
      ],
    );
  }

  Widget _buildSectionTitle(String titre) {
    return Text(
      titre,
      style: GoogleFonts.lato(
        fontSize: 16,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
      ),
    );
  }

  Widget _buildInfoCard(UserProfile user) {
    return _InfoCard(
      rows: [
        _InfoRowData(icone: Icons.person_outline, label: 'Nom complet', valeur: user.fullName),
        _InfoRowData(icone: Icons.email_outlined, label: 'Email', valeur: user.email),
        _InfoRowData(icone: Icons.badge_outlined, label: 'Rôle', valeur: user.displayRole),
        if (user.tenantName.isNotEmpty)
          _InfoRowData(
              icone: Icons.business_outlined,
              label: 'Entreprise',
              valeur: user.tenantName),
      ],
    );
  }

  Widget _buildParametresCard(BuildContext context) {
    return Container(
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
        children: [
          _MenuRow(
            icone: Icons.notifications_outlined,
            label: 'Notifications',
            onTap: () => _afficherInfoBientot(context),
          ),
          const Divider(height: 1, indent: 16),
          _MenuRow(
            icone: Icons.security_outlined,
            label: 'Sécurité & mot de passe',
            onTap: () => _afficherInfoBientot(context),
          ),
          const Divider(height: 1, indent: 16),
          _MenuRow(
            icone: Icons.language_outlined,
            label: 'Langue',
            valeur: 'Français',
            onTap: () => _afficherInfoBientot(context),
          ),
        ],
      ),
    );
  }

  Widget _buildAboutCard() {
    return _InfoCard(
      rows: [
        _InfoRowData(
          icone: Icons.info_outline,
          label: 'Application',
          valeur: 'Analyse États Financiers IA',
        ),
        _InfoRowData(
          icone: Icons.tag_outlined,
          label: 'Version',
          valeur: '1.0.0',
        ),
        _InfoRowData(
          icone: Icons.copyright_outlined,
          label: 'Éditeur',
          valeur: 'E-DÉFENCE V4',
        ),
        _InfoRowData(
          icone: Icons.gavel_outlined,
          label: 'Conformité',
          valeur: 'SYSCOHADA · FEC · UEMOA',
        ),
      ],
    );
  }

  void _afficherInfoBientot(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Cette fonctionnalité sera disponible prochainement.'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _confirmerDeconnexion(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Text(
          'Déconnexion',
          style: GoogleFonts.lato(
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        content: Text(
          'Êtes-vous sûr de vouloir vous déconnecter de votre compte ?',
          style: GoogleFonts.lato(
            fontSize: 14,
            color: AppColors.textSecondary,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(
              'Annuler',
              style: GoogleFonts.lato(color: AppColors.textSecondary),
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              await ref.read(authNotifierProvider.notifier).logout();
              if (context.mounted) {
                context.go('/login');
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: Text(
              'Se déconnecter',
              style: GoogleFonts.lato(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Data models pour widgets ─────────────────────────────────────────────────

class _InfoRowData {
  final IconData icone;
  final String label;
  final String valeur;

  const _InfoRowData({
    required this.icone,
    required this.label,
    required this.valeur,
  });
}

// ─── Widgets internes ─────────────────────────────────────────────────────────

class _HeaderBadge extends StatelessWidget {
  final IconData icone;
  final String label;

  const _HeaderBadge({required this.icone, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icone, size: 14, color: Colors.white),
          const SizedBox(width: 5),
          Text(
            label,
            style: GoogleFonts.lato(
              fontSize: 12,
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String valeur;
  final String label;
  final IconData icone;
  final Color couleur;

  const _StatItem({
    required this.valeur,
    required this.label,
    required this.icone,
    required this.couleur,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icone, color: couleur, size: 24),
          const SizedBox(height: 8),
          Text(
            valeur,
            style: GoogleFonts.lato(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: GoogleFonts.lato(
              fontSize: 11,
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final List<_InfoRowData> rows;

  const _InfoCard({required this.rows});

  @override
  Widget build(BuildContext context) {
    return Container(
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
        children: rows.asMap().entries.map((entry) {
          final isLast = entry.key == rows.length - 1;
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    Icon(entry.value.icone,
                        size: 18, color: AppColors.primary),
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 110,
                      child: Text(
                        entry.value.label,
                        style: GoogleFonts.lato(
                          fontSize: 13,
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        entry.value.valeur,
                        style: GoogleFonts.lato(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                        textAlign: TextAlign.end,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
              if (!isLast)
                const Divider(height: 1, indent: 16),
            ],
          );
        }).toList(),
      ),
    );
  }
}

class _MenuRow extends StatelessWidget {
  final IconData icone;
  final String label;
  final String? valeur;
  final VoidCallback onTap;

  const _MenuRow({
    required this.icone,
    required this.label,
    this.valeur,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Icon(icone, size: 18, color: AppColors.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: GoogleFonts.lato(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: AppColors.textPrimary,
                ),
              ),
            ),
            if (valeur != null) ...[
              Text(
                valeur!,
                style: GoogleFonts.lato(
                  fontSize: 13,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(width: 4),
            ],
            const Icon(Icons.chevron_right,
                size: 18, color: AppColors.textHint),
          ],
        ),
      ),
    );
  }
}
