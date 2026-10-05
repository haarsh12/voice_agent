/// Knowledge document model
class KnowledgeDocument {
  final String id;
  final String title;
  final String? source;
  final String? type;
  final DateTime? lastUpdated;
  final int? chunks;
  final Map<String, dynamic>? metadata;

  KnowledgeDocument({
    required this.id,
    required this.title,
    this.source,
    this.type,
    this.lastUpdated,
    this.chunks,
    this.metadata,
  });

  factory KnowledgeDocument.fromJson(Map<String, dynamic> json) {
    return KnowledgeDocument(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? json['name'] ?? 'Untitled Document',
      source: json['source'] ?? json['url'],
      type: json['type'] ?? json['document_type'],
      lastUpdated: json['last_updated'] != null
          ? DateTime.tryParse(json['last_updated'])
          : (json['updated_at'] != null
              ? DateTime.tryParse(json['updated_at'])
              : null),
      chunks: json['chunks'] ?? json['chunk_count'],
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'source': source,
      'type': type,
      'last_updated': lastUpdated?.toIso8601String(),
      'chunks': chunks,
      'metadata': metadata,
    };
  }
}
