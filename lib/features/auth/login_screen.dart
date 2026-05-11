import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/providers/auth_state_provider.dart';
import '../../core/theme/app_theme.dart';
import 'register_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleLogin() {
    if (_formKey.currentState!.validate()) {
      ref.read(authStateProvider.notifier).login(
            _usernameController.text.trim(),
            _passwordController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    // Listen for error state and show snackbar
    ref.listen(authStateProvider, (previous, next) {
      if (next.status == AuthStatus.unauthenticated && next.errorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.errorMessage!),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    });

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppTheme.backgroundColor,
              Color(0xFF1E1B4B), // Deep purple shade
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 40),
                // Logo/Branding
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      border: Border.all(
                          color: AppTheme.primaryColor.withOpacity(0.2)),
                    ),
                    child: const Icon(
                      Icons.auto_awesome_motion,
                      color: AppTheme.accentColor,
                      size: 60,
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                Center(
                  child: Text(
                    'Welcome Back',
                    style: Theme.of(context).textTheme.displayLarge,
                  ),
                ),
                const SizedBox(height: 8),
                Center(
                  child: Text(
                    'Sign in to access Sign2Voice AI',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
                const SizedBox(height: 48),

                // Glass Container for inputs
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceColor.withOpacity(0.6),
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        // Username Input
                        TextFormField(
                          controller: _usernameController,
                          decoration: InputDecoration(
                            labelText: 'Username',
                            prefixIcon: const Icon(Icons.person_outline),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            filled: true,
                            fillColor: Colors.black12,
                          ),
                          validator: (val) => val == null || val.isEmpty
                              ? 'Please enter username'
                              : null,
                        ),
                        const SizedBox(height: 20),
                        // Password Input
                        TextFormField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            filled: true,
                            fillColor: Colors.black12,
                          ),
                          validator: (val) => val == null || val.isEmpty
                              ? 'Please enter password'
                              : null,
                        ),
                        const SizedBox(height: 24),
                        // Sign In Button
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: authState.status == AuthStatus.loading
                                ? null
                                : _handleLogin,
                            child: authState.status == AuthStatus.loading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2, color: Colors.white))
                                : const Text('Sign In'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 32),

                // Divider line
                Row(
                  children: [
                    const Expanded(child: Divider(color: Colors.white24)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('OR', style: TextStyle(color: Colors.white38)),
                    ),
                    const Expanded(child: Divider(color: Colors.white24)),
                  ],
                ),

                const SizedBox(height: 32),

                // Google Sign-In Button
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16)),
                      side: const BorderSide(color: Colors.white24),
                    ),
                    icon: Image.network(
                      'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png',
                      height: 24,
                    ),
                    label: const Text('Continue with Google',
                        style: TextStyle(color: Colors.white, fontSize: 16)),
                    onPressed: authState.status == AuthStatus.loading
                        ? null
                        : () {
                            ref
                                .read(authStateProvider.notifier)
                                .signInWithGoogle();
                          },
                  ),
                ),

                const SizedBox(height: 40),

                // Register switch
                Center(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text("Don't have an account? "),
                      GestureDetector(
                        onTap: () {
                          Navigator.of(context).push(MaterialPageRoute(
                              builder: (context) => const RegisterScreen()));
                        },
                        child: const Text(
                          'Sign Up',
                          style: TextStyle(
                            color: AppTheme.accentColor,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
