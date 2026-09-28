#!/usr/bin/env python3
"""Test Google Cloud Vertex AI embeddings generation with current credentials."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
_BACKEND_DIRECTORY = Path(__file__).resolve().parent
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent

load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_PROJECT_DIRECTORY / ".env.local", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env.local", override=True)


def test_google_credentials():
    """Test if Google credentials are available."""
    print("\n🔍 Testing Google Cloud Credentials...")
    
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    creds_file = Path(creds_path)
    if not creds_file.exists():
        print(f"   ❌ Credentials file not found: {creds_path}")
        return False
    
    print(f"   ✅ Credentials file found: {creds_path}")
    
    try:
        import json
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
        
        print(f"   ✅ Project ID: {creds_data.get('project_id')}")
        print(f"   ✅ Client Email: {creds_data.get('client_email')}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to parse credentials: {e}")
        return False


def test_vertex_ai_embeddings():
    """Test Vertex AI text embeddings generation."""
    print("\n📊 Testing Vertex AI Text Embeddings...")
    
    try:
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel
        
        # Initialize Vertex AI
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
            return False
        
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        print(f"   ℹ️  Project: {project_id}")
        print(f"   ℹ️  Location: {location}")
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        print("   ✅ Vertex AI initialized")
        
        # Load the embedding model
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        print("   ✅ Embedding model loaded: text-embedding-004")
        
        # Test text samples
        test_texts = [
            "Hello, how are you?",
            "नमस्ते, आप कैसे हैं?",  # Hindi
            "स्वागत आहे",  # Marathi
        ]
        
        print("\n   Testing embedding generation...")
        for i, text in enumerate(test_texts, 1):
            embeddings = model.get_embeddings([text])
            embedding_vector = embeddings[0].values
            print(f"   ✅ Text {i}: '{text[:30]}...' → {len(embedding_vector)} dimensions")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vertex_ai_gecko_embeddings():
    """Test Vertex AI Gecko embeddings (older model)."""
    print("\n📊 Testing Vertex AI Gecko Embeddings (Legacy)...")
    
    try:
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        aiplatform.init(project=project_id, location=location)
        
        # Try gecko model
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        print("   ✅ Gecko model loaded: textembedding-gecko@003")
        
        # Test embedding
        test_text = "This is a test sentence for embedding generation."
        embeddings = model.get_embeddings([test_text])
        embedding_vector = embeddings[0].values
        print(f"   ✅ Generated embedding: {len(embedding_vector)} dimensions")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Gecko model not available: {e}")
        return False


def test_generative_ai_embeddings():
    """Test using Google Generative AI SDK for embeddings."""
    print("\n📊 Testing Google Generative AI Embeddings...")
    
    try:
        import google.generativeai as genai
        
        # Try using GEMINI_API_KEY first
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            print("   ℹ️  Using GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            
            # Test embedding with genai
            result = genai.embed_content(
                model="models/text-embedding-004",
                content="Hello, this is a test for embeddings",
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            print(f"   ✅ Generated embedding via Generative AI: {len(embedding)} dimensions")
            print(f"   ℹ️  Sample values: {embedding[:5]}")
            
            return True
        else:
            print("   ⚠️  GEMINI_API_KEY not set, skipping this test")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_enabled_apis():
    """Check which APIs are enabled in the project."""
    print("\n🔍 Checking Enabled APIs...")
    
    try:
        from google.cloud import service_usage_v1
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id')
        
        client = service_usage_v1.ServiceUsageClient()
        parent = f"projects/{project_id}"
        
        # Check specific APIs
        apis_to_check = [
            "aiplatform.googleapis.com",  # Vertex AI
            "generativelanguage.googleapis.com",  # Generative AI
            "speech.googleapis.com",  # Speech-to-Text
            "texttospeech.googleapis.com",  # Text-to-Speech
        ]
        
        print(f"   Project: {project_id}")
        for api in apis_to_check:
            try:
                service_name = f"projects/{project_id}/services/{api}"
                service = client.get_service(name=service_name)
                status = "✅ ENABLED" if service.state == service_usage_v1.State.ENABLED else "❌ DISABLED"
                print(f"   {status}: {api}")
            except Exception:
                print(f"   ❓ UNKNOWN: {api}")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not check API status: {e}")
        return False


def main():
    """Run all embedding tests."""
    print("=" * 70)
    print("GOOGLE CLOUD EMBEDDINGS TEST")
    print("=" * 70)
    
    results = {
        "credentials": test_google_credentials(),
        "enabled_apis": test_enabled_apis(),
        "vertex_embeddings": test_vertex_ai_embeddings(),
        "gecko_embeddings": test_vertex_ai_gecko_embeddings(),
        "genai_embeddings": test_generative_ai_embeddings(),
    }
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Google Credentials:      {'✅ PASS' if results['credentials'] else '❌ FAIL'}")
    print(f"API Status Check:        {'✅ PASS' if results['enabled_apis'] else '⚠️  SKIP'}")
    print(f"Vertex AI Embeddings:    {'✅ PASS' if results['vertex_embeddings'] else '❌ FAIL'}")
    print(f"Gecko Embeddings:        {'✅ PASS' if results['gecko_embeddings'] else '⚠️  SKIP'}")
    print(f"GenAI SDK Embeddings:    {'✅ PASS' if results['genai_embeddings'] else '⚠️  SKIP'}")
    print("=" * 70)
    
    if results['vertex_embeddings'] or results['genai_embeddings']:
        print("\n✅ EMBEDDINGS GENERATION WORKING!")
        print("\nAvailable Methods:")
        if results['vertex_embeddings']:
            print("  • Vertex AI API (text-embedding-004)")
            print("    - Best for production")
            print("    - 768 dimensions")
            print("    - Multilingual support")
        if results['genai_embeddings']:
            print("  • Generative AI SDK (via GEMINI_API_KEY)")
            print("    - Simple API")
            print("    - Good for development")
        
        print("\nSetup Instructions:")
        print("  1. Ensure Vertex AI API is enabled:")
        print("     https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
        print("  2. Use the service account credentials you already have")
        print("  3. Location: us-central1 (or your preferred region)")
        
        return 0
    else:
        print("\n❌ EMBEDDINGS NOT AVAILABLE")
        print("\nTo enable embeddings:")
        print("  1. Enable Vertex AI API in Google Cloud Console:")
        print("     https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
        print("  2. Grant your service account 'Vertex AI User' role")
        print("  3. Install required packages:")
        print("     pip install google-cloud-aiplatform")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
