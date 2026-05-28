import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme.dart';
import 'analyses_provider.dart';

class NewAnalysisScreen extends ConsumerStatefulWidget {
  const NewAnalysisScreen({super.key});

  @override
  ConsumerState<NewAnalysisScreen> createState() => _NewAnalysisScreenState();
}

class _NewAnalysisScreenState extends ConsumerState<NewAnalysisScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nomEntrepriseController = TextEditingController();
  String? _exerciceSelectionne;
  PlatformFile? _fichierSelectionne;
  bool _isLoading = false;

  final List<String> _exercices = [
    '2025',
    '2024',
    '2023',
    '2022',
    '2021',
    '2020',
  ];

  @override
  void dispose() {
    _nomEntrepriseController.dispose();
    super.dispose();
  }

  Future<void> _selectionnerFichier() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['txt', 'csv'],
        allowMultiple: false,
      );
      if (result != null && result.files.isNotEmpty) {
        setState(() => _fichierSelectionne = result.files.first);
      }
    } catch (e) {
      if (mounted) {
        _afficherErreur('Erreur lors de la sélection du fichier.');
      }
    }
  }

  Future<void> _lancerAnalyse() async {
    if (!_formKey.currentState!.validate()) return;
    if (_fichierSelectionne == null) {
      _afficherErreur('Veuillez sélectionner un fichier FEC.');
      return;
    }
    if (_fichierSelectionne!.path == null) {
      _afficherErreur('Chemin du fichier invalide.');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final formData = FormData.fromMap({
        'nom_entreprise': _nomEntrepriseController.text.trim(),
        'exercice': _exerciceSelectionne!,
        'fichier_fec': await MultipartFile.fromFile(
          _fichierSelectionne!.path!,
          filename: _fichierSelectionne!.name,
        ),
      });

      final notifier = ref.read(newAnalysisProvider.notifier);
      await notifier.creerAnalyse(
        nomEntreprise: _nomEntrepriseController.text.trim(),
        exercice: _exerciceSelectionne!,
        cheminFichier: _fichierSelectionne!.path!,
        nomFichier: _fichierSelectionne!.name,
      );

      final state = ref.read(newAnalysisProvider);
      if (mounted) {
        if (state.isSuccess) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Row(
                children: [
                  const Icon(Icons.check_circle, color: Colors.white),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Analyse lancée avec succès ! L\'IA traite votre fichier FEC.',
                      style: GoogleFonts.lato(color: Colors.white),
                    ),
                  ),
                ],
              ),
              backgroundColor: AppColors.success,
              duration: const Duration(seconds: 4),
            ),
          );
          if (state.createdId != null) {
            context.go('/analyses/${state.createdId}');
          } else {
            context.go('/analyses');
          }
        } else if (state.errorMessage != null) {
          _afficherErreur(state.errorMessage!);
        }
      }
    } catch (e) {
      if (mounted) {
        _afficherErreur('Erreur lors du lancement de l\'analyse.');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _afficherErreur(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: GoogleFonts.lato(color: Colors.white),
              ),
            ),
          ],
        ),
        backgroundColor: AppColors.error,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Nouvelle analyse'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/analyses'),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ─── Bandeau informatif ──────────────────────────────────
              _buildInfoBanner(),
              const SizedBox(height: 24),

              // ─── Section Informations ────────────────────────────────
              _buildSectionCard(
                titre: 'Informations de l\'entreprise',
                icone: Icons.business_outlined,
                children: [
                  // Champ nom entreprise
                  TextFormField(
                    controller: _nomEntrepriseController,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: 'Nom de l\'entreprise *',
                      hintText: 'Ex: SARL TechBurkina',
                      prefixIcon: Icon(Icons.business),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Le nom de l\'entreprise est requis';
                      }
                      if (value.trim().length < 2) {
                        return 'Le nom doit contenir au moins 2 caractères';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),

                  // Sélection exercice
                  DropdownButtonFormField<String>(
                    value: _exerciceSelectionne,
                    decoration: const InputDecoration(
                      labelText: 'Exercice fiscal *',
                      prefixIcon: Icon(Icons.calendar_today_outlined),
                    ),
                    items: _exercices
                        .map((e) => DropdownMenuItem(
                              value: e,
                              child: Text(e),
                            ))
                        .toList(),
                    onChanged: (value) {
                      setState(() => _exerciceSelectionne = value);
                    },
                    validator: (value) {
                      if (value == null) {
                        return 'Veuillez sélectionner l\'exercice';
                      }
                      return null;
                    },
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ─── Section Fichier FEC ─────────────────────────────────
              _buildSectionCard(
                titre: 'Fichier FEC SYSCOHADA',
                icone: Icons.upload_file_outlined,
                children: [
                  _buildFilePicker(),
                ],
              ),
              const SizedBox(height: 16),

              // ─── Info FEC ────────────────────────────────────────────
              _buildFecInfo(),
              const SizedBox(height: 32),

              // ─── Bouton lancer ───────────────────────────────────────
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _lancerAnalyse,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    disabledBackgroundColor: AppColors.primary.withOpacity(0.5),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2.5,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              'Envoi en cours...',
                              style: GoogleFonts.lato(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        )
                      : Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.psychology_outlined, size: 22),
                            const SizedBox(width: 10),
                            Text(
                              'Lancer l\'analyse IA',
                              style: GoogleFonts.lato(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoBanner() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.infoLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.primary.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.info_outline,
            color: AppColors.primary,
            size: 22,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Analyse IA automatique',
                  style: GoogleFonts.lato(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'L\'IA analysera votre fichier FEC, détectera les anomalies comptables et calculera un score de risque global.',
                  style: GoogleFonts.lato(
                    fontSize: 12,
                    color: AppColors.primaryDark,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionCard({
    required String titre,
    required IconData icone,
    required List<Widget> children,
  }) {
    return Container(
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
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            child: Row(
              children: [
                Icon(icone, color: AppColors.primary, size: 20),
                const SizedBox(width: 8),
                Text(
                  titre,
                  style: GoogleFonts.lato(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: children,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilePicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: _selectionnerFichier,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              border: Border.all(
                color: _fichierSelectionne != null
                    ? AppColors.success
                    : AppColors.divider,
                width: 2,
                style: BorderStyle.solid,
              ),
              borderRadius: BorderRadius.circular(10),
              color: _fichierSelectionne != null
                  ? AppColors.successLight
                  : AppColors.background,
            ),
            child: _fichierSelectionne == null
                ? Column(
                    children: [
                      const Icon(
                        Icons.cloud_upload_outlined,
                        size: 40,
                        color: AppColors.textHint,
                      ),
                      const SizedBox(height: 10),
                      Text(
                        'Appuyez pour sélectionner votre fichier FEC',
                        style: GoogleFonts.lato(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Formats acceptés : .txt, .csv',
                        style: GoogleFonts.lato(
                          fontSize: 12,
                          color: AppColors.textHint,
                        ),
                      ),
                    ],
                  )
                : Row(
                    children: [
                      const Icon(
                        Icons.check_circle,
                        color: AppColors.success,
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _fichierSelectionne!.name,
                              style: GoogleFonts.lato(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: AppColors.textPrimary,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 3),
                            Text(
                              _formatTaille(_fichierSelectionne!.size),
                              style: GoogleFonts.lato(
                                fontSize: 12,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: AppColors.error),
                        onPressed: () {
                          setState(() => _fichierSelectionne = null);
                        },
                      ),
                    ],
                  ),
          ),
        ),
        if (_fichierSelectionne == null) ...[
          const SizedBox(height: 8),
          TextButton.icon(
            onPressed: _selectionnerFichier,
            icon: const Icon(Icons.folder_open_outlined, size: 18),
            label: const Text('Parcourir les fichiers'),
          ),
        ],
      ],
    );
  }

  Widget _buildFecInfo() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.warningLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.warning.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.help_outline,
                color: AppColors.warning,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'À propos du fichier FEC',
                style: GoogleFonts.lato(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppColors.warning,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...[
            'Le FEC (Fichier des Écritures Comptables) est le fichier standard SYSCOHADA.',
            'Il doit contenir toutes les écritures de l\'exercice sélectionné.',
            'Format attendu : délimiteur tabulation ou point-virgule.',
            'Taille maximale recommandée : 50 Mo.',
          ].map(
            (text) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ',
                      style: TextStyle(color: AppColors.warning)),
                  Expanded(
                    child: Text(
                      text,
                      style: GoogleFonts.lato(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatTaille(int bytes) {
    if (bytes < 1024) return '$bytes octets';
    if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} Ko';
    }
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} Mo';
  }
}
