/// Government scheme model - maps to /api/schemes response
class SchemeModel {
  final String id;
  final String title;       // official_name
  final String? acronym;    // short_name
  final String? description;
  final String? category;
  final String? type;       // scheme_type
  final String? geography;  // geographic_scope
  final List<String>? beneficiaries; // beneficiary_categories
  final String? status;
  final Map<String, dynamic>? data;  // nested data object with full details
  final List<Map<String, dynamic>>? sources; // source URLs
  final Map<String, dynamic>? metadata;

  SchemeModel({
    required this.id,
    required this.title,
    this.acronym,
    this.description,
    this.category,
    this.type,
    this.geography,
    this.beneficiaries,
    this.status,
    this.data,
    this.sources,
    this.metadata,
  });

  factory SchemeModel.fromJson(Map<String, dynamic> json) {
    List<String> extractList(dynamic val) {
      if (val is List) return val.map((e) => e.toString()).toList();
      if (val is String && val.isNotEmpty) return [val];
      return [];
    }

    // Try to get official URL from sources list
    String? officialUrl;
    final sourcesList = json['sources'];
    if (sourcesList is List && sourcesList.isNotEmpty) {
      final firstSource = sourcesList.first;
      if (firstSource is Map) {
        officialUrl = firstSource['url']?.toString();
      }
    }

    // Build metadata combining top-level + data object
    final Map<String, dynamic> meta = Map<String, dynamic>.from(json);
    if (json['data'] is Map) {
      meta.addAll(Map<String, dynamic>.from(json['data'] as Map));
    }
    if (officialUrl != null) {
      meta['official_url'] = officialUrl;
    }

    return SchemeModel(
      id: json['id']?.toString() ?? '',
      // API returns official_name as the primary name field
      title: json['official_name']?.toString() ??
          json['title']?.toString() ??
          json['name']?.toString() ??
          json['scheme_name']?.toString() ??
          'Unknown Scheme',
      acronym: json['short_name']?.toString(),
      description: json['description']?.toString() ??
          (json['data'] is Map ? json['data']['description']?.toString() : null),
      category: json['category']?.toString() ?? json['sector']?.toString(),
      type: json['scheme_type']?.toString() ?? json['type']?.toString(),
      geography: json['geographic_scope']?.toString() ?? json['coverage']?.toString(),
      beneficiaries: json['beneficiary_categories'] != null
          ? extractList(json['beneficiary_categories'])
          : (json['relevant_user_types'] != null
              ? extractList(json['relevant_user_types'])
              : null),
      status: json['status']?.toString(),
      data: json['data'] is Map ? Map<String, dynamic>.from(json['data'] as Map) : null,
      sources: sourcesList is List
          ? sourcesList
              .whereType<Map>()
              .map((s) => Map<String, dynamic>.from(s))
              .toList()
          : null,
      metadata: meta,
    );
  }

  Map<String, dynamic> toJson() => metadata ?? {};
}
