import requests
import sys
import json
import io
import csv
from datetime import datetime

class SDOHAPITester:
    def __init__(self, base_url="https://data-tag-collab.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_document_id = None
        self.test_sentence_id = None

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

    def create_test_csv(self):
        """Create a test CSV file with sample medical discharge summaries"""
        csv_content = """patient_id,discharge_summary,notes
1,"Patient is a 45-year-old male with diabetes who was admitted for diabetic ketoacidosis. He reports difficulty affording his insulin medication due to job loss. Lives in a one-bedroom apartment with three family members. Discharge plan includes social work consultation for medication assistance programs.","Financial hardship affecting medication compliance"
2,"67-year-old female with hypertension and COPD. Patient lives alone in a rural area with limited access to healthcare facilities. Nearest pharmacy is 30 miles away. Has high school education and struggles to understand medication instructions. Needs transportation assistance for follow-up appointments.","Geographic and educational barriers to care"
3,"32-year-old mother of two with postpartum depression. Recently moved to new neighborhood and reports feeling isolated. No family support nearby. Concerned about childcare costs affecting ability to attend therapy sessions. Works part-time without health insurance benefits.","Social isolation and economic barriers to mental health care"
"""
        return io.StringIO(csv_content)

    def test_document_upload(self):
        """Test CSV document upload"""
        # Create test CSV content
        csv_content = self.create_test_csv().getvalue()
        
        # Create file-like object
        files = {
            'file': ('test_discharge_summaries.csv', csv_content, 'text/csv')
        }
        
        success, response = self.run_test(
            "Document Upload",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            self.test_document_id = response['id']
            print(f"   Document ID: {self.test_document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
        
        return success

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

    def test_create_skipped_annotation(self):
        """Test creating a skipped annotation"""
        if not self.test_sentence_id:
            print("❌ No test sentence ID available")
            return False
            
        # Create another sentence for skip test
        success, sentences_response = self.run_test(
            "Get Document Sentences for Skip Test",
            "GET", 
            f"documents/{self.test_document_id}/sentences",
            200
        )
        
        if not success or len(sentences_response) < 2:
            print("❌ Need at least 2 sentences for skip test")
            return False
            
        skip_sentence_id = sentences_response[1]['id']
        
        annotation_data = {
            "sentence_id": skip_sentence_id,
            "tags": [],
            "notes": "No SDOH content found in this sentence",
            "skipped": True
        }
        
        return self.run_test(
            "Create Skipped Annotation",
            "POST",
            "annotations",
            200,
            data=annotation_data
        )

    def test_get_sentence_annotations(self):
        """Test getting annotations for a sentence"""
        if not self.test_sentence_id:
            print("❌ No test sentence ID available")
            return False
            
        return self.run_test(
            "Get Sentence Annotations",
            "GET",
            f"annotations/sentence/{self.test_sentence_id}",
            200
        )

    def test_analytics_overview(self):
        """Test analytics overview endpoint"""
        return self.run_test("Analytics Overview", "GET", "analytics/overview", 200)

    def test_analytics_tag_prevalence(self):
        """Test tag prevalence analytics (updated endpoint)"""
        return self.run_test("Tag Prevalence Analytics", "GET", "analytics/tag-prevalence", 200)

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting SDOH API Tests")
        print("=" * 50)
        
        # Basic endpoint tests
        self.test_root_endpoint()
        self.test_domains_endpoint()
        
        # Authentication tests
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return False
            
        self.test_get_current_user()
        
        # Document management tests
        if not self.test_document_upload():
            print("❌ Document upload failed, stopping document tests")
        else:
            self.test_get_documents()
            
            if not self.test_get_document_sentences():
                print("❌ Getting sentences failed, stopping annotation tests")
            else:
                # Annotation tests
                self.test_create_annotation()
                self.test_get_sentence_annotations()
        
        # Analytics tests
        self.test_analytics_overview()
        self.test_domain_prevalence()
        
        # Print final results
        print("\n" + "=" * 50)
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