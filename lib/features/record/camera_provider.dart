import 'package:camera/camera.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final cameraListProvider = FutureProvider<List<CameraDescription>>((ref) async {
  return await availableCameras();
});

final cameraControllerProvider = StateNotifierProvider<CameraControllerNotifier, AsyncValue<CameraController?>>((ref) {
  return CameraControllerNotifier();
});

class CameraControllerNotifier extends StateNotifier<AsyncValue<CameraController?>> {
  CameraControllerNotifier() : super(const AsyncValue.data(null));

  Future<void> initCamera(CameraDescription description) async {
    state = const AsyncValue.loading();
    try {
      final controller = CameraController(
        description,
        ResolutionPreset.high,
        enableAudio: true,
      );
      await controller.initialize();
      state = AsyncValue.data(controller);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<void> disposeCamera() async {
    final controller = state.asData?.value;
    if (controller != null) {
      await controller.dispose();
      state = const AsyncValue.data(null);
    }
  }
}
