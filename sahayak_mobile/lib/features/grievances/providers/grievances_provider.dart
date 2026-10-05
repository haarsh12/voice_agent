import 'package:flutter/material.dart';
import '../../../core/services/api_client.dart';
import '../models/grievance_model.dart';

class GrievancesProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();

  List<GrievanceModel> _grievances = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<GrievanceModel> get grievances => _grievances;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchGrievances() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _api.get('/api/grievances');
      final List<dynamic> data = response['grievances'] ?? response ?? [];
      
      _grievances = data.map((e) => GrievanceModel.fromJson(e)).toList();

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load grievances: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createGrievance(Map<String, dynamic> data) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _api.post('/api/grievances', data);
      await fetchGrievances(); // Refresh list

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to create grievance: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  GrievanceModel? getGrievanceById(String id) {
    try {
      return _grievances.firstWhere((g) => g.id == id);
    } catch (e) {
      return null;
    }
  }
}
