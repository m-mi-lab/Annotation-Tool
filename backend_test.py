import requests
import sys
import json
import io
import csv
from datetime import datetime

class SDOHAPITester:
    def __init__(self, base_url="https://sdoh-tagger.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_document_id = None
        self.test_sentence_id = None
        self.created_user_ids = []  # Track created users for cleanup

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
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
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
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

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_domains_endpoint(self):
        """Test domains endpoint"""
        return self.run_test("Get SDOH Domains", "GET", "domains", 200)

    def test_admin_login(self):
        """Test admin login with predefined credentials"""
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained successfully")
            return True
        return False

    def test_admin_get_current_user(self):
        """Test getting admin user info"""
        # Temporarily switch to admin token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Get Admin User Info", "GET", "auth/me", 200)
        
        if success and response.get('role') == 'admin':
            self.admin_user_id = response.get('id')
            print(f"   Admin user confirmed with role: {response.get('role')}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_get_all_users(self):
        """Test admin endpoint to get all users"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Admin - Get All Users", "GET", "admin/users", 200)
        
        if success:
            print(f"   Found {len(response)} users in system")
            for user in response[:3]:  # Show first 3 users
                print(f"   - {user.get('full_name')} ({user.get('email')}) - {user.get('role')}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_create_annotator(self):
        """Test admin creating a new annotator account"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        timestamp = datetime.now().strftime('%H%M%S')
        new_annotator = {
            "email": f"annotator_{timestamp}@sdoh.com",
            "password": "AnnotatorPass123!",
            "full_name": f"Test Annotator {timestamp}",
            "role": "annotator"
        }
        
        success, response = self.run_test(
            "Admin - Create Annotator",
            "POST",
            "admin/users",
            200,
            data=new_annotator
        )
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            print(f"   Created annotator with ID: {response['id']}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_create_admin(self):
        """Test admin creating a new admin account"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        timestamp = datetime.now().strftime('%H%M%S')
        new_admin = {
            "email": f"admin_{timestamp}@sdoh.com",
            "password": "AdminPass123!",
            "full_name": f"Test Admin {timestamp}",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Admin - Create Admin",
            "POST",
            "admin/users",
            200,
            data=new_admin
        )
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            print(f"   Created admin with ID: {response['id']}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_update_user(self):
        """Test admin updating user account"""
        if not self.created_user_ids:
            print("❌ No created users to update")
            return False
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        user_id = self.created_user_ids[0]
        update_data = {
            "full_name": "Updated Test User",
            "is_active": False  # Deactivate user
        }
        
        success, response = self.run_test(
            "Admin - Update User",
            "PUT",
            f"admin/users/{user_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"   Updated user - Active: {response.get('is_active')}")
            print(f"   Updated name: {response.get('full_name')}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_reactivate_user(self):
        """Test admin reactivating user account"""
        if not self.created_user_ids:
            print("❌ No created users to reactivate")
            return False
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        user_id = self.created_user_ids[0]
        update_data = {
            "is_active": True  # Reactivate user
        }
        
        success, response = self.run_test(
            "Admin - Reactivate User",
            "PUT",
            f"admin/users/{user_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"   Reactivated user - Active: {response.get('is_active')}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_document_upload(self):
        """Test admin document upload with project metadata"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        # Create test CSV content
        csv_content = self.create_test_csv().getvalue()
        
        # Create file-like object with project metadata
        files = {
            'file': ('admin_test_discharge_summaries.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Admin Test Project'),
            'description': (None, 'Test project uploaded by admin for annotation team')
        }
        
        success, response = self.run_test(
            "Admin - Document Upload with Metadata",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            self.test_document_id = response['id']
            print(f"   Document ID: {self.test_document_id}")
            print(f"   Project: {response.get('project_name')}")
            print(f"   Description: {response.get('description')}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_delete_document(self):
        """Test admin deleting a document"""
        if not self.test_document_id:
            print("❌ No test document to delete")
            return False
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Admin - Delete Document",
            "DELETE",
            f"admin/documents/{self.test_document_id}",
            200
        )
        
        if success:
            print(f"   Document deleted successfully")
            self.test_document_id = None  # Clear the ID since document is deleted
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_user_analytics(self):
        """Test admin-only user analytics endpoint"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Admin - User Analytics", "GET", "admin/analytics/users", 200)
        
        if success:
            print(f"   User analytics retrieved for {len(response)} users")
            # Show sample analytics
            for user_id, analytics in list(response.items())[:2]:
                user_info = analytics.get('user', {})
                print(f"   - {user_info.get('full_name')}: {analytics.get('total_annotations', 0)} annotations")
        
        # Restore original token
        self.token = original_token
        return success

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            # Auto-login after registration
            return self.test_user_login(test_user_data['email'], test_user_data['password'])
        return success

    def test_user_login(self, email, password):
        """Test user login"""
        login_data = {"email": email, "password": password}
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_non_admin_access_denied(self):
        """Test that non-admin users cannot access admin endpoints"""
        if not self.token:
            print("❌ No regular user token available")
            return False
            
        # Try to access admin endpoint with regular user token
        success, response = self.run_test(
            "Non-Admin Access Denied Test",
            "GET",
            "admin/users",
            403  # Expect forbidden
        )
        
        if success:
            print("   ✅ Access properly denied to non-admin user")
        
        return success

    def test_non_admin_upload_denied(self):
        """Test that non-admin users cannot upload documents"""
        if not self.token:
            print("❌ No regular user token available")
            return False
            
        # Create test CSV content
        csv_content = self.create_test_csv().getvalue()
        
        # Create file-like object
        files = {
            'file': ('unauthorized_upload.csv', csv_content, 'text/csv')
        }
        
        success, response = self.run_test(
            "Non-Admin Upload Denied Test",
            "POST",
            "documents/upload",
            403,  # Expect forbidden
            files=files
        )
        
        if success:
            print("   ✅ Upload properly denied to non-admin user")
        
        return success

    def create_test_csv(self):
        """Create a test CSV file with sample medical discharge summaries"""
        csv_content = """patient_id,discharge_summary,notes
1,"Patient is a 45-year-old male with diabetes who was admitted for diabetic ketoacidosis. He reports difficulty affording his insulin medication due to job loss. Lives in a one-bedroom apartment with three family members. Discharge plan includes social work consultation for medication assistance programs.","Financial hardship affecting medication compliance"
2,"67-year-old female with hypertension and COPD. Patient lives alone in a rural area with limited access to healthcare facilities. Nearest pharmacy is 30 miles away. Has high school education and struggles to understand medication instructions. Needs transportation assistance for follow-up appointments.","Geographic and educational barriers to care"
3,"32-year-old mother of two with postpartum depression. Recently moved to new neighborhood and reports feeling isolated. No family support nearby. Concerned about childcare costs affecting ability to attend therapy sessions. Works part-time without health insurance benefits.","Social isolation and economic barriers to mental health care"
"""
        return io.StringIO(csv_content)

    def test_get_documents(self):
        """Test getting all documents"""
        return self.run_test("Get Documents", "GET", "documents", 200)

    def test_get_document_sentences(self):
        """Test getting sentences from a document"""
        if not self.test_document_id:
            print("❌ No test document ID available")
            return False
            
        success, response = self.run_test(
            "Get Document Sentences",
            "GET",
            f"documents/{self.test_document_id}/sentences",
            200
        )
        
        if success and response and len(response) > 0:
            self.test_sentence_id = response[0]['id']
            print(f"   First sentence ID: {self.test_sentence_id}")
            print(f"   First sentence: {response[0]['text'][:100]}...")
        
        return success

    def test_get_tag_structure(self):
        """Test getting the structured tag definitions"""
        return self.run_test("Get Tag Structure", "GET", "tag-structure", 200)

    def test_create_structured_annotation(self):
        """Test creating a structured annotation with new format"""
        if not self.test_sentence_id:
            print("❌ No test sentence ID available")
            return False
            
        # Test structured annotation with multiple tags and valences
        annotation_data = {
            "sentence_id": self.test_sentence_id,
            "tags": [
                {
                    "domain": "Economic Stability",
                    "category": "Employment", 
                    "tag": "Unemployed",
                    "valence": "negative"
                },
                {
                    "domain": "Economic Stability",
                    "category": "Poverty",
                    "tag": "Below Poverty Threshold", 
                    "valence": "negative"
                }
            ],
            "notes": "Patient reports job loss affecting medication access",
            "skipped": False
        }
        
        return self.run_test(
            "Create Structured Annotation",
            "POST",
            "annotations",
            200,
            data=annotation_data
        )

    def test_analytics_overview(self):
        """Test analytics overview endpoint"""
        return self.run_test("Analytics Overview", "GET", "analytics/overview", 200)

    def test_analytics_tag_prevalence(self):
        """Test tag prevalence analytics (updated endpoint)"""
        return self.run_test("Tag Prevalence Analytics", "GET", "analytics/tag-prevalence", 200)

    def test_admin_delete_user_validation(self):
        """Test user deletion validation (cannot delete self)"""
        if not self.admin_user_id:
            print("❌ No admin user ID available")
            return False
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        # Try to delete self - should fail with 400
        success, response = self.run_test(
            "Admin - Delete Self (Should Fail)",
            "DELETE",
            f"admin/users/{self.admin_user_id}",
            400  # Expect bad request
        )
        
        if success:
            print("   ✅ Self-deletion properly prevented")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_delete_nonexistent_user(self):
        """Test deleting non-existent user"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        fake_user_id = "nonexistent-user-id-12345"
        success, response = self.run_test(
            "Admin - Delete Non-existent User",
            "DELETE",
            f"admin/users/{fake_user_id}",
            404  # Expect not found
        )
        
        if success:
            print("   ✅ Non-existent user deletion properly handled")
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_delete_user_with_annotations(self):
        """Test deleting user who has annotations"""
        if not self.created_user_ids:
            print("❌ No created users available for deletion test")
            return False
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        user_id = self.created_user_ids[0]
        
        # Get user info before deletion
        success, user_info = self.run_test(
            "Get User Info Before Deletion",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            user_to_delete = next((u for u in user_info if u['id'] == user_id), None)
            if user_to_delete:
                print(f"   User to delete: {user_to_delete['full_name']} ({user_to_delete['email']})")
        
        # Delete the user
        success, response = self.run_test(
            "Admin - Delete User with Annotations",
            "DELETE",
            f"admin/users/{user_id}",
            200
        )
        
        if success:
            print(f"   ✅ User deleted successfully")
            print(f"   Message: {response.get('message', 'N/A')}")
            print(f"   User name: {response.get('user_name', 'N/A')}")
            print(f"   Annotations deleted: {response.get('annotations_deleted', 0)}")
            
            # Remove from created_user_ids since it's deleted
            if user_id in self.created_user_ids:
                self.created_user_ids.remove(user_id)
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_verify_user_deleted(self):
        """Verify that deleted user no longer appears in user list"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Admin - Verify User List After Deletion",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            print(f"   Current user count: {len(response)}")
            # Check that none of the deleted users appear in the list
            remaining_created_users = [u for u in response if u['id'] in self.created_user_ids]
            if len(remaining_created_users) == 0:
                print("   ✅ Deleted users no longer appear in user list")
            else:
                print(f"   ❌ {len(remaining_created_users)} deleted users still appear in list")
                return False
        
        # Restore original token
        self.token = original_token
        return success

    def test_admin_delete_created_users(self):
        """Clean up by deleting remaining created test users"""
        if not self.created_user_ids:
            print("ℹ️  No test users to clean up")
            return True
            
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        success_count = 0
        for user_id in self.created_user_ids[:]:  # Create a copy to iterate over
            success, response = self.run_test(
                f"Admin - Delete Test User {user_id[:8]}",
                "DELETE",
                f"admin/users/{user_id}",
                200
            )
            if success:
                success_count += 1
                self.created_user_ids.remove(user_id)
        
        print(f"   Cleaned up {success_count} test users")
        
        # Restore original token
        self.token = original_token
        return True

    def run_all_tests(self):
        """Run all API tests including comprehensive admin functionality"""
        print("🚀 Starting SDOH API Tests with Admin Functionality")
        print("=" * 60)
        
        # Basic endpoint tests
        self.test_root_endpoint()
        self.test_domains_endpoint()
        self.test_get_tag_structure()
        
        # === ADMIN FUNCTIONALITY TESTS ===
        print("\n" + "=" * 30 + " ADMIN TESTS " + "=" * 30)
        
        # Admin authentication
        if not self.test_admin_login():
            print("❌ Admin login failed, stopping admin tests")
            return False
            
        self.test_admin_get_current_user()
        
        # Admin user management
        self.test_admin_get_all_users()
        self.test_admin_create_annotator()
        self.test_admin_create_admin()
        self.test_admin_update_user()
        self.test_admin_reactivate_user()
        
        # === USER DELETION TESTS ===
        print("\n" + "=" * 25 + " USER DELETION TESTS " + "=" * 25)
        self.test_admin_delete_user_validation()
        self.test_admin_delete_nonexistent_user()
        self.test_admin_delete_user_with_annotations()
        self.test_admin_verify_user_deleted()
        
        # Admin document management
        self.test_admin_document_upload()
        if self.test_document_id:
            self.test_get_documents()
            self.test_get_document_sentences()
            if self.test_sentence_id:
                self.test_create_structured_annotation()
        
        # Admin analytics
        self.test_admin_user_analytics()
        
        # Admin document deletion
        if self.test_document_id:
            self.test_admin_delete_document()
        
        # === REGULAR USER TESTS ===
        print("\n" + "=" * 25 + " REGULAR USER TESTS " + "=" * 25)
        
        # Regular user authentication
        if not self.test_user_registration():
            print("❌ Registration failed, stopping regular user tests")
        else:
            self.test_get_current_user()
            
            # Test access control
            self.test_non_admin_access_denied()
            self.test_non_admin_upload_denied()
        
        # Analytics tests (available to all users)
        self.test_analytics_overview()
        self.test_analytics_tag_prevalence()
        
        # === CLEANUP ===
        print("\n" + "=" * 30 + " CLEANUP " + "=" * 30)
        self.test_admin_delete_created_users()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = SDOHAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())