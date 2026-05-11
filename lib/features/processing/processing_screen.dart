import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../data/repository/video_repository.dart';
import '../../data/api/websocket_service.dart';
import '../result/result_screen.dart';
import '../../core/theme/app_theme.dart';
import '../../data/repository/history_repository.dart';
import '../../data/models/api_response.dart';

class ProcessingScreen extends ConsumerStatefulWidget {
  final String videoPath;
  const ProcessingScreen({super.key, required this.videoPath});

  @override
  ConsumerState<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends ConsumerState<ProcessingScreen> with TickerProviderStateMixin {
  late AnimationController _pulseController;
  String _statusText = 'Uploading video...';
  bool _hasError = false;
  String _errorMessage = '';
  StreamSubscription? _wsSubscription;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _uploadAndProcess();
  }

  Future<void> _uploadAndProcess() async {
    try {
      final repository = ref.read(videoRepositoryProvider);
      final historyRepo = ref.read(historyRepositoryProvider);
      final wsService = ref.read(webSocketServiceProvider);
      
      // 1. Setup dummy context (until authenticating UI is complete)
      const dummyChatId = 1;
      const dummyUserId = 1; // Needed for WebSocket identifier

      // 2. Connect websocket listener
      wsService.connect(dummyUserId);
      
      setState(() => _statusText = 'Sending to server...');
      
      // Setup the listener to resolve once we get matching results
      final completer = Completer<AIProcessingResult>();
      _wsSubscription = wsService.results.listen((result) {
        if (!completer.isCompleted) {
           completer.complete(result);
        }
      });

      // 3. Start upload (Non-blocking/Quick Accept response)
      await repository.uploadVideo(dummyChatId, widget.videoPath);
      
      setState(() => _statusText = 'AI is translating signs...');

      // 4. Wait for web socket to fire completing the processing
      // Timeout protection included for failsafe (e.g. 2 minutes)
      final finalResult = await completer.future.timeout(
        const Duration(minutes: 2),
        onTimeout: () => throw TimeoutException('AI processing took too long. Please check back later.'),
      );
      
      // Save to history
      await historyRepo.saveResult(finalResult);
      
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => ResultScreen(result: finalResult),
          ),
        );
      }
    } catch (e) {
      String message = e.toString();
      if (e is TimeoutException) {
        message = "System timed out waiting for AI. It may still process in backend.";
      } else if (e is DioException && e.response?.data != null) {
        final data = e.response?.data;
        if (data is Map && data.containsKey('detail')) {
          final detail = data['detail'];
          if (detail is String) {
            message = detail;
          } else if (detail is List && detail.isNotEmpty) {
            final firstError = detail[0];
            message = firstError is Map && firstError.containsKey('msg') 
                ? firstError['msg'].toString() 
                : detail.toString();
          }
        }
      }
      
      if (mounted) {
        setState(() {
          _hasError = true;
          _statusText = 'Processing failed';
          _errorMessage = message;
        });
      }
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _wsSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          color: AppTheme.backgroundColor,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated Pulse Effect
            Stack(
              alignment: Alignment.center,
              children: [
                ScaleTransition(
                  scale: Tween(begin: 1.0, end: 1.5).animate(
                    CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
                  ),
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppTheme.primaryColor.withOpacity(0.2),
                    ),
                  ),
                ),
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: AppTheme.accentColor.withOpacity(0.5), width: 2),
                  ),
                  child: Icon(
                    _hasError ? Icons.error_outline : Icons.auto_awesome,
                    color: _hasError ? Colors.red : AppTheme.accentColor,
                    size: 40,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 48),
            
            Text(
              _statusText,
              style: Theme.of(context).textTheme.displayMedium?.copyWith(fontSize: 24),
            ),
            
            const SizedBox(height: 16),
            
            if (_hasError) ...[
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 40),
                child: Text(
                  _errorMessage,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.redAccent),
                ),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Try Again'),
              ),
            ] else 
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 60),
                child: LinearProgressIndicator(
                  backgroundColor: Colors.white10,
                  color: AppTheme.primaryColor,
                  borderRadius: BorderRadius.all(Radius.circular(10)),
                  minHeight: 6,
                ),
              ),
            
            const SizedBox(height: 12),
            if (!_hasError)
              const Text(
                'This might take a few seconds',
                style: TextStyle(color: Colors.white30, fontSize: 12),
              ),
          ],
        ),
      ),
    );
  }
}
