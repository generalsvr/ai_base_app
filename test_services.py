#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class ServiceTester:
    def __init__(self, api_gateway_url="http://localhost:8080"):
        self.api_gateway_url = api_gateway_url
        self.token = None
        self.user_id = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        self.created_username = f"testuser_{int(time.time())}"
        self.created_password = "Password123!"

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
        
        # Cleanup - logout first, then delete user
        self.test_logout()
        self.test_delete_user()
        
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
                f"{self.api_gateway_url}/api/v1/ai/completions",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"  AI Response: {data.get('choices', [{}])[0].get('text', '')[:30]}...")
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
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get default API key from environment
            api_key = os.environ.get("OPENAI_API_KEY", "")
            
            payload = {
                "prompt": "Write a haiku about programming:",
                "max_tokens": 100,
                "model": "gpt-3.5-turbo-instruct",  # Explicitly specify model
                "api_key": api_key,  # Use the same API key for testing
                "base_url": "https://api.openai.com/v1"  # Use standard base URL for testing
            }
            
            print(f"  Testing custom model: {payload['model']}")
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/ai/completions",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                print(f"  AI Response: {data.get('choices', [{}])[0].get('text', '')[:30]}...")
                print(f"  Model used: {data.get('model', 'unknown')}")
                
                # Verify the model used matches what we requested
                model_success = "gpt-3.5-turbo-instruct" in data.get('model', '')
                if not model_success:
                    print(f"  {Fore.YELLOW}Warning: Model used doesn't match requested model{Style.RESET_ALL}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Completion Custom Model", success)
        except Exception as e:
            self.print_test_result("AI Completion Custom Model", False, str(e))

    def test_ai_embedding(self):
        """Test AI embedding creation with default settings"""
        if not self.token:
            self.print_test_result("AI Embedding", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "input": "This is a test embedding for semantic search."
            }
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/ai/embeddings",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 201
            if success:
                data = response.json()
                print(f"  Embedding created with ID: {data.get('id')}")
                print(f"  Embedding vector length: {len(data.get('embedding', []))}")
            else:
                print(f"  Response status: {response.status_code}")
                print(f"  Response: {response.text}")
                
            self.print_test_result("AI Embedding", success)
        except Exception as e:
            self.print_test_result("AI Embedding", False, str(e))

    def test_ai_embedding_custom_model(self):
        """Test AI embedding creation with custom model"""
        if not self.token:
            self.print_test_result("AI Embedding Custom Model", False, "Missing token")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get default API key from environment
            api_key = os.environ.get("OPENAI_API_KEY", "")
            
            payload = {
                "input": "This is a test embedding using a custom model configuration.",
                "model": "text-embedding-ada-002",  # Explicitly specify model
                "api_key": api_key,  # Use the same API key for testing
                "base_url": "https://api.openai.com/v1"  # Use standard base URL for testing
            }
            
            print(f"  Testing custom embedding model: {payload['model']}")
            
            response = requests.post(
                f"{self.api_gateway_url}/api/v1/ai/embeddings",
                headers=headers,
                json=payload
            )
            
            success = response.status_code == 201
            if success:
                data = response.json()
                print(f"  Embedding created with ID: {data.get('id')}")
                print(f"  Embedding vector length: {len(data.get('embedding', []))}")
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
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    
    print(f"Testing API Gateway at: {api_url}")
    
    # Run tests
    tester = ServiceTester(api_url)
    tester.run_all_tests() 