#!/usr/bin/env python3
"""
Authentication Methods Test Script

This script tests all three authentication methods for the API gateway:
1. JWT tokens (for UI access)
2. Admin API key (for administrative access)
3. User API keys (for programmatic access to AI services)

Usage:
    python test_auth_methods.py

Environment variables:
    API_GATEWAY_URL - URL of the API gateway (default: http://localhost:8080)
    API_SECRET_KEY - Admin API key (default: your-api-secret-key-change-me-in-production)
    TEST_USERNAME - Username for testing (default: admin)
    TEST_PASSWORD - Password for testing (default: Password123!)
"""

import os
import json
import requests
from datetime import datetime, timedelta


# Configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-api-secret-key-change-me-in-production")
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Password123!")


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(f"{title}")
    print("=" * 50)


def print_response(response, include_content=True):
    """Pretty print a response"""
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if include_content and response.text:
        try:
            print("Content:")
            print(json.dumps(response.json(), indent=2))
        except:
            print(f"Content: {response.text[:200]}...")


def test_jwt_authentication():
    """Test JWT authentication (used for UI access)"""
    print_section("Testing JWT Authentication (UI Access)")
    
    # Step 1: Login to get a JWT token
    print("\n1. Login to get JWT token")
    login_url = f"{API_GATEWAY_URL}/api/v1/login"
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    response = requests.post(login_url, json=login_data)
    print_response(response)
    
    if response.status_code != 200:
        print("❌ Login failed - cannot continue JWT tests")
        return None
    
    token = response.json().get("token")
    print(f"✅ Successfully obtained JWT token: {token[:20]}...{token[-10:]}")
    print(f"Full token: {token}")
    
    # Step 2: Access a protected endpoint using JWT
    print("\n2. Access protected endpoint using JWT")
    headers = {"Authorization": f"Bearer {token}"}
    protected_url = f"{API_GATEWAY_URL}/api/v1/users"
    response = requests.get(protected_url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Successfully accessed protected endpoint with JWT")
    else:
        print("❌ Failed to access protected endpoint with JWT")
    
    return token


def test_admin_api_key():
    """Test admin API key authentication"""
    print_section("Testing Admin API Key Authentication")
    
    # Access protected endpoint using admin API key
    print("\nAccessing protected endpoint using admin API key")
    headers = {"Authorization": f"Bearer {API_SECRET_KEY}"}
    
    # Try to access users endpoint
    users_url = f"{API_GATEWAY_URL}/api/v1/users"
    response = requests.get(users_url, headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Successfully accessed users endpoint with admin API key")
    else:
        print("❌ Failed to access users endpoint with admin API key")
    
    # Try to access AI endpoint
    ai_url = f"{API_GATEWAY_URL}/api/v1/completions"
    ai_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, AI!"}]
    }
    response = requests.post(ai_url, json=ai_data, headers=headers)
    print_response(response)
    
    if response.status_code < 400:  # Success or redirect
        print("✅ Successfully accessed AI endpoint with admin API key")
    else:
        print("❌ Failed to access AI endpoint with admin API key")


def test_user_api_keys(jwt_token):
    """Test user API key authentication"""
    print_section("Testing User API Keys")
    
    if not jwt_token:
        print("❌ JWT token not available - cannot test API key creation")
        return
    
    jwt_headers = {"Authorization": f"Bearer {jwt_token}"}
    
    # Step 1: Create a new API key
    print("\n1. Creating new API key")
    create_url = f"{API_GATEWAY_URL}/api/v1/keys"
    key_name = f"test-key-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    
    create_data = {
        "name": key_name,
        "expires_at": expires_at
    }
    
    response = requests.post(create_url, json=create_data, headers=jwt_headers)
    print_response(response)
    
    if response.status_code not in (200, 201):
        print("❌ Failed to create API key - cannot continue user API key tests")
        return
    
    api_key = response.json().get("key")
    key_id = response.json().get("id")
    print(f"✅ Successfully created API key: {api_key[:10]}...{api_key[-5:]}")
    
    # Step 2: List API keys
    print("\n2. Listing API keys")
    list_url = f"{API_GATEWAY_URL}/api/v1/keys"
    response = requests.get(list_url, headers=jwt_headers)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Successfully listed API keys")
    else:
        print("❌ Failed to list API keys")
    
    # Step 3: Test API key with AI service
    print("\n3. Testing API key with AI service")
    headers = {"X-API-Key": api_key}
    ai_url = f"{API_GATEWAY_URL}/api/v1/completions"
    ai_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, API key authentication!"}]
    }
    
    response = requests.post(ai_url, json=ai_data, headers=headers)
    print_response(response)
    
    if response.status_code < 400:  # Success or redirect
        print("✅ Successfully accessed AI endpoint with user API key")
    else:
        print("❌ Failed to access AI endpoint with user API key")
    
    # Step 4: Revoke API key
    print("\n4. Revoking API key")
    revoke_url = f"{API_GATEWAY_URL}/api/v1/keys/{key_id}"
    response = requests.put(revoke_url, headers=jwt_headers)
    print_response(response, include_content=False)
    
    if response.status_code < 400:  # Success or redirect
        print("✅ Successfully revoked API key")
    else:
        print("❌ Failed to revoke API key")
    
    # Step 5: Test revoked API key
    print("\n5. Testing revoked API key (should fail)")
    response = requests.post(ai_url, json=ai_data, headers={"X-API-Key": api_key})
    print_response(response)
    
    if response.status_code == 401:
        print("✅ Revoked API key correctly rejected")
    else:
        print("❌ Revoked API key was not rejected properly")


def main():
    """Run all authentication tests"""
    print_section("API AUTHENTICATION METHODS TEST")
    print(f"API Gateway URL: {API_GATEWAY_URL}")
    print(f"Test User: {TEST_USERNAME}")
    
    # Test all authentication methods
    jwt_token = test_jwt_authentication()
    test_admin_api_key()
    test_user_api_keys(jwt_token)
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    main() 