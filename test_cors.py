"""Quick CORS diagnostic script to test API endpoints."""

import requests

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method: str, endpoint: str):
    """Test a single endpoint with OPTIONS and actual request."""
    url = f"{BASE_URL}{endpoint}"
    origin = "http://localhost:5173"
    
    print(f"\n{'='*60}")
    print(f"Testing {method} {endpoint}")
    print(f"{'='*60}")
    
    # Test OPTIONS (preflight)
    try:
        options_response = requests.options(
            url,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "content-type"
            }
        )
        print(f"OPTIONS: {options_response.status_code}")
        print(f"CORS Headers: {dict(options_response.headers)}")
    except Exception as e:
        print(f"OPTIONS failed: {e}")
    
    # Test actual request
    try:
        if method == "GET":
            response = requests.get(url, headers={"Origin": origin})
        elif method == "POST":
            response = requests.post(url, json={}, headers={"Origin": origin})
        
        print(f"{method}: {response.status_code}")
        if response.status_code < 400:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"{method} failed: {e}")

if __name__ == "__main__":
    print("CORS Diagnostic Test")
    print("="*60)
    
    # Test key endpoints
    test_endpoint("GET", "/api/health")
    test_endpoint("POST", "/api/guest-sessions")
    test_endpoint("POST", "/api/token")
    
    print("\n" + "="*60)
    print("Test Complete!")
