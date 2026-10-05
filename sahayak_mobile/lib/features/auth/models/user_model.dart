/// User model representing authenticated user data
class UserModel {
  final String id;
  final String phoneNumber;
  final String? name;
  final String? email;
  final String? state;
  final String? district;
  final String? villageOrTown;
  final String? address;
  final String? pincode;
  final String? casteCategory;
  final String? userType;
  final String? cooperativeRole;
  final bool needsOnboarding;
  final DateTime createdAt;
  final DateTime? updatedAt;

  UserModel({
    required this.id,
    required this.phoneNumber,
    this.name,
    this.email,
    this.state,
    this.district,
    this.villageOrTown,
    this.address,
    this.pincode,
    this.casteCategory,
    this.userType,
    this.cooperativeRole,
    this.needsOnboarding = false,
    required this.createdAt,
    this.updatedAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      phoneNumber: json['phone_number'] ?? json['phone'] ?? '',
      name: json['full_name'] ?? json['name'],
      email: json['email'],
      state: json['state'],
      district: json['district'],
      villageOrTown: json['village_or_town'],
      address: json['address'],
      pincode: json['pincode'],
      casteCategory: json['caste_category'],
      userType: json['user_type'],
      cooperativeRole: json['cooperative_role'],
      needsOnboarding: json['needs_onboarding'] == true,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'phone_number': phoneNumber,
      'full_name': name,
      'email': email,
      'state': state,
      'district': district,
      'village_or_town': villageOrTown,
      'address': address,
      'pincode': pincode,
      'caste_category': casteCategory,
      'user_type': userType,
      'cooperative_role': cooperativeRole,
      'needs_onboarding': needsOnboarding,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  UserModel copyWith({
    String? id,
    String? phoneNumber,
    String? name,
    String? email,
    String? state,
    String? district,
    String? villageOrTown,
    String? address,
    String? pincode,
    String? casteCategory,
    String? userType,
    String? cooperativeRole,
    bool? needsOnboarding,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      name: name ?? this.name,
      email: email ?? this.email,
      state: state ?? this.state,
      district: district ?? this.district,
      villageOrTown: villageOrTown ?? this.villageOrTown,
      address: address ?? this.address,
      pincode: pincode ?? this.pincode,
      casteCategory: casteCategory ?? this.casteCategory,
      userType: userType ?? this.userType,
      cooperativeRole: cooperativeRole ?? this.cooperativeRole,
      needsOnboarding: needsOnboarding ?? this.needsOnboarding,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  bool get isProfileComplete {
    return name != null &&
        name!.isNotEmpty &&
        state != null &&
        state!.isNotEmpty &&
        district != null &&
        district!.isNotEmpty &&
        villageOrTown != null &&
        villageOrTown!.isNotEmpty &&
        address != null &&
        address!.isNotEmpty &&
        pincode != null &&
        pincode!.isNotEmpty &&
        casteCategory != null &&
        casteCategory!.isNotEmpty &&
        userType != null &&
        userType!.isNotEmpty;
  }
}
