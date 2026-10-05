class GrievanceModel {
  final String id;
  final String title;
  final String description;
  final String status;
  final String? category;
  final DateTime createdAt;
  final DateTime? updatedAt;

  GrievanceModel({
    required this.id,
    required this.title,
    required this.description,
    required this.status,
    this.category,
    required this.createdAt,
    this.updatedAt,
  });

  factory GrievanceModel.fromJson(Map<String, dynamic> json) {
    return GrievanceModel(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Untitled',
      description: json['description'] ?? '',
      status: json['status'] ?? 'pending',
      category: json['category'],
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
      'title': title,
      'description': description,
      'status': status,
      'category': category,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }
}
