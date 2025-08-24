import requests
import json
import io
import csv
from datetime import datetime

class AdditionalAPITester:
    def __init__(self, base_url="https://sdoh-tagger.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.test_document_id = None
        self.test_sentence_id = None
        self.test_annotation_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {}
        
        if headers:
            test_headers.update(headers)
        
        if not files and 'Content-Type' not in test_headers:
            test_headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers={k:v for k,v in test_headers.items() if k != 'Content-Type'})
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    if response.headers.get('content-type', '').startswith('text/csv'):
                        print(f"   Response: CSV file with {len(response.content)} bytes")
                        return True, response.content
                    else:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                        return True, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return True, response.text
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
            return True
        return False

    def setup_user_auth(self):
        """Setup regular user authentication"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_additional_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Additional Test User {timestamp}"
        }
        
        # Register user
        success, response = self.run_test(
            "User Registration Setup",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if not success:
            return False
            
        # Login user
        login_data = {"email": user_data['email'], "password": user_data['password']}
        success, response = self.run_test(
            "User Login Setup",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            return True
        return False

    def test_annotation_create_skipped(self):
        """Test creating a skipped annotation"""
        if not self.test_sentence_id:
            print("❌ No test sentence ID available")
            return False
            
        annotation_data = {
            "sentence_id": self.test_sentence_id,
            "tags": [],
            "notes": "Skipped due to unclear content",
            "skipped": True
        }
        
        headers = {'Authorization': f'Bearer {self.user_token}'}
        success, response = self.run_test(
            "Create Skipped Annotation",
            "POST",
            "annotations",
            200,
            data=annotation_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.test_annotation_id = response['id']
            print(f"   Created skipped annotation with ID: {self.test_annotation_id}")
        
        return success

    def test_get_sentence_annotations(self):
        """Test getting annotations for a specific sentence"""
        if not self.test_sentence_id:
            print("❌ No test sentence ID available")
            return False
            
        headers = {'Authorization': f'Bearer {self.user_token}'}
        return self.run_test(
            "Get Sentence Annotations",
            "GET",
            f"annotations/sentence/{self.test_sentence_id}",
            200,
            headers=headers
        )

    def test_delete_annotation(self):
        """Test deleting an annotation"""
        if not self.test_annotation_id:
            print("❌ No test annotation ID available")
            return False
            
        headers = {'Authorization': f'Bearer {self.user_token}'}
        return self.run_test(
            "Delete Annotation",
            "DELETE",
            f"annotations/{self.test_annotation_id}",
            200,
            headers=headers
        )

    def test_admin_download_csv(self):
        """Test admin downloading annotated CSV"""
        if not self.test_document_id:
            print("❌ No test document ID available")
            return False
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        return self.run_test(
            "Admin Download Annotated CSV",
            "GET",
            f"admin/download/annotated-csv/{self.test_document_id}",
            200,
            headers=headers
        )

    def create_test_document(self):
        """Create a test document for testing"""
        csv_content = """patient_id,discharge_summary,notes
1,"Patient is a 55-year-old female with chronic pain who reports difficulty accessing pain management services due to insurance limitations. Lives in rural area with limited transportation options.","Access barriers to specialized care"
2,"28-year-old male with substance use disorder. Recently lost job and housing. Reports feeling isolated from family and community support systems.","Economic instability and social isolation"
"""
        
        files = {
            'file': ('additional_test_document.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Additional Test Project'),
            'description': (None, 'Document for additional endpoint testing')
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Create Test Document",
            "POST",
            "documents/upload",
            200,
            files=files,
            headers=headers
        )
        
        if success and 'id' in response:
            self.test_document_id = response['id']
            print(f"   Created test document with ID: {self.test_document_id}")
            return True
        return False

    def get_test_sentence(self):
        """Get a sentence from the test document"""
        if not self.test_document_id:
            return False
            
        headers = {'Authorization': f'Bearer {self.user_token}'}
        success, response = self.run_test(
            "Get Test Document Sentences",
            "GET",
            f"documents/{self.test_document_id}/sentences",
            200,
            headers=headers
        )
        
        if success and response and len(response) > 0:
            self.test_sentence_id = response[0]['id']
            print(f"   Got test sentence ID: {self.test_sentence_id}")
            return True
        return False

    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = requests.options(f"{self.base_url}/")
            print(f"\n🔍 Testing CORS Headers...")
            print(f"   URL: {self.base_url}/")
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
            # Check if at least some CORS headers are present
            has_cors = any(value is not None for value in cors_headers.values())
            
            if has_cors:
                print("✅ CORS headers are configured")
                self.tests_passed += 1
            else:
                print("❌ No CORS headers found")
            
            self.tests_run += 1
            return has_cors
            
        except Exception as e:
            print(f"❌ CORS test failed: {str(e)}")
            self.tests_run += 1
            return False

    def cleanup_test_document(self):
        """Clean up test document"""
        if not self.test_document_id:
            return True
            
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        success, response = self.run_test(
            "Cleanup Test Document",
            "DELETE",
            f"admin/documents/{self.test_document_id}",
            200,
            headers=headers
        )
        
        if success:
            print("   Test document cleaned up successfully")
        
        return success

    def run_additional_tests(self):
        """Run additional specific tests"""
        print("🚀 Starting Additional Backend API Tests")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_admin_auth():
            print("❌ Admin authentication failed")
            return False
            
        if not self.setup_user_auth():
            print("❌ User authentication failed")
            return False
        
        # Create test document and get sentence
        if not self.create_test_document():
            print("❌ Failed to create test document")
            return False
            
        if not self.get_test_sentence():
            print("❌ Failed to get test sentence")
            return False
        
        # Test specific endpoints
        self.test_annotation_create_skipped()
        self.test_get_sentence_annotations()
        self.test_delete_annotation()
        self.test_admin_download_csv()
        self.test_cors_headers()
        
        # Cleanup
        self.cleanup_test_document()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Additional Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All additional tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} additional tests failed")
            return False

def main():
    tester = AdditionalAPITester()
    success = tester.run_additional_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())