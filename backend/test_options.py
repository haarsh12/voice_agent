"""Quick test to see what's happening with OPTIONS requests."""
import requests

base_url = "http://127.0.0.1:8000"

print("Testing OPTIONS request to /api/health...")
try:
    response = requests.options(f"{base_url}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting GET request to /api/health...")
try:
    response = requests.get(f"{base_url}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
