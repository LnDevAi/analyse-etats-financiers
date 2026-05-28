import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/auth_provider.dart';
import '../features/auth/login_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/analyses/analyses_list_screen.dart';
import '../features/analyses/new_analysis_screen.dart';
import '../features/analyses/analysis_detail_screen.dart';
import '../features/analyses/anomalies_screen.dart';
import '../features/profile/profile_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoginPage = state.matchedLocation == '/login';

      if (!isAuthenticated && !isLoginPage) {
        return '/login';
      }
      if (isAuthenticated && isLoginPage) {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) {
          return AppShell(child: child);
        },
        routes: [
          GoRoute(
            path: '/dashboard',
            name: 'dashboard',
            builder: (context, state) => const DashboardContent(),
          ),
          GoRoute(
            path: '/analyses',
            name: 'analyses',
            builder: (context, state) => const AnalysesListScreen(),
            routes: [
              GoRoute(
                path: 'new',
                name: 'new-analysis',
                builder: (context, state) => const NewAnalysisScreen(),
              ),
              GoRoute(
                path: ':id',
                name: 'analysis-detail',
                builder: (context, state) {
                  final id = state.pathParameters['id']!;
                  return AnalysisDetailScreen(analyseId: id);
                },
                routes: [
                  GoRoute(
                    path: 'anomalies',
                    name: 'anomalies',
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return AnomaliesScreen(analyseId: id);
                    },
                  ),
                ],
              ),
            ],
          ),
          GoRoute(
            path: '/anomalies',
            name: 'all-anomalies',
            builder: (context, state) => const AnomaliesScreen(analyseId: null),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Page introuvable')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('Page introuvable', style: TextStyle(fontSize: 18)),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: () => context.go('/dashboard'),
              child: const Text('Retour à l\'accueil'),
            ),
          ],
        ),
      ),
    ),
  );
});

class AppShell extends ConsumerStatefulWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _currentIndex = 0;

  static const _routes = [
    '/dashboard',
    '/analyses',
    '/anomalies',
    '/profile',
  ];

  void _onTabTapped(int index) {
    context.go(_routes[index]);
    setState(() => _currentIndex = index);
  }

  int _getIndexFromLocation(String location) {
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/analyses')) return 1;
    if (location.startsWith('/anomalies')) return 2;
    if (location.startsWith('/profile')) return 3;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _getIndexFromLocation(location);

    return Scaffold(
      body: widget.child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIndex,
        onTap: _onTabTapped,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard_outlined),
            activeIcon: Icon(Icons.dashboard),
            label: 'Tableau de bord',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics_outlined),
            activeIcon: Icon(Icons.analytics),
            label: 'Analyses',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.warning_amber_outlined),
            activeIcon: Icon(Icons.warning_amber),
            label: 'Anomalies',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: 'Profil',
          ),
        ],
      ),
    );
  }
}
