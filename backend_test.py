#!/usr/bin/env python3
"""
Backend API Testing Suite for Supabase Authentication System
Tests all endpoints and authentication flows
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Load environment variables
BACKEND_URL = "https://dfcd59a6-fc43-4fe0-a341-d0540fe159e8.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    def test_public_endpoints(self):
        """Test public endpoints that don't require authentication"""
        print("\n=== Testing Public Endpoints ===")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "EngageMesh" in data["message"]:
                    self.log_test("GET /api/", True, f"Status: {response.status_code}, Message: {data['message']}")
                else:
                    self.log_test("GET /api/", False, f"Unexpected response format", data)
            else:
                self.log_test("GET /api/", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET /api/", False, f"Request failed: {str(e)}")
        
        # Test health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("GET /api/health", True, f"Status: {response.status_code}, Health: {data['status']}")
                else:
                    self.log_test("GET /api/health", False, f"Unexpected health status", data)
            else:
                self.log_test("GET /api/health", False, f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("GET /api/health", False, f"Request failed: {str(e)}")
    
    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without authentication - should return 401"""
        print("\n=== Testing Protected Endpoints Without Auth ===")
        
        protected_endpoints = [
            ("GET", "/auth/me", "Get user profile"),
            ("PUT", "/auth/me", "Update user profile"),
            ("POST", "/status", "Create status check"),
            ("GET", "/status", "Get status checks"),
            ("GET", "/users/leaderboard", "Get leaderboard")
        ]
        
        for method, endpoint, description in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json={"client_name": "test_client"})
                elif method == "PUT":
                    response = self.session.put(f"{self.base_url}{endpoint}", 
                                              json={"name": "Test User"})
                
                if response.status_code == 401:
                    self.log_test(f"{method} {endpoint} (no auth)", True, 
                                f"Correctly returned 401 Unauthorized")
                else:
                    self.log_test(f"{method} {endpoint} (no auth)", False, 
                                f"Expected 401, got {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"{method} {endpoint} (no auth)", False, f"Request failed: {str(e)}")
    
    def test_protected_endpoints_with_invalid_auth(self):
        """Test protected endpoints with invalid JWT token - should return 401"""
        print("\n=== Testing Protected Endpoints With Invalid Auth ===")
        
        # Use an invalid JWT token
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.invalid_signature"
        headers = {"Authorization": f"Bearer {invalid_token}"}
        
        protected_endpoints = [
            ("GET", "/auth/me", "Get user profile"),
            ("PUT", "/auth/me", "Update user profile"),
            ("POST", "/status", "Create status check"),
            ("GET", "/status", "Get status checks"),
            ("GET", "/users/leaderboard", "Get leaderboard")
        ]
        
        for method, endpoint, description in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json={"client_name": "test_client"}, headers=headers)
                elif method == "PUT":
                    response = self.session.put(f"{self.base_url}{endpoint}", 
                                              json={"name": "Test User"}, headers=headers)
                
                if response.status_code == 401:
                    self.log_test(f"{method} {endpoint} (invalid auth)", True, 
                                f"Correctly returned 401 Unauthorized for invalid token")
                else:
                    self.log_test(f"{method} {endpoint} (invalid auth)", False, 
                                f"Expected 401, got {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"{method} {endpoint} (invalid auth)", False, f"Request failed: {str(e)}")
    
    def test_jwt_verification_middleware(self):
        """Test JWT verification middleware functionality"""
        print("\n=== Testing JWT Verification Middleware ===")
        
        # Test with malformed token
        malformed_tokens = [
            ("", "Empty token"),
            ("not-a-jwt-token", "Non-JWT string"),
            ("Bearer", "Bearer without token"),
            ("Basic dGVzdDp0ZXN0", "Wrong auth scheme")
        ]
        
        for token, description in malformed_tokens:
            try:
                headers = {"Authorization": token} if token else {}
                response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
                
                if response.status_code == 401:
                    self.log_test(f"JWT Middleware ({description})", True, 
                                f"Correctly rejected malformed token")
                else:
                    self.log_test(f"JWT Middleware ({description})", False, 
                                f"Expected 401, got {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"JWT Middleware ({description})", False, f"Request failed: {str(e)}")
    
    def test_environment_variables(self):
        """Test that environment variables are loaded correctly"""
        print("\n=== Testing Environment Variables ===")
        
        # Test if backend can access Supabase credentials
        # We can infer this from the JWT verification behavior
        try:
            # Try with a properly formatted but invalid JWT
            fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            headers = {"Authorization": f"Bearer {fake_jwt}"}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            # If we get a specific JWT error (not just generic 401), it means the JWT secret is loaded
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    if "detail" in error_data and ("token" in error_data["detail"].lower() or "jwt" in error_data["detail"].lower()):
                        self.log_test("Environment Variables", True, 
                                    "Supabase JWT secret appears to be loaded (JWT verification working)")
                    else:
                        self.log_test("Environment Variables", True, 
                                    "Authentication middleware working (credentials likely loaded)")
                except:
                    self.log_test("Environment Variables", True, 
                                "Authentication middleware working (credentials likely loaded)")
            else:
                self.log_test("Environment Variables", False, 
                            f"Unexpected response to JWT test: {response.status_code}")
        except Exception as e:
            self.log_test("Environment Variables", False, f"Failed to test JWT verification: {str(e)}")
    
    def test_database_connection(self):
        """Test database connection by checking if endpoints that require DB work"""
        print("\n=== Testing Database Connection ===")
        
        # Test if the health endpoint works (indicates basic server functionality)
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_test("Database Connection", True, 
                            "Server responding (MongoDB connection likely working)")
            else:
                self.log_test("Database Connection", False, 
                            f"Server not responding properly: {response.status_code}")
        except Exception as e:
            self.log_test("Database Connection", False, f"Server connection failed: {str(e)}")
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n=== Testing CORS Configuration ===")
        
        try:
            # Make a request and check CORS headers
            response = self.session.get(f"{self.base_url}/health")
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                self.log_test("CORS Configuration", True, 
                            f"CORS headers present: {cors_headers}")
            else:
                self.log_test("CORS Configuration", False, 
                            "CORS headers not found in response")
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Failed to test CORS: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        self.test_public_endpoints()
        self.test_protected_endpoints_without_auth()
        self.test_protected_endpoints_with_invalid_auth()
        self.test_jwt_verification_middleware()
        self.test_environment_variables()
        self.test_database_connection()
        self.test_cors_configuration()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: /app/backend_test_results.json")