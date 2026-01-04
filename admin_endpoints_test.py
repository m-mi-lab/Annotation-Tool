#!/usr/bin/env python3
"""
Focused test for admin role-based endpoints as requested in the review.
Tests all admin user and document management endpoints with proper RBAC.
"""

import requests
import json
import sys
from datetime import datetime

class AdminEndpointsTest:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.regular_token = None
        self.admin_user_id = None
        self.created_user_ids = []
        self.created_document_ids = []
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        if details:
            print(f"   {details}")

    def make_request(self, method, endpoint, token=None, data=None, files=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers={k:v for k,v in headers.items() if k != 'Content-Type'})
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {}
            
            return success, response.status_code, response_data
        except Exception as e:
            return False, 0, {"error": str(e)}

    def setup_authentication(self):
        """Setup admin and regular user authentication"""
        print("🔐 Setting up authentication...")
        
        # Admin login
        success, status, response = self.make_request(
            'POST', 'auth/login', 
            data={"email": "admin@sdoh.com", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print("   ✅ Admin authentication successful")
            
            # Get admin user info
            success, status, user_info = self.make_request('GET', 'auth/me', token=self.admin_token)
            if success:
                self.admin_user_id = user_info.get('id')
                print(f"   Admin ID: {self.admin_user_id}")
        else:
            print("   ❌ Admin authentication failed")
            return False

        # Create and login regular user for RBAC testing
        timestamp = datetime.now().strftime('%H%M%S')
        regular_user = {
            "email": f"regular_{timestamp}@test.com",
            "password": "RegularPass123!",
            "full_name": f"Regular User {timestamp}"
        }
        
        success, status, response = self.make_request('POST', 'auth/register', data=regular_user)
        if success:
            # Login as regular user
            success, status, response = self.make_request(
                'POST', 'auth/login',
                data={"email": regular_user["email"], "password": regular_user["password"]}
            )
            if success and 'access_token' in response:
                self.regular_token = response['access_token']
                print("   ✅ Regular user authentication successful")
            else:
                print("   ❌ Regular user login failed")
        else:
            print("   ❌ Regular user registration failed")
        
        return True

    def test_admin_users_get(self):
        """Test GET /api/admin/users"""
        success, status, response = self.make_request('GET', 'admin/users', token=self.admin_token)
        
        if success and isinstance(response, list):
            # Verify response format
            if response:
                user = response[0]
                required_fields = ['id', 'email', 'full_name', 'role']
                missing_fields = [f for f in required_fields if f not in user]
                has_password = 'password' in user
                
                if missing_fields:
                    self.log_test("GET /api/admin/users - Response Format", False, 
                                f"Missing fields: {missing_fields}")
                elif has_password:
                    self.log_test("GET /api/admin/users - Password Exposure", False, 
                                "Password field should not be exposed")
                else:
                    self.log_test("GET /api/admin/users - Response Format", True, 
                                f"Found {len(response)} users, all required fields present")
            else:
                self.log_test("GET /api/admin/users - Response Format", True, "Empty user list")
        else:
            self.log_test("GET /api/admin/users", False, f"Status: {status}")

    def test_admin_users_post(self):
        """Test POST /api/admin/users"""
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Test creating annotator
        annotator_data = {
            "email": f"test_annotator_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": f"Test Annotator {timestamp}",
            "role": "annotator"
        }
        
        success, status, response = self.make_request('POST', 'admin/users', token=self.admin_token, data=annotator_data)
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            expected_fields = ['id', 'email', 'full_name', 'role']
            missing_fields = [f for f in expected_fields if f not in response]
            has_password = 'password' in response
            
            if missing_fields:
                self.log_test("POST /api/admin/users - Annotator Creation", False, 
                            f"Missing fields: {missing_fields}")
            elif has_password:
                self.log_test("POST /api/admin/users - Password Exposure", False, 
                            "Password should not be returned")
            elif response.get('role') != 'annotator':
                self.log_test("POST /api/admin/users - Role Assignment", False, 
                            f"Expected role 'annotator', got '{response.get('role')}'")
            else:
                self.log_test("POST /api/admin/users - Annotator Creation", True, 
                            f"Created annotator with ID: {response['id']}")
        else:
            self.log_test("POST /api/admin/users - Annotator Creation", False, f"Status: {status}")

        # Test creating admin
        admin_data = {
            "email": f"test_admin_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": f"Test Admin {timestamp}",
            "role": "admin"
        }
        
        success, status, response = self.make_request('POST', 'admin/users', token=self.admin_token, data=admin_data)
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            if response.get('role') == 'admin':
                self.log_test("POST /api/admin/users - Admin Creation", True, 
                            f"Created admin with ID: {response['id']}")
            else:
                self.log_test("POST /api/admin/users - Admin Creation", False, 
                            f"Expected role 'admin', got '{response.get('role')}'")
        else:
            self.log_test("POST /api/admin/users - Admin Creation", False, f"Status: {status}")

    def test_admin_users_put(self):
        """Test PUT /api/admin/users/{user_id}"""
        if not self.created_user_ids:
            self.log_test("PUT /api/admin/users/{user_id}", False, "No test users available")
            return

        user_id = self.created_user_ids[0]
        
        # Test updating is_active
        update_data = {"is_active": False}
        success, status, response = self.make_request('PUT', f'admin/users/{user_id}', 
                                                    token=self.admin_token, data=update_data)
        
        if success and response.get('is_active') == False:
            self.log_test("PUT /api/admin/users/{user_id} - Deactivate User", True, 
                        "User successfully deactivated")
        else:
            self.log_test("PUT /api/admin/users/{user_id} - Deactivate User", False, 
                        f"Status: {status}, is_active: {response.get('is_active')}")

        # Test updating role
        update_data = {"role": "admin", "is_active": True}
        success, status, response = self.make_request('PUT', f'admin/users/{user_id}', 
                                                    token=self.admin_token, data=update_data)
        
        if success and response.get('role') == 'admin' and response.get('is_active') == True:
            self.log_test("PUT /api/admin/users/{user_id} - Update Role & Reactivate", True, 
                        "User role updated to admin and reactivated")
        else:
            self.log_test("PUT /api/admin/users/{user_id} - Update Role & Reactivate", False, 
                        f"Status: {status}, role: {response.get('role')}, active: {response.get('is_active')}")

    def test_admin_users_delete(self):
        """Test DELETE /api/admin/users/{user_id}"""
        if not self.created_user_ids:
            self.log_test("DELETE /api/admin/users/{user_id}", False, "No test users available")
            return

        # Test preventing self-delete
        success, status, response = self.make_request('DELETE', f'admin/users/{self.admin_user_id}', 
                                                    token=self.admin_token, expected_status=400)
        
        if success:
            self.log_test("DELETE /api/admin/users/{user_id} - Prevent Self-Delete", True, 
                        "Self-deletion properly prevented")
        else:
            self.log_test("DELETE /api/admin/users/{user_id} - Prevent Self-Delete", False, 
                        f"Expected 400, got {status}")

        # Test deleting another user
        user_id = self.created_user_ids[0]
        success, status, response = self.make_request('DELETE', f'admin/users/{user_id}', 
                                                    token=self.admin_token)
        
        if success and 'message' in response:
            self.created_user_ids.remove(user_id)
            self.log_test("DELETE /api/admin/users/{user_id} - Delete User", True, 
                        f"User deleted: {response.get('user_name', 'N/A')}")
        else:
            self.log_test("DELETE /api/admin/users/{user_id} - Delete User", False, 
                        f"Status: {status}")

    def test_admin_users_bulk_delete(self):
        """Test POST /api/admin/users/bulk-delete"""
        if len(self.created_user_ids) < 2:
            self.log_test("POST /api/admin/users/bulk-delete", False, "Need at least 2 test users")
            return

        # Include current admin in the list to test skipping
        user_ids_to_delete = self.created_user_ids[:2] + [self.admin_user_id]
        
        bulk_delete_data = {"ids": user_ids_to_delete}
        success, status, response = self.make_request('POST', 'admin/users/bulk-delete', 
                                                    token=self.admin_token, data=bulk_delete_data)
        
        if success:
            deleted_count = response.get('deleted', 0)
            skipped_count = response.get('skipped', 0)
            
            # Should delete 2 users and skip 1 (current admin)
            if deleted_count == 2 and skipped_count == 1:
                self.log_test("POST /api/admin/users/bulk-delete", True, 
                            f"Deleted {deleted_count} users, skipped {skipped_count} (current admin)")
                # Remove deleted users from tracking
                for user_id in user_ids_to_delete[:2]:
                    if user_id in self.created_user_ids:
                        self.created_user_ids.remove(user_id)
            else:
                self.log_test("POST /api/admin/users/bulk-delete", False, 
                            f"Expected deleted=2, skipped=1, got deleted={deleted_count}, skipped={skipped_count}")
        else:
            self.log_test("POST /api/admin/users/bulk-delete", False, f"Status: {status}")

    def test_admin_documents_bulk_delete(self):
        """Test POST /api/admin/documents/bulk-delete"""
        # First create some test documents
        import io
        csv_content = """patient_id,discharge_summary
1,"Test patient with diabetes"
2,"Another test patient with hypertension"
"""
        
        for i in range(2):
            files = {
                'file': (f'test_doc_{i}.csv', csv_content, 'text/csv'),
                'project_name': (None, f'Test Project {i}'),
                'description': (None, f'Test document {i} for bulk deletion')
            }
            
            success, status, response = self.make_request('POST', 'documents/upload', 
                                                        token=self.admin_token, files=files)
            if success and 'id' in response:
                self.created_document_ids.append(response['id'])

        if len(self.created_document_ids) < 2:
            self.log_test("POST /api/admin/documents/bulk-delete", False, "Failed to create test documents")
            return

        # Test bulk delete
        bulk_delete_data = {"ids": self.created_document_ids}
        success, status, response = self.make_request('POST', 'admin/documents/bulk-delete', 
                                                    token=self.admin_token, data=bulk_delete_data)
        
        if success:
            deleted_count = response.get('deleted', 0)
            sentences_deleted = response.get('sentences_deleted', 0)
            
            if deleted_count == len(self.created_document_ids):
                self.log_test("POST /api/admin/documents/bulk-delete", True, 
                            f"Deleted {deleted_count} documents, {sentences_deleted} sentences")
                self.created_document_ids.clear()
            else:
                self.log_test("POST /api/admin/documents/bulk-delete", False, 
                            f"Expected {len(self.created_document_ids)} deleted, got {deleted_count}")
        else:
            self.log_test("POST /api/admin/documents/bulk-delete", False, f"Status: {status}")

    def test_rbac_enforcement(self):
        """Test that non-admin users cannot access admin endpoints"""
        if not self.regular_token:
            self.log_test("RBAC Enforcement", False, "No regular user token available")
            return

        # Test all admin endpoints with regular user token (should get 403)
        endpoints_to_test = [
            ('GET', 'admin/users'),
            ('POST', 'admin/users'),
            ('PUT', 'admin/users/fake-id'),
            ('DELETE', 'admin/users/fake-id'),
            ('POST', 'admin/users/bulk-delete'),
            ('POST', 'admin/documents/bulk-delete')
        ]

        all_blocked = True
        for method, endpoint in endpoints_to_test:
            success, status, response = self.make_request(method, endpoint, 
                                                        token=self.regular_token, 
                                                        data={"test": "data"}, 
                                                        expected_status=403)
            if not success:
                all_blocked = False
                print(f"   ❌ {method} {endpoint} - Expected 403, got {status}")

        if all_blocked:
            self.log_test("RBAC Enforcement - All Admin Endpoints", True, 
                        "All admin endpoints properly blocked for non-admin users")
        else:
            self.log_test("RBAC Enforcement - All Admin Endpoints", False, 
                        "Some admin endpoints not properly protected")

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete remaining test users
        if self.created_user_ids:
            for user_id in self.created_user_ids[:]:
                success, status, response = self.make_request('DELETE', f'admin/users/{user_id}', 
                                                            token=self.admin_token)
                if success:
                    self.created_user_ids.remove(user_id)
                    print(f"   ✅ Deleted user {user_id}")

        # Delete remaining test documents
        if self.created_document_ids:
            for doc_id in self.created_document_ids[:]:
                success, status, response = self.make_request('DELETE', f'admin/documents/{doc_id}', 
                                                            token=self.admin_token)
                if success:
                    self.created_document_ids.remove(doc_id)
                    print(f"   ✅ Deleted document {doc_id}")

    def run_all_tests(self):
        """Run all admin endpoint tests"""
        print("🚀 Testing Admin Role-Based Endpoints")
        print("=" * 50)
        
        if not self.setup_authentication():
            print("❌ Authentication setup failed, aborting tests")
            return False

        print("\n📋 Testing Admin User Management Endpoints:")
        self.test_admin_users_get()
        self.test_admin_users_post()
        self.test_admin_users_put()
        self.test_admin_users_delete()
        self.test_admin_users_bulk_delete()

        print("\n📄 Testing Admin Document Management Endpoints:")
        self.test_admin_documents_bulk_delete()

        print("\n🔒 Testing RBAC Enforcement:")
        self.test_rbac_enforcement()

        self.cleanup()

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All admin endpoint tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = AdminEndpointsTest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())