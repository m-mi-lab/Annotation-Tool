#!/usr/bin/env python3
"""
Test script for updated login functionality that accepts both email and username (full_name)
"""

import requests
import sys
import json
from datetime import datetime

class LoginTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_info = None
        self.regular_user_info = None
        self.created_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def get_admin_info(self):
        """Get admin user information to check full_name"""
        # First login as admin to get token
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login for Info Retrieval",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            admin_token = response['access_token']
            
            # Get admin user info
            headers = {'Authorization': f'Bearer {admin_token}'}
            try:
                me_response = requests.get(f"{self.base_url}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    self.admin_info = me_response.json()
                    print(f"   Admin info retrieved: {self.admin_info.get('email')} - Full name: '{self.admin_info.get('full_name')}'")
                    return True
            except Exception as e:
                print(f"   Error getting admin info: {e}")
        
        return False

    def create_test_user(self):
        """Create a test user with a known full_name for testing"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user_data = {
            "email": f"testuser_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"TestUser{timestamp}"
        }
        
        success, response = self.run_test(
            "Create Test User for Login Testing",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'id' in response:
            self.created_user_id = response['id']
            self.regular_user_info = {
                'email': test_user_data['email'],
                'password': test_user_data['password'],
                'full_name': test_user_data['full_name'],
                'id': response['id']
            }
            print(f"   Created test user: {test_user_data['email']} with full_name: '{test_user_data['full_name']}'")
            return True
        return False

    def test_login_with_email_admin(self):
        """Test 1: Login with admin email"""
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Login with Admin Email",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success:
            # Verify response contains access_token
            if 'access_token' in response and 'token_type' in response:
                print(f"   ✅ Login successful with access_token")
                print(f"   Token type: {response.get('token_type')}")
                return True
            else:
                print(f"   ❌ Response missing access_token or token_type")
                return False
        return False

    def test_login_with_username_admin(self):
        """Test 2: Login with admin username (full_name)"""
        if not self.admin_info or not self.admin_info.get('full_name'):
            print("❌ Admin full_name not available for testing")
            return False
        
        admin_username_credentials = {
            "email": self.admin_info['full_name'],  # Using full_name as email field
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Login with Admin Username (full_name)",
            "POST",
            "auth/login",
            200,
            data=admin_username_credentials
        )
        
        if success:
            # Verify response contains access_token
            if 'access_token' in response and 'token_type' in response:
                print(f"   ✅ Login successful with username: '{self.admin_info['full_name']}'")
                print(f"   Token type: {response.get('token_type')}")
                return True
            else:
                print(f"   ❌ Response missing access_token or token_type")
                return False
        return False

    def test_login_with_email_regular_user(self):
        """Test 3: Login with regular user email"""
        if not self.regular_user_info:
            print("❌ Regular user info not available for testing")
            return False
        
        user_credentials = {
            "email": self.regular_user_info['email'],
            "password": self.regular_user_info['password']
        }
        
        success, response = self.run_test(
            "Login with Regular User Email",
            "POST",
            "auth/login",
            200,
            data=user_credentials
        )
        
        if success:
            # Verify response contains access_token
            if 'access_token' in response and 'token_type' in response:
                print(f"   ✅ Login successful with email: {self.regular_user_info['email']}")
                return True
            else:
                print(f"   ❌ Response missing access_token or token_type")
                return False
        return False

    def test_login_with_username_regular_user(self):
        """Test 4: Login with regular user username (full_name)"""
        if not self.regular_user_info:
            print("❌ Regular user info not available for testing")
            return False
        
        user_username_credentials = {
            "email": self.regular_user_info['full_name'],  # Using full_name as email field
            "password": self.regular_user_info['password']
        }
        
        success, response = self.run_test(
            "Login with Regular User Username (full_name)",
            "POST",
            "auth/login",
            200,
            data=user_username_credentials
        )
        
        if success:
            # Verify response contains access_token
            if 'access_token' in response and 'token_type' in response:
                print(f"   ✅ Login successful with username: '{self.regular_user_info['full_name']}'")
                return True
            else:
                print(f"   ❌ Response missing access_token or token_type")
                return False
        return False

    def test_invalid_username_login(self):
        """Test 5: Login with non-existent username"""
        invalid_credentials = {
            "email": "NonExistentUser123",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Login with Non-existent Username",
            "POST",
            "auth/login",
            401,  # Expect unauthorized
            data=invalid_credentials
        )
        
        if success:
            # Verify error message
            if 'detail' in response and 'Invalid credentials' in response['detail']:
                print(f"   ✅ Proper error message: {response['detail']}")
                return True
            else:
                print(f"   ❌ Unexpected error message: {response}")
                return False
        return False

    def test_invalid_password_login(self):
        """Test 6: Login with correct username but wrong password"""
        if not self.regular_user_info:
            print("❌ Regular user info not available for testing")
            return False
        
        invalid_credentials = {
            "email": self.regular_user_info['full_name'],
            "password": "WrongPassword123"
        }
        
        success, response = self.run_test(
            "Login with Correct Username but Wrong Password",
            "POST",
            "auth/login",
            401,  # Expect unauthorized
            data=invalid_credentials
        )
        
        if success:
            # Verify error message
            if 'detail' in response and 'Invalid credentials' in response['detail']:
                print(f"   ✅ Proper error message: {response['detail']}")
                return True
            else:
                print(f"   ❌ Unexpected error message: {response}")
                return False
        return False

    def test_input_format_validation(self):
        """Test 7: Verify email field accepts non-email strings"""
        # Test with various username formats (no @ symbol)
        test_cases = [
            {
                "name": "Simple Username",
                "email": "testuser",
                "password": "testpass"
            },
            {
                "name": "Username with Numbers",
                "email": "user123",
                "password": "testpass"
            },
            {
                "name": "Username with Spaces",
                "email": "Test User Name",
                "password": "testpass"
            },
            {
                "name": "Username with Special Characters",
                "email": "test_user-name",
                "password": "testpass"
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            print(f"\n   Testing {test_case['name']}: '{test_case['email']}'")
            
            # We expect 401 (invalid credentials) not 422 (validation error)
            # This confirms the field accepts non-email formats
            success, response = self.run_test(
                f"Input Format - {test_case['name']}",
                "POST",
                "auth/login",
                401,  # Expect unauthorized (not validation error)
                data=test_case
            )
            
            if success:
                # Check that it's "Invalid credentials" not a validation error
                if 'detail' in response:
                    if 'Invalid credentials' in response['detail']:
                        print(f"      ✅ Non-email format accepted, got expected 'Invalid credentials'")
                    elif 'validation' in response['detail'].lower() or 'email' in response['detail'].lower():
                        print(f"      ❌ Got validation error instead of credentials error: {response['detail']}")
                        all_passed = False
                    else:
                        print(f"      ✅ Non-email format accepted: {response['detail']}")
                else:
                    print(f"      ✅ Non-email format accepted")
            else:
                print(f"      ❌ Unexpected response for {test_case['name']}")
                all_passed = False
        
        return all_passed

    def cleanup_test_user(self):
        """Clean up created test user"""
        if not self.created_user_id:
            return True
        
        # Login as admin to delete the test user
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        try:
            login_response = requests.post(f"{self.base_url}/auth/login", json=admin_credentials)
            if login_response.status_code == 200:
                admin_token = login_response.json()['access_token']
                headers = {'Authorization': f'Bearer {admin_token}'}
                
                delete_response = requests.delete(f"{self.base_url}/admin/users/{self.created_user_id}", headers=headers)
                if delete_response.status_code == 200:
                    print(f"   ✅ Test user cleaned up successfully")
                    return True
                else:
                    print(f"   ⚠️  Could not delete test user: {delete_response.status_code}")
            else:
                print(f"   ⚠️  Could not login as admin for cleanup")
        except Exception as e:
            print(f"   ⚠️  Error during cleanup: {e}")
        
        return False

    def run_all_tests(self):
        """Run all login functionality tests"""
        print("🚀 Starting Updated Login Functionality Tests")
        print("Testing login with both email and username (full_name)")
        print("=" * 70)
        
        # Setup: Get admin info and create test user
        print("\n" + "=" * 25 + " SETUP " + "=" * 25)
        if not self.get_admin_info():
            print("❌ Could not retrieve admin info, stopping tests")
            return False
        
        if not self.create_test_user():
            print("❌ Could not create test user, stopping tests")
            return False
        
        # Test 1: Login with admin email
        print("\n" + "=" * 20 + " TEST 1: ADMIN EMAIL LOGIN " + "=" * 20)
        test1_result = self.test_login_with_email_admin()
        
        # Test 2: Login with admin username (full_name)
        print("\n" + "=" * 20 + " TEST 2: ADMIN USERNAME LOGIN " + "=" * 20)
        test2_result = self.test_login_with_username_admin()
        
        # Test 3: Login with regular user email
        print("\n" + "=" * 20 + " TEST 3: REGULAR USER EMAIL LOGIN " + "=" * 20)
        test3_result = self.test_login_with_email_regular_user()
        
        # Test 4: Login with regular user username (full_name)
        print("\n" + "=" * 20 + " TEST 4: REGULAR USER USERNAME LOGIN " + "=" * 20)
        test4_result = self.test_login_with_username_regular_user()
        
        # Test 5: Invalid credentials - non-existent username
        print("\n" + "=" * 20 + " TEST 5: INVALID USERNAME " + "=" * 20)
        test5_result = self.test_invalid_username_login()
        
        # Test 6: Invalid credentials - wrong password
        print("\n" + "=" * 20 + " TEST 6: INVALID PASSWORD " + "=" * 20)
        test6_result = self.test_invalid_password_login()
        
        # Test 7: Input format validation
        print("\n" + "=" * 20 + " TEST 7: INPUT FORMAT VALIDATION " + "=" * 20)
        test7_result = self.test_input_format_validation()
        
        # Cleanup
        print("\n" + "=" * 25 + " CLEANUP " + "=" * 25)
        self.cleanup_test_user()
        
        # Print final results
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Summary of specific test results
        test_results = [
            ("Admin Email Login", test1_result),
            ("Admin Username Login", test2_result),
            ("Regular User Email Login", test3_result),
            ("Regular User Username Login", test4_result),
            ("Invalid Username Rejection", test5_result),
            ("Invalid Password Rejection", test6_result),
            ("Input Format Validation", test7_result)
        ]
        
        print("\n📋 Test Summary:")
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} - {test_name}")
        
        all_critical_passed = all([test1_result, test2_result, test3_result, test4_result, test5_result, test6_result])
        
        if all_critical_passed and test7_result:
            print("\n🎉 All tests passed! Login functionality works with both email and username.")
            return True
        elif all_critical_passed:
            print("\n✅ Core login functionality works, minor issues with input validation.")
            return True
        else:
            print(f"\n⚠️  Some critical tests failed. Login functionality needs attention.")
            return False

def main():
    tester = LoginTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())