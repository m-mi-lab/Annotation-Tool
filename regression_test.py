import requests
import sys
import json
import io
import csv
from datetime import datetime

class RegressionTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.admin_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_document_id = None
        self.test_sentence_id = None
        self.test_annotation_id = None
        self.test_message_id = None
        self.failures = []

    def log_failure(self, test_name, reason):
        """Log a test failure"""
        self.failures.append(f"{test_name}: {reason}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers_override=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = headers_override or {}
        
        if self.token and not headers_override:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files and 'Content-Type' not in headers:
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
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    self.log_failure(name, f"Status {response.status_code}: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                    self.log_failure(name, f"Status {response.status_code}: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.log_failure(name, f"Exception: {str(e)}")
            return False, {}

    def setup_admin_auth(self):
        """Setup admin authentication"""
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login Setup",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            
            # Get admin user info
            original_token = self.token
            self.token = self.admin_token
            success, user_response = self.run_test("Get Admin User Info", "GET", "auth/me", 200)
            if success:
                self.admin_user_id = user_response.get('id')
            self.token = original_token
            return True
        return False

    def setup_regular_user(self):
        """Setup regular user authentication"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user_data = {
            "email": f"regression_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Regression Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration Setup",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            # Login
            login_data = {"email": test_user_data['email'], "password": test_user_data['password']}
            success, login_response = self.run_test(
                "User Login Setup",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success and 'access_token' in login_response:
                self.token = login_response['access_token']
                return True
        return False

    def create_test_csv_with_subject_id(self):
        """Create a test CSV file with note_id and text columns"""
        csv_content = """note_id,patient_id,text,discharge_summary
NOTE001,PAT001,"Patient is a 45-year-old male with diabetes who was admitted for diabetic ketoacidosis. He reports difficulty affording his insulin medication due to job loss.","Financial hardship affecting medication compliance"
NOTE002,PAT002,"67-year-old female with hypertension and COPD. Patient lives alone in a rural area with limited access to healthcare facilities.","Geographic barriers to care"
NOTE003,PAT003,"32-year-old mother of two with postpartum depression. Recently moved to new neighborhood and reports feeling isolated.","Social isolation and economic barriers"
"""
        return io.StringIO(csv_content)

    def test_csv_upload_with_subject_id(self):
        """Test CSV upload with note_id and text columns, ensure sentences store subject_id"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        # Create test CSV content with note_id
        csv_content = self.create_test_csv_with_subject_id().getvalue()
        
        files = {
            'file': ('regression_test_with_note_id.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Regression Test Project'),
            'description': (None, 'Testing CSV upload with note_id and subject_id storage')
        }
        
        success, response = self.run_test(
            "CSV Upload with note_id",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            self.test_document_id = response['id']
            print(f"   Document ID: {self.test_document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
        
        # Restore original token
        self.token = original_token
        return success

    def test_sentences_return_subject_id(self):
        """Test GET /api/documents/{id}/sentences returns subject_id"""
        if not self.test_document_id:
            self.log_failure("Sentences Subject ID Test", "No test document available")
            return False
            
        success, response = self.run_test(
            "Get Document Sentences with subject_id",
            "GET",
            f"documents/{self.test_document_id}/sentences",
            200
        )
        
        if success and response and len(response) > 0:
            # Check if sentences have subject_id
            first_sentence = response[0]
            if 'subject_id' in first_sentence:
                subject_id = first_sentence.get('subject_id')
                print(f"   ✅ First sentence has subject_id: {subject_id}")
                self.test_sentence_id = first_sentence['id']
                
                # Check multiple sentences for subject_id
                sentences_with_subject = [s for s in response if s.get('subject_id')]
                print(f"   ✅ {len(sentences_with_subject)}/{len(response)} sentences have subject_id")
                return True
            else:
                self.log_failure("Sentences Subject ID Test", "Sentences missing subject_id field")
                return False
        else:
            self.log_failure("Sentences Subject ID Test", "No sentences returned")
            return False

    def test_analytics_enhanced(self):
        """Test /api/analytics/enhanced returns per_user, sentences_left_overall, irr_pairs"""
        success, response = self.run_test(
            "Analytics Enhanced Endpoint",
            "GET",
            "analytics/enhanced",
            200
        )
        
        if success and response:
            # Check required fields
            required_fields = ['per_user', 'sentences_left_overall', 'irr_pairs']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ All required fields present: {required_fields}")
                print(f"   - per_user: {len(response.get('per_user', []))} users")
                print(f"   - sentences_left_overall: {response.get('sentences_left_overall')}")
                print(f"   - irr_pairs: {len(response.get('irr_pairs', []))} pairs")
                
                # Validate per_user structure
                if response.get('per_user'):
                    first_user = response['per_user'][0]
                    user_fields = ['user_id', 'full_name', 'total', 'tagged', 'skipped', 'sentences_left']
                    user_missing = [field for field in user_fields if field not in first_user]
                    if not user_missing:
                        print(f"   ✅ per_user structure correct")
                    else:
                        self.log_failure("Analytics Enhanced", f"per_user missing fields: {user_missing}")
                        return False
                
                return True
            else:
                self.log_failure("Analytics Enhanced", f"Missing required fields: {missing_fields}")
                return False
        else:
            self.log_failure("Analytics Enhanced", "No response data")
            return False

    def test_messages_list(self):
        """Test /api/messages list endpoint"""
        success, response = self.run_test(
            "Messages List",
            "GET",
            "messages",
            200
        )
        
        if success:
            print(f"   ✅ Messages list returned {len(response) if response else 0} messages")
            return True
        return False

    def test_messages_post(self):
        """Test /api/messages post endpoint"""
        message_data = {
            "content": "This is a regression test message"
        }
        
        success, response = self.run_test(
            "Messages Post",
            "POST",
            "messages",
            200,
            data=message_data
        )
        
        if success and 'id' in response:
            self.test_message_id = response['id']
            print(f"   ✅ Message created with ID: {self.test_message_id}")
            print(f"   Content: {response.get('content')}")
            print(f"   User: {response.get('user_name')}")
            return True
        return False

    def test_messages_delete_own(self):
        """Test /api/messages delete own message"""
        if not self.test_message_id:
            self.log_failure("Messages Delete Own", "No test message available")
            return False
            
        success, response = self.run_test(
            "Messages Delete Own",
            "DELETE",
            f"messages/{self.test_message_id}",
            200
        )
        
        if success:
            print(f"   ✅ Own message deleted successfully")
            return True
        return False

    def test_messages_delete_admin_can_delete_any(self):
        """Test admin can delete any message"""
        # First create a message as regular user
        message_data = {"content": "Message to be deleted by admin"}
        success, response = self.run_test(
            "Create Message for Admin Delete Test",
            "POST",
            "messages",
            200,
            data=message_data
        )
        
        if not success or 'id' not in response:
            self.log_failure("Messages Admin Delete", "Could not create test message")
            return False
            
        message_id = response['id']
        
        # Switch to admin token and delete the message
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Messages Delete by Admin",
            "DELETE",
            f"messages/{message_id}",
            200
        )
        
        # Restore original token
        self.token = original_token
        
        if success:
            print(f"   ✅ Admin successfully deleted user's message")
            return True
        return False

    def test_change_password_valid(self):
        """Test /api/auth/change-password with valid current password"""
        change_data = {
            "current_password": "TestPass123!",
            "new_password": "NewTestPass456!"
        }
        
        success, response = self.run_test(
            "Change Password Valid",
            "POST",
            "auth/change-password",
            200,
            data=change_data
        )
        
        if success:
            print(f"   ✅ Password changed successfully")
            # Change it back for other tests
            change_back_data = {
                "current_password": "NewTestPass456!",
                "new_password": "TestPass123!"
            }
            self.run_test(
                "Change Password Back",
                "POST",
                "auth/change-password",
                200,
                data=change_back_data
            )
            return True
        return False

    def test_change_password_invalid_current(self):
        """Test /api/auth/change-password blocks invalid current password"""
        change_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewTestPass456!"
        }
        
        success, response = self.run_test(
            "Change Password Invalid Current",
            "POST",
            "auth/change-password",
            400,  # Expect bad request
            data=change_data
        )
        
        if success:
            print(f"   ✅ Invalid current password properly blocked")
            return True
        return False

    def test_update_profile(self):
        """Test /api/auth/me/profile updates full_name"""
        profile_data = {
            "full_name": "Updated Regression Test User"
        }
        
        success, response = self.run_test(
            "Update Profile",
            "PUT",
            "auth/me/profile",
            200,
            data=profile_data
        )
        
        if success and response.get('full_name') == profile_data['full_name']:
            print(f"   ✅ Profile updated successfully: {response.get('full_name')}")
            return True
        else:
            self.log_failure("Update Profile", f"Name not updated correctly. Got: {response.get('full_name')}")
            return False

    def test_existing_endpoints(self):
        """Test existing endpoints still work"""
        endpoints_to_test = [
            ("Analytics Overview", "GET", "analytics/overview", 200),
            ("Tag Prevalence", "GET", "analytics/tag-prevalence", 200),
            ("Documents List", "GET", "documents", 200),
            ("Tag Structure", "GET", "tag-structure", 200),
        ]
        
        all_passed = True
        for name, method, endpoint, expected_status in endpoints_to_test:
            success, response = self.run_test(name, method, endpoint, expected_status)
            if not success:
                all_passed = False
        
        return all_passed

    def test_bulk_delete_endpoints(self):
        """Test bulk delete endpoints still work"""
        # Use admin token
        original_token = self.token
        self.token = self.admin_token
        
        # Test bulk delete annotations (empty list should work)
        success1, response1 = self.run_test(
            "Bulk Delete Annotations",
            "POST",
            "annotations/bulk-delete",
            200,
            data={"annotation_ids": []}
        )
        
        # Test bulk delete users (empty list should work)
        success2, response2 = self.run_test(
            "Bulk Delete Users",
            "POST",
            "admin/users/bulk-delete",
            200,
            data={"user_ids": []}
        )
        
        # Test bulk delete documents (empty list should work)
        success3, response3 = self.run_test(
            "Bulk Delete Documents",
            "POST",
            "admin/documents/bulk-delete",
            200,
            data={"document_ids": []}
        )
        
        # Restore original token
        self.token = original_token
        
        return success1 and success2 and success3

    def cleanup(self):
        """Clean up test data"""
        # Delete test document if created
        if self.test_document_id:
            original_token = self.token
            self.token = self.admin_token
            self.run_test(
                "Cleanup - Delete Test Document",
                "DELETE",
                f"admin/documents/{self.test_document_id}",
                200
            )
            self.token = original_token

    def run_regression_tests(self):
        """Run all regression tests"""
        print("🚀 Starting Backend Regression Tests")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_admin_auth():
            print("❌ Admin authentication failed, stopping tests")
            return False
            
        if not self.setup_regular_user():
            print("❌ Regular user setup failed, stopping tests")
            return False
        
        print("\n" + "=" * 20 + " REGRESSION TESTS " + "=" * 20)
        
        # Test 1: CSV upload with subject_id
        print("\n📋 Testing CSV upload with note_id and subject_id storage...")
        self.test_csv_upload_with_subject_id()
        self.test_sentences_return_subject_id()
        
        # Test 2: Enhanced analytics
        print("\n📊 Testing enhanced analytics endpoint...")
        self.test_analytics_enhanced()
        
        # Test 3: Messages RBAC
        print("\n💬 Testing messages endpoints with RBAC...")
        self.test_messages_list()
        self.test_messages_post()
        self.test_messages_delete_own()
        self.test_messages_delete_admin_can_delete_any()
        
        # Test 4: Password change
        print("\n🔐 Testing password change functionality...")
        self.test_change_password_valid()
        self.test_change_password_invalid_current()
        
        # Test 5: Profile update
        print("\n👤 Testing profile update...")
        self.test_update_profile()
        
        # Test 6: Existing endpoints
        print("\n🔄 Testing existing endpoints still work...")
        self.test_existing_endpoints()
        self.test_bulk_delete_endpoints()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        self.cleanup()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Regression Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failures:
            print(f"\n❌ FAILURES ({len(self.failures)}):")
            for failure in self.failures:
                print(f"   - {failure}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All regression tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} regression tests failed")
            return False

def main():
    tester = RegressionTester()
    success = tester.run_regression_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())