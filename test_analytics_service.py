#!/usr/bin/env python3
import requests
import json
import time
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class AnalyticsServiceTester:
    def __init__(self, analytics_url="http://localhost:8083"):
        self.analytics_url = analytics_url
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }

    def print_header(self, message):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "="*60)
        print(f" {message}")
        print("="*60 + f"{Style.RESET_ALL}\n")

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
        self.print_header("STARTING ANALYTICS SERVICE TESTS")
        
        # Run tests
        self.test_health()
        self.test_log_user_activity()
        self.test_log_ai_call()
        self.test_get_user_stats()
        self.test_get_ai_stats()
        self.test_get_total_users()
        
        # Print summary
        self.print_summary()

    def test_health(self):
        """Test the health endpoint"""
        try:
            response = requests.get(f"{self.analytics_url}/api/v1/health")
            success = response.status_code == 200 and response.json().get("status") == "ok"
            self.print_test_result("Health Check", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Health Check", False, str(e))

    def test_log_user_activity(self):
        """Test logging user activity"""
        try:
            payload = {
                "user_id": "test-user-123",
                "action": "login",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Browser/1.0"
            }
            response = requests.post(f"{self.analytics_url}/api/v1/user-activity", json=payload)
            success = response.status_code == 200
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
            response = requests.post(f"{self.analytics_url}/api/v1/ai-call", json=payload)
            success = response.status_code == 200
            self.print_test_result("Log AI Call", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Log AI Call", False, str(e))

    def test_get_user_stats(self):
        """Test getting user statistics"""
        try:
            # Get stats for the last 7 days
            response = requests.get(f"{self.analytics_url}/api/v1/user-stats")
            success = response.status_code == 200
            self.print_test_result("Get User Stats", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get User Stats", False, str(e))

    def test_get_ai_stats(self):
        """Test getting AI statistics"""
        try:
            # Get stats for the last 7 days
            response = requests.get(f"{self.analytics_url}/api/v1/ai-stats")
            success = response.status_code == 200
            self.print_test_result("Get AI Stats", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get AI Stats", False, str(e))

    def test_get_total_users(self):
        """Test getting total users"""
        try:
            response = requests.get(f"{self.analytics_url}/api/v1/user-stats/total")
            success = response.status_code == 200 and "total_users" in response.json()
            self.print_test_result("Get Total Users", success, None if success else f"Unexpected response: {response.text}")
        except Exception as e:
            self.print_test_result("Get Total Users", False, str(e))

    def print_summary(self):
        """Print the test summary"""
        print("\n" + "="*60)
        print(f"{Fore.CYAN}{Style.BRIGHT} TEST SUMMARY{Style.RESET_ALL}")
        print("="*60)
        print(f"Total tests: {self.test_results['total']}")
        print(f"{Fore.GREEN}Passed: {self.test_results['passed']}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.test_results['failed']}{Style.RESET_ALL}")
        
        if self.test_results['failed'] == 0:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}All tests passed successfully!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}Some tests failed. Please check the output above.{Style.RESET_ALL}")

if __name__ == "__main__":
    tester = AnalyticsServiceTester()
    tester.run_all_tests() 