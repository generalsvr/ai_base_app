#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
import base64
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class ServiceTester:
    def __init__(self, api_gateway_url="http://localhost:8080", analytics_url="http://localhost:8083"):
        self.api_gateway_url = api_gateway_url
        self.analytics_url = analytics_url
        self.token = None
        self.user_id = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        self.created_username = f"testuser_{int(time.time())}"
        self.created_password = "Password123!"
        # Sample image URL for image processing tests
        self.sample_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2023_06_08_Raccoon1.jpg/1599px-2023_06_08_Raccoon1.jpg"

    def print_header(self, message):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*50)
        print(f" {message}")
        print("="*50 + f"{Style.RESET_ALL}\n")

    def print_test_result(self, test_name, success, error=None):
        """Print test result with formatting"""
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print(f"{Fore.GREEN}✓ {test_name}: PASSED{Style.RESET_ALL}")
        else:
            self.test_results["failed"] += 1
            print(f"{Fore.RED}✗ {test_name}: FAILED{Style.RESET_ALL}")
            if error:
                print(f"  Error: {error}")

    def run_all_tests(self):
        """Run all test cases in sequence"""
        self.print_header("STARTING API GATEWAY TESTS")
        
        # Test Gateway Health
        self.test_gateway_health()
        
        # Test User Service via Gateway
        self.test_create_user()
        self.test_login()
        self.test_get_user()
        self.test_get_users_list()
        self.test_update_user()
        self.test_verify_token()
        
        # Test AI Service via Gateway
        print(f"\n{Fore.CYAN}Testing AI service with updated API key{Style.RESET_ALL}")
        self.test_ai_completion()
        self.test_ai_completion_custom_model()
        self.test_ai_embedding()
        self.test_ai_embedding_custom_model()
        
        # Test Image Processing
        print(f"\n{Fore.CYAN}Testing Image Processing{Style.RESET_ALL}")
        self.test_image_from_url()
        
        # Cleanup - logout first, then delete user
        self.test_logout()
        self.test_delete_user()
        
        # Test Analytics Service
        self.print_header("TESTING ANALYTICS SERVICE")
        self.test_analytics_health()
        self.test_log_user_activity()
        self.test_log_ai_call()
        self.test_get_user_stats()
        self.test_get_ai_stats()
        self.test_get_total_users()
        
        # Print summary
        self.print_summary()

    def test_gateway_health(self):
        """Test if API gateway is up and running"""
        try:
            response = requests.get(f"{self.api_gateway_url}/health", timeout=5)
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            self.print_test_result("API Gateway Health Check", success)
        except Exception as e:
            self.print_test_result("API Gateway Health Check", False, str(e))

    def test_create_user(self):
        """Test user creation"""
        try:
            new_user = {
                "username": self.created_username,
                "email": f"test_{int(time.time())}@example.com",
                "password": self.created_password,
                "firstName": "Test",
                "lastName": "User"
            }
            
            print(f"  Sending request to: {self.api_gateway_url}/api/v1/users")
            print(f"  Request payload: {json.dumps(new_user)}")
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/users",
                json=new_user
            )
            
            success = response.status_code == 201
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            
            if success:
                data = response.json()
                self.user_id = data.get("id")
                print(f"  Created user with ID: {self.user_id}")
                print(f"  Username: {self.created_username}")
            
            self.print_test_result("Create User", success)
        except Exception as e:
            self.print_test_result("Create User", False, str(e))

    def test_login(self):
        """Test user login"""
        try:
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/login",
                json={
                    "username": self.created_username,
                    "password": self.created_password
                }
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.token = data.get("token")
                print(f"  Received token: {self.token[:10]}..." if self.token else "  No token received")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("User Login", success)
        except Exception as e:
            self.print_test_result("User Login", False, str(e))

    def test_get_user(self):
        """Test getting user by ID"""
        if not self.user_id or not self.token:
            self.print_test_result("Get User", False, "Missing user_id or token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_gateway_url}/api/v1/users/{self.user_id}",
                headers=headers
            )
            
            success = response.status_code == 200
            if not success:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("Get User", success)
        except Exception as e:
            self.print_test_result("Get User", False, str(e))

    def test_get_users_list(self):
        """Test getting list of users"""
        if not self.token:
            self.print_test_result("Get Users List", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_gateway_url}/api/v1/users",
                headers=headers
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"  Retrieved {len(data.get('users', []))} users")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("Get Users List", success)
        except Exception as e:
            self.print_test_result("Get Users List", False, str(e))

    def test_update_user(self):
        """Test updating user"""
        if not self.user_id or not self.token:
            self.print_test_result("Update User", False, "Missing user_id or token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            update_data = {
                "firstName": "Updated",
                "lastName": "User"
            }
            
            response = requests.put(
                f"{self.api_gateway_url}/api/v1/users/{self.user_id}",
                headers=headers,
                json=update_data
            )
            
            success = response.status_code == 200
            if not success:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("Update User", success)
        except Exception as e:
            self.print_test_result("Update User", False, str(e))

    def test_verify_token(self):
        """Test token verification"""
        if not self.token:
            self.print_test_result("Verify Token", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/verify-token",
                headers=headers
            )
            
            success = response.status_code == 200
            if not success:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("Verify Token", success)
        except Exception as e:
            self.print_test_result("Verify Token", False, str(e))

    def test_ai_completion(self):
        """Test AI completion endpoint with default settings"""
        if not self.token:
            self.print_test_result("AI Completion", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "prompt": "Hello, how are you?",
                "max_tokens": 50
            }
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/completions",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"  AI Response: {data.get('choices', [{}])[0].get('text', '')[:50]}...")
                print(f"  Model used: {data.get('model', 'unknown')}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Completion", success)
        except Exception as e:
            self.print_test_result("AI Completion", False, str(e))

    def test_ai_completion_custom_model(self):
        """Test AI completion endpoint with custom model"""
        if not self.token:
            self.print_test_result("AI Completion Custom Model", False, "Missing token")
            return
            
        try:
            model = "gpt-3.5-turbo-instruct"
            print(f"  Testing custom model: {model}")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "prompt": "Write a short poem about coding.",
                "model": model,
                "max_tokens": 100,
                "temperature": 0.8
            }
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/completions",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"  AI Response: {data.get('choices', [{}])[0].get('text', '')[:50]}...")
                print(f"  Model used: {data.get('model', 'unknown')}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Completion Custom Model", success)
        except Exception as e:
            self.print_test_result("AI Completion Custom Model", False, str(e))

    def test_ai_embedding(self):
        """Test AI embedding endpoint with default settings"""
        if not self.token:
            self.print_test_result("AI Embedding", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "input": "This is a test sentence for embedding."
            }
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/embeddings",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 201
            if success:
                data = response.json()
                embedding_id = data.get("id")
                embedding_vec = data.get("embedding", [])
                print(f"  Embedding created with ID: {embedding_id}")
                print(f"  Embedding vector length: {len(embedding_vec)}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Embedding", success)
        except Exception as e:
            self.print_test_result("AI Embedding", False, str(e))

    def test_ai_embedding_custom_model(self):
        """Test AI embedding endpoint with custom model"""
        if not self.token:
            self.print_test_result("AI Embedding Custom Model", False, "Missing token")
            return
            
        try:
            model = "text-embedding-ada-002"
            print(f"  Testing custom embedding model: {model}")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "input": "This is a test sentence for custom embedding model.",
                "model": model
            }
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/embeddings",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 201
            if success:
                data = response.json()
                embedding_id = data.get("id")
                embedding_vec = data.get("embedding", [])
                print(f"  Embedding created with ID: {embedding_id}")
                print(f"  Embedding vector length: {len(embedding_vec)}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Embedding Custom Model", success)
        except Exception as e:
            self.print_test_result("AI Embedding Custom Model", False, str(e))

    def test_delete_user(self):
        """Test user deletion"""
        if not self.user_id or not self.token:
            self.print_test_result("Delete User", False, "Missing user_id or token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(
                f"{self.api_gateway_url}/api/v1/users/{self.user_id}",
                headers=headers
            )
            
            success = response.status_code == 204
            if not success:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("Delete User", success)
        except Exception as e:
            self.print_test_result("Delete User", False, str(e))

    def test_logout(self):
        """Test user logout"""
        if not self.token:
            self.print_test_result("User Logout", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/logout",
                headers=headers
            )
            
            success = response.status_code == 204
            if not success:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("User Logout", success)
        except Exception as e:
            self.print_test_result("User Logout", False, str(e))

    def test_image_from_url(self):
        """Test image processing from URL"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                
            payload = {
                "prompt": "What is in this image? Describe it in detail.",
                "image_url": self.sample_image_url,
                "model": "gpt-4o-mini"  # Use a model that supports vision
            }
            
            print(f"  Sending request to: {self.api_gateway_url}/api/v1/images/url")
            print(f"  Request payload: {json.dumps(payload)}")
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/images/url",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            
            if success:
                data = response.json()
                print(f"  AI Response: {data.get('text', '')[:100]}...")  # Print first 100 chars
                print(f"  Model used: {data.get('model', 'unknown')}")
            else:
                print(f"  Response: {response.text}")
            
            self.print_test_result("Image Processing from URL", success)
        except Exception as e:
            self.print_test_result("Image Processing from URL", False, str(e))

    # Analytics Service Tests
    def test_analytics_health(self):
        """Test the analytics service health endpoint"""
        try:
            response = requests.get(f"{self.analytics_url}/api/v1/health")
            success = response.status_code == 200 and response.json().get("status") == "ok"
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            self.print_test_result("Analytics Service Health Check", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Analytics Service Health Check", False, str(e))

    def test_log_user_activity(self):
        """Test logging user activity"""
        try:
            payload = {
                "user_id": "test-user-123",
                "action": "login",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Browser/1.0"
            }
            print(f"  Sending payload: {json.dumps(payload)}")
            response = requests.post(f"{self.analytics_url}/api/v1/user-activity", json=payload)
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            self.print_test_result("Log User Activity", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Log User Activity", False, str(e))

    def test_log_ai_call(self):
        """Test logging AI call"""
        try:
            payload = {
                "user_id": "test-user-123",
                "model_used": "gpt-4",
                "call_type": "completion",
                "response_time": 0.75,
                "tokens": 320,
                "success": True
            }
            print(f"  Sending payload: {json.dumps(payload)}")
            response = requests.post(f"{self.analytics_url}/api/v1/ai-call", json=payload)
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            self.print_test_result("Log AI Call", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Log AI Call", False, str(e))

    def test_get_user_stats(self):
        """Test getting user statistics"""
        try:
            # Get stats for the last 7 days
            response = requests.get(f"{self.analytics_url}/api/v1/user-stats")
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text[:100]}...")  # Print first 100 chars
            self.print_test_result("Get User Stats", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get User Stats", False, str(e))

    def test_get_ai_stats(self):
        """Test getting AI statistics"""
        try:
            # Get stats for the last 7 days
            response = requests.get(f"{self.analytics_url}/api/v1/ai-stats")
            success = response.status_code == 200
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text[:100]}...")  # Print first 100 chars
            self.print_test_result("Get AI Stats", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get AI Stats", False, str(e))

    def test_get_total_users(self):
        """Test getting total users"""
        try:
            response = requests.get(f"{self.analytics_url}/api/v1/user-stats/total")
            success = response.status_code == 200 and "total_users" in response.json()
            print(f"  Response status: {response.status_code}")
            print(f"  Response: {response.text}")
            self.print_test_result("Get Total Users", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get Total Users", False, str(e))

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        print(f"Total tests: {self.test_results['total']}")
        print(f"{Fore.GREEN}Passed: {self.test_results['passed']}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.test_results['failed']}{Style.RESET_ALL}")
        
        if self.test_results['failed'] == 0:
            print(f"\n{Fore.GREEN}All tests passed successfully!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}Some tests failed. Please check the logs above.{Style.RESET_ALL}")

if __name__ == "__main__":
    # Parse command line arguments for custom URL
    api_url = "http://localhost:8080"
    analytics_url = "http://localhost:8083"
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    if len(sys.argv) > 2:
        analytics_url = sys.argv[2]
    
    print(f"Testing API Gateway at: {api_url}")
    print(f"Testing Analytics Service at: {analytics_url}")
    
    # Run tests
    tester = ServiceTester(api_url, analytics_url)
    tester.run_all_tests() 