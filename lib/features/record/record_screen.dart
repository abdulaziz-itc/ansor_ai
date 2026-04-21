import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'camera_provider.dart';
import '../../core/theme/app_theme.dart';
import '../processing/processing_screen.dart';
import '../history/history_screen.dart';

class RecordScreen extends ConsumerStatefulWidget {
  const RecordScreen({super.key});

  @override
  ConsumerState<RecordScreen> createState() => _RecordScreenState();
}

class _RecordScreenState extends ConsumerState<RecordScreen> {
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _initFirstCamera();
  }

  Future<void> _initFirstCamera() async {
    final cameras = await ref.read(cameraListProvider.future);
    if (cameras.isNotEmpty) {
      await ref.read(cameraControllerProvider.notifier).initCamera(cameras.first);
    }
  }

  @override
  Widget build(BuildContext context) {
    final controllerAsync = ref.watch(cameraControllerProvider);

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera Preview
          controllerAsync.when(
            data: (controller) => controller != null && controller.value.isInitialized
                ? CameraPreview(controller)
                : const Center(child: CircularProgressIndicator()),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (err, stack) => Center(child: Text('Error: $err')),
          ),

          // Top Header Overlay
          Positioned(
            top: 60,
            left: 20,
            right: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceColor.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.auto_awesome, color: AppTheme.accentColor, size: 18),
                      const SizedBox(width: 8),
                      Text(
                        'Sign2Voice AI',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (context) => const HistoryScreen()),
                    );
                  },
                  icon: const Icon(Icons.history, color: Colors.white),
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.surfaceColor.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),

          // Bottom Controls Overlay
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Column(
              children: [
                if (_isRecording)
                  Container(
                    margin: const EdgeInsets.only(bottom: 20),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.8),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.circle, color: Colors.white, size: 12),
                        SizedBox(width: 8),
                        Text('REC 00:05', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    IconButton(
                      onPressed: _toggleFlash,
                      icon: Icon(
                        (ref.watch(cameraControllerProvider).asData?.value?.value.flashMode == FlashMode.torch)
                            ? Icons.flash_on
                            : Icons.flash_off,
                        color: Colors.white,
                      ),
                      iconSize: 28,
                    ),
                    GestureDetector(
                      onTap: _toggleRecording,
                      child: Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 4),
                        ),
                        child: Center(
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            width: _isRecording ? 40 : 60,
                            height: _isRecording ? 40 : 60,
                            decoration: BoxDecoration(
                              color: _isRecording ? Colors.red : AppTheme.primaryColor,
                              borderRadius: BorderRadius.circular(_isRecording ? 8 : 30),
                              boxShadow: [
                                BoxShadow(
                                  color: (_isRecording ? Colors.red : AppTheme.primaryColor).withOpacity(0.5),
                                  blurRadius: 20,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: _switchCamera,
                      icon: const Icon(Icons.flip_camera_ios, color: Colors.white),
                      iconSize: 28,
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text(
                  _isRecording ? 'Tap to stop' : 'Tap to record sign language',
                  style: const TextStyle(color: Colors.white70, letterSpacing: 1.2),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleRecording() async {
    final controller = ref.read(cameraControllerProvider).asData?.value;
    if (controller == null || !controller.value.isInitialized) return;

    if (_isRecording) {
      try {
        final file = await controller.stopVideoRecording();
        setState(() => _isRecording = false);
        
        // Navigate to Processing Screen with the video file
        if (mounted) {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => ProcessingScreen(videoPath: file.path),
            ),
          );
        }
      } catch (e) {
        debugPrint('Error stopping recording: $e');
      }
    } else {
      try {
        await controller.startVideoRecording();
        setState(() => _isRecording = true);
      } catch (e) {
        debugPrint('Error starting recording: $e');
      }
    }
  }

  Future<void> _switchCamera() async {
    final cameras = await ref.read(cameraListProvider.future);
    final currentController = ref.read(cameraControllerProvider).asData?.value;
    if (cameras.length < 2 || currentController == null) return;

    final currentDescription = currentController.description;
    final newDescription = cameras.firstWhere((c) => c != currentDescription);

    await ref.read(cameraControllerProvider.notifier).disposeCamera();
    await ref.read(cameraControllerProvider.notifier).initCamera(newDescription);
  }

  Future<void> _toggleFlash() async {
    final controller = ref.read(cameraControllerProvider).asData?.value;
    if (controller == null) return;

    final currentMode = controller.value.flashMode;
    final nextMode = currentMode == FlashMode.off ? FlashMode.torch : FlashMode.off;
    
    await controller.setFlashMode(nextMode);
    setState(() {}); // To update icon if needed
  }
}

