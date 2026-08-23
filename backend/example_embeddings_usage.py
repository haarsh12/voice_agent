#!/usr/bin/env python3
"""Example: How to use Google Cloud embeddings in your application."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
_BACKEND_DIRECTORY = Path(__file__).resolve().parent
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent

load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Vertex AI.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each vector is 768 dimensions)
    """
    from google.cloud import aiplatform
    from vertexai.language_models import TextEmbeddingModel
    import json
    
    # Get credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
    
    project_id = creds_data.get('project_id')
    location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
    
    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=location)
    
    # Load embedding model
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    # Generate embeddings (can batch up to 250 texts)
    embeddings = model.get_embeddings(texts)
    
    # Extract vectors
    return [embedding.values for embedding in embeddings]


def calculate_similarity(embedding1: list[float], embedding2: list[float]) -> float:
    """Calculate cosine similarity between two embedding vectors.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between -1 and 1 (higher is more similar)
    """
    import numpy as np
    
    # Convert to numpy arrays
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    return dot_product / (norm1 * norm2)


def example_semantic_search():
    """Example: Semantic search using embeddings."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Semantic Search with Embeddings")
    print("=" * 70)
    
    # Sample documents (in English, Hindi, and Marathi)
    documents = [
        "The weather is sunny today",
        "आज मौसम धूप वाला है",  # Hindi: The weather is sunny today
        "आज हवामान सनी आहे",  # Marathi: The weather is sunny today
        "I love eating pizza",
        "मुझे पिज़्ज़ा खाना पसंद है",  # Hindi: I love eating pizza
        "Machine learning is fascinating",
        "मशीन लर्निंग आकर्षक आहे",  # Marathi: Machine learning is fascinating
    ]
    
    # Query
    query = "What's the weather like?"
    
    print(f"\n📝 Documents: {len(documents)} items")
    for i, doc in enumerate(documents, 1):
        print(f"   {i}. {doc}")
    
    print(f"\n🔍 Query: '{query}'")
    print("\n⏳ Generating embeddings...")
    
    # Generate embeddings
    all_texts = documents + [query]
    embeddings = generate_embeddings(all_texts)
    
    doc_embeddings = embeddings[:-1]
    query_embedding = embeddings[-1]
    
    print("   ✅ Embeddings generated")
    print(f"   ℹ️  Embedding dimensions: {len(query_embedding)}")
    
    # Calculate similarities
    print("\n📊 Similarity Scores:")
    similarities = []
    for i, doc_emb in enumerate(doc_embeddings):
        similarity = calculate_similarity(query_embedding, doc_emb)
        similarities.append((i, similarity))
        print(f"   {i+1}. {documents[i][:50]:50} → {similarity:.4f}")
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🏆 Top 3 Most Relevant Documents:")
    for rank, (idx, score) in enumerate(similarities[:3], 1):
        print(f"   {rank}. [{score:.4f}] {documents[idx]}")


def example_multilingual_clustering():
    """Example: Cluster similar texts across languages."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Multilingual Text Clustering")
    print("=" * 70)
    
    # Mixed language texts about similar topics
    texts = [
        # Group 1: Weather
        "It's raining heavily",
        "बारिश बहुत तेज हो रही है",  # Hindi
        "जोरदार पाऊस पडत आहे",  # Marathi
        
        # Group 2: Food
        "I'm hungry, let's eat",
        "मुझे भूख लगी है, चलो खाते हैं",  # Hindi
        "मला भूक लागली आहे, चला जेवूया",  # Marathi
        
        # Group 3: Technology
        "Artificial intelligence is amazing",
        "कृत्रिम बुद्धिमत्ता अद्भुत है",  # Hindi
        "कृत्रिम बुद्धिमत्ता आश्चर्यकारक आहे",  # Marathi
    ]
    
    print(f"\n📝 Texts to cluster: {len(texts)} items")
    
    print("\n⏳ Generating embeddings...")
    embeddings = generate_embeddings(texts)
    print("   ✅ Embeddings generated")
    
    # Calculate similarity matrix
    print("\n📊 Cross-Language Similarity Matrix:")
    print("   " + " ".join([f"{i+1:5}" for i in range(len(texts))]))
    
    for i, emb1 in enumerate(embeddings):
        row = f"{i+1}. "
        for j, emb2 in enumerate(embeddings):
            similarity = calculate_similarity(emb1, emb2)
            row += f"{similarity:5.2f} "
        print(row)
    
    print("\n💡 Notice: Texts with similar meaning across different languages")
    print("    have high similarity scores (close to 1.0)")


def example_rag_application():
    """Example: Simple RAG (Retrieval Augmented Generation) setup."""
    print("\n" + "=" * 70)
    print("EXAMPLE: RAG Application Structure")
    print("=" * 70)
    
    print("\n📚 RAG Workflow:")
    print("   1. Chunk documents into smaller pieces")
    print("   2. Generate embeddings for each chunk")
    print("   3. Store embeddings in a vector database")
    print("   4. When user asks a question:")
    print("      a. Generate embedding for the question")
    print("      b. Find most similar document chunks")
    print("      c. Pass relevant chunks to Gemini for answer generation")
    
    print("\n🔧 Code Structure:")
    print("""
    # Step 1: Index documents
    documents = load_your_documents()
    chunks = split_into_chunks(documents)
    embeddings = generate_embeddings(chunks)
    vector_db.store(chunks, embeddings)
    
    # Step 2: Answer user query
    user_question = "What is the refund policy?"
    question_embedding = generate_embeddings([user_question])[0]
    relevant_chunks = vector_db.search(question_embedding, top_k=5)
    
    # Step 3: Use Gemini to generate answer
    context = "\\n".join(relevant_chunks)
    prompt = f"Context: {context}\\n\\nQuestion: {user_question}\\n\\nAnswer:"
    answer = gemini_model.generate(prompt)
    """)
    
    print("\n💾 Recommended Vector Databases:")
    print("   • Pinecone - Fully managed, easy to use")
    print("   • Weaviate - Open source, feature-rich")
    print("   • Chroma - Lightweight, good for development")
    print("   • FAISS - Local, high performance")


def main():
    """Run example demonstrations."""
    print("=" * 70)
    print("GOOGLE CLOUD EMBEDDINGS - USAGE EXAMPLES")
    print("=" * 70)
    
    try:
        # Example 1: Semantic Search
        example_semantic_search()
        
        # Example 2: Multilingual Clustering
        example_multilingual_clustering()
        
        # Example 3: RAG Application Structure
        example_rag_application()
        
        print("\n" + "=" * 70)
        print("✅ ALL EXAMPLES COMPLETED!")
        print("=" * 70)
        print("\n💡 Key Takeaways:")
        print("   • text-embedding-004 supports 100+ languages including Hindi & Marathi")
        print("   • Embeddings are 768 dimensions")
        print("   • Can batch up to 250 texts per API call")
        print("   • Perfect for RAG, semantic search, and clustering")
        print("   • Works with same credentials as your STT/TTS/Gemini")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
        sys.exit(130)
