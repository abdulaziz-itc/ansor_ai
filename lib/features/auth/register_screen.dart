import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/providers/auth_state_provider.dart';
import '../../core/theme/app_theme.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _fullNameController.dispose();
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleRegister() {
    if (_formKey.currentState!.validate()) {
      ref.read(authStateProvider.notifier).register(
            _usernameController.text.trim(),
            _emailController.text.trim(),
            _passwordController.text.trim(),
            _fullNameController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    // Pop out of this screen if we suddenly get authenticated 
    // (notifier should handle main route switches but this ensures safety stack unwind)
    ref.listen(authStateProvider, (previous, next) {
      if (next.status == AuthStatus.authenticated) {
         Navigator.of(context).pop();
      }
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
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      extendBodyBehindAppBar: true,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topRight,
            end: Alignment.bottomLeft,
            colors: [
              AppTheme.backgroundColor,
              Color(0xFF312E81), // Indigo shade
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Create Account',
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 28),
                ),
                const SizedBox(height: 8),
                Text(
                  'Join our community today!',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 32),

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
                        // Full Name
                        TextFormField(
                          controller: _fullNameController,
                          decoration: _inputDecoration('Full Name', Icons.badge_outlined),
                          validator: (val) => val == null || val.isEmpty ? 'Enter your name' : null,
                        ),
                        const SizedBox(height: 16),
                        
                        // Username
                        TextFormField(
                          controller: _usernameController,
                          decoration: _inputDecoration('Username', Icons.alternate_email),
                          validator: (val) => val == null || val.isEmpty ? 'Pick a username' : null,
                        ),
                        const SizedBox(height: 16),
                        
                        // Email
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          decoration: _inputDecoration('Email', Icons.email_outlined),
                          validator: (val) => val == null || !val.contains('@') ? 'Enter valid email' : null,
                        ),
                        const SizedBox(height: 16),
                        
                        // Password
                        TextFormField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: _inputDecoration('Password', Icons.lock_outline),
                          validator: (val) => val == null || val.length < 6 ? 'Minimum 6 chars required' : null,
                        ),
                        const SizedBox(height: 32),

                        // Signup Action
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: authState.status == AuthStatus.loading ? null : _handleRegister,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.accentColor,
                            ),
                            child: authState.status == AuthStatus.loading
                                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : const Text('Complete Registration'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      filled: true,
      fillColor: Colors.black12,
    );
  }
}
