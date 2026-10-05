import 'package:flutter/material.dart';
import '../../auth/providers/auth_provider.dart';

class ProfileProvider extends ChangeNotifier {
  final AuthProvider _authProvider;

  ProfileProvider({AuthProvider? authProvider})
      : _authProvider = authProvider ?? AuthProvider();

  Future<bool> updateProfile(Map<String, dynamic> updates) async {
    return await _authProvider.updateProfile(updates);
  }

  Future<void> logout() async {
    await _authProvider.logout();
  }
}
