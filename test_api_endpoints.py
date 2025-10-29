#!/usr/bin/env python3
"""
Test script to verify API endpoints for Birds-Eye Dashboard
"""

import requests
import json
import sys
from typing import Dict, Any

def test_api_endpoint(url: str, expected_status: int = 200) -> Dict[str, Any]:
    """Test an API endpoint and return the result"""
    try:
        response = requests.get(url, timeout=10)
        return {
            "url": url,
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "data": response.json() if response.status_code == 200 else None,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "status_code": None,
            "success": False,
            "data": None,
            "error": str(e)
        }

def main():
    """Test all API endpoints for the Birds-Eye Dashboard"""
    
    base_url = "http://localhost:8000"
    
    # API endpoints that the Birds-Eye Dashboard expects
    endpoints = [
        "/api/sources/overview",
        "/api/doublets/flow", 
        "/api/timeline/evolution",
        "/api/redaction/patterns",
        "/doublets/flow",  # Existing endpoint
        "/timeline/documentary-lens?query=creation&limit=200",  # Existing endpoint
        "/geography/pov?limit=200"  # Existing endpoint
    ]
    
    print("Testing API Endpoints for Birds-Eye Dashboard")
    print("=" * 60)
    
    results = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTesting: {endpoint}")
        
        result = test_api_endpoint(url)
        results.append(result)
        
        if result["success"]:
            print(f"SUCCESS - Status: {result['status_code']}")
            if result["data"]:
                print(f"   Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'Array data'}")
        else:
            print(f"FAILED - Status: {result['status_code']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Successful: {successful}/{total}")
    print(f"Failed: {total - successful}/{total}")
    
    if successful == total:
        print("\nALL TESTS PASSED! Birds-Eye Dashboard should work correctly.")
    else:
        print("\nSome endpoints failed. Check the errors above.")
        print("The dashboard may still work with available endpoints.")
    
    # Test frontend connection
    print(f"\nFrontend should be available at: http://localhost:5173")
    print(f"API documentation at: {base_url}/docs")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
