class ServiceModel {
  final String id;
  final String name;
  final String? description;
  final String? category;
  final String? icon;

  ServiceModel({
    required this.id,
    required this.name,
    this.description,
    this.category,
    this.icon,
  });

  factory ServiceModel.fromJson(Map<String, dynamic> json) {
    return ServiceModel(
      id: json['id']?.toString() ?? '',
      name: json['name'] ?? 'Unknown Service',
      description: json['description'],
      category: json['category'],
      icon: json['icon'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'category': category,
      'icon': icon,
    };
  }
}
