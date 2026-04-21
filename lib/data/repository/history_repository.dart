import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../models/api_response.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final historyRepositoryProvider = Provider<HistoryRepository>((ref) {
  return HistoryRepository();
});

class HistoryRepository {
  static const String _fileName = 'history.json';

  Future<File> _getHistoryFile() async {
    final directory = await getApplicationDocumentsDirectory();
    return File('${directory.path}/$_fileName');
  }

  Future<List<VideoUploadResponse>> getHistory() async {
    try {
      final file = await _getHistoryFile();
      if (!await file.exists()) {
        return [];
      }
      final contents = await file.readAsString();
      final List<dynamic> jsonList = json.decode(contents);
      return jsonList.map((item) => VideoUploadResponse.fromJson(item)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<void> saveResult(VideoUploadResponse result) async {
    final history = await getHistory();
    history.insert(0, result); // Add to beginning
    
    final file = await _getHistoryFile();
    final jsonString = json.encode(history.map((record) => record.toJson()).toList());
    await file.writeAsString(jsonString);
  }
}
