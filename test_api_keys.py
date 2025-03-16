#!/usr/bin/env python3
"""
Simple script to test the API key functionality in the user service.
This script will:
1. Create a new API key
2. List existing API keys
3. Test using the API key with the AI service
4. Revoke the API key
5. Verify the revoked key no longer works

Usage:
    # Make the script executable
    chmod +x test_api_keys.py
    
    # Run with default settings (localhost)
    ./test_api_keys.py
    
    # Or specify custom service URLs
    ./test_api_keys.py --user-url http://your-user-service:8081 --ai-url http://your-ai-service:8082
    
    # Run with specific credentials
    ./test_api_keys.py --username admin --password admin
"""

import requests
import json
import argparse
import time
from datetime import datetime, timedelta


# Default service URLs
USER_SERVICE_URL = "http://localhost:8081"
AI_SERVICE_URL = "http://localhost:8082/api/v1"


def login(username, password, base_url=USER_SERVICE_URL):
    """Login to user service and get auth token"""
    url = f"{base_url}/api/v1/login"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["token"]
    except requests.exceptions.RequestException as e:
        print(f"Error logging in: {e}")
        if response.text:
            print(f"Response: {response.text}")
        return None


def create_api_key(token, name, base_url=USER_SERVICE_URL):
    """Create a new API key"""
    url = f"{base_url}/api/v1/keys"
    
    # Set expiration date to 30 days from now with proper UTC format
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    payload = {
        "name": name,
        "expires_at": expires_at
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating API key: {e}")
        if response.text:
            print(f"Response: {response.text}")
        return None


def list_api_keys(token, base_url=USER_SERVICE_URL):
    """List all API keys for the authenticated user"""
    url = f"{base_url}/api/v1/keys"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing API keys: {e}")
        if response.text:
            print(f"Response: {response.text}")
        return None


def revoke_api_key(token, key_id, base_url=USER_SERVICE_URL):
    """Revoke an API key"""
    url = f"{base_url}/api/v1/keys/{key_id}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.put(url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error revoking API key: {e}")
        if response.text:
            print(f"Response: {response.text}")
        return False


def test_api_key_with_ai_service(api_key, base_url=AI_SERVICE_URL):
    """Test using the API key with the AI service"""
    url = f"{base_url}/embeddings"
    
    payload = {
        "input": "This is a test for API key authentication",
        "model": "text-embedding-3-small"
    }
    
    headers = {
        "X-API-Key": api_key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return True, response.status_code
    except requests.exceptions.RequestException as e:
        return False, getattr(e.response, 'status_code', None)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test API key functionality")
    parser.add_argument("--user-url", default=USER_SERVICE_URL, help="User service URL")
    parser.add_argument("--ai-url", default=AI_SERVICE_URL, help="AI service URL")
    parser.add_argument("--username", default="admin", help="Username for login")
    parser.add_argument("--password", default="Password123!", help="Password for login")
    args = parser.parse_args()
    
    # Get URLs from arguments
    user_url = args.user_url
    ai_url = args.ai_url
    
    print("=== Testing API Key Functionality ===\n")
    
    # Step 1: Login
    print("Step 1: Logging in...")
    token = login(args.username, args.password, user_url)
    if not token:
        print("❌ Login failed. Exiting.")
        return
    print("✅ Login successful\n")
    
    # Step 2: Create API key
    print("Step 2: Creating API key...")
    api_key_response = create_api_key(token, "Test API Key", user_url)
    if not api_key_response:
        print("❌ Failed to create API key. Exiting.")
        return
    
    api_key = api_key_response["key"]
    key_id = api_key_response["id"]
    print(f"✅ API key created successfully: {api_key[:10]}...{api_key[-5:]}")
    print(f"   Key ID: {key_id}")
    print(f"   Name: {api_key_response['name']}")
    print(f"   Expires: {api_key_response['expires_at']}\n")
    
    # Step 3: List API keys
    print("Step 3: Listing API keys...")
    keys_response = list_api_keys(token, user_url)
    if not keys_response:
        print("❌ Failed to list API keys.")
    else:
        print(f"✅ Found {keys_response['total']} API keys")
        for key in keys_response["api_keys"]:
            print(f"   - {key['name']} (ID: {key['id']}, Active: {key['is_active']})")
    print()
    
    # Step 4: Test API key with AI service
    print("Step 4: Testing API key with AI service...")
    success, status_code = test_api_key_with_ai_service(api_key, ai_url)
    if success:
        print(f"✅ Successfully used API key with AI service (Status: {status_code})\n")
    else:
        print(f"❌ Failed to use API key with AI service (Status: {status_code})\n")
    
    # Step 5: Revoke API key
    print("Step 5: Revoking API key...")
    if revoke_api_key(token, key_id, user_url):
        print(f"✅ API key {key_id} revoked successfully\n")
    else:
        print(f"❌ Failed to revoke API key {key_id}\n")
    
    # Step 6: Verify revoked key doesn't work
    print("Step 6: Verifying revoked API key doesn't work...")
    success, status_code = test_api_key_with_ai_service(api_key, ai_url)
    if not success and status_code == 401:
        print(f"✅ Revoked API key correctly rejected (Status: {status_code})\n")
    else:
        print(f"❌ Revoked API key was not properly rejected (Status: {status_code})\n")
    
    print("=== API Key Tests Completed ===")


if __name__ == "__main__":
    main() 