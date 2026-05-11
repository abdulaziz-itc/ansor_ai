import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/api/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/providers/auth_state_provider.dart';

class ChatListScreen extends ConsumerWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final apiClient = ref.watch(apiClientProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chats'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white60),
            onPressed: () {
              // Easy way to test logout
              ref.read(authStateProvider.notifier).logout();
            },
          )
        ],
      ),
      body: FutureBuilder(
        future: apiClient.getChats(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          // Even if backend errors out, show elegant mockup/empty for this pass
          final hasError = snapshot.hasError;
          final List<dynamic> chats = !hasError && snapshot.data != null 
              ? snapshot.data!.data 
              : [];

          if (chats.isEmpty) {
            return _buildEmptyState(context);
          }

          return ListView.builder(
            itemCount: chats.length,
            padding: const EdgeInsets.all(16),
            itemBuilder: (context, index) {
              final chat = chats[index];
              return _buildChatTile(context, chat);
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Place holder for starting new chat
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Starting new chat logic...")),
          );
        },
        backgroundColor: AppTheme.accentColor,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.chat_bubble_outline_rounded,
            size: 80,
            color: Colors.white.withOpacity(0.1),
          ),
          const SizedBox(height: 24),
          Text(
            'No chats yet',
            style: Theme.of(context).textTheme.displayMedium?.copyWith(
                  color: Colors.white30,
                  fontSize: 20,
                ),
          ),
          const SizedBox(height: 8),
          const Text('Start a conversation by using the main recorder!'),
        ],
      ),
    );
  }

  Widget _buildChatTile(BuildContext context, dynamic chat) {
    // Simple mapping based on schemas
    final name = chat['name'] ?? 'Unnamed Chat #${chat['id']}';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor.withOpacity(0.5),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white10),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: AppTheme.primaryColor.withOpacity(0.2),
          child: const Icon(Icons.person, color: AppTheme.primaryColor),
        ),
        title: Text(
          name,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: const Text('Last active: Just now', style: TextStyle(color: Colors.white38)),
        trailing: const Icon(Icons.chevron_right, color: Colors.white24),
        onTap: () {
          // Placeholder for entering concrete chat detailed view
        },
      ),
    );
  }
}
