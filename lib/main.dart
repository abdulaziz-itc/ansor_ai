import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'features/record/record_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/navigation/main_navigation_screen.dart';
import 'core/providers/auth_state_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Lock orientation to portrait
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}



class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);

    Widget homeWidget;
    
    switch (authState.status) {
      case AuthStatus.initial:
      case AuthStatus.loading:
        homeWidget = const Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        );
        break;
      case AuthStatus.authenticated:
        homeWidget = const MainNavigationScreen();
        break;
      case AuthStatus.unauthenticated:
      default:
        homeWidget = const LoginScreen();
        break;
    }

    return MaterialApp(
      title: 'Sign2Voice AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: homeWidget,
    );
  }
}
