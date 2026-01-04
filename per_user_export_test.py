import requests
import sys
import json
import io
import csv
from datetime import datetime

class PerUserExportTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.admin_user_id = None
        self.regular_user_id = None
        self.test_document_id = None
        self.test_sentence_ids = []
        self.tests_run = 0
        self.tests_passed = 0
        self.created_annotation_ids = []

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
                
                # Handle different response types
                if 'text/csv' in response.headers.get('content-type', ''):
                    print(f"   CSV Response - Size: {len(response.content)} bytes")
                    print(f"   Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
                    return True, response.content
                elif 'image/png' in response.headers.get('content-type', ''):
                    print(f"   PNG Response - Size: {len(response.content)} bytes")
                    return True, response.content
                else:
                    try:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                        return True, response_data
                    except:
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
        """Login as admin user"""
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
            
            # Get admin user info
            success, user_info = self.run_test(
                "Get Admin User Info",
                "GET",
                "auth/me",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                self.admin_user_id = user_info.get('id')
                print(f"   Admin user ID: {self.admin_user_id}")
            
            return True
        return False

    def setup_regular_user(self):
        """Create and login as regular user"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_annotator_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test Annotator {timestamp}"
        }
        
        success, response = self.run_test(
            "Create Regular User",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.regular_user_id = response['id']
            
            # Login as the new user
            login_data = {"email": user_data['email'], "password": user_data['password']}
            success, login_response = self.run_test(
                "Regular User Login",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success and 'access_token' in login_response:
                self.user_token = login_response['access_token']
                print(f"   Regular user ID: {self.regular_user_id}")
                return True
        
        return False

    def create_test_document(self):
        """Create a test document with sample data"""
        csv_content = """patient_id,discharge_summary
P001,"Patient is a 45-year-old male with diabetes who was admitted for diabetic ketoacidosis. He reports difficulty affording his insulin medication due to job loss. Lives in a one-bedroom apartment with three family members."
P002,"67-year-old female with hypertension and COPD. Patient lives alone in a rural area with limited access to healthcare facilities. Nearest pharmacy is 30 miles away."
P003,"32-year-old mother of two with postpartum depression. Recently moved to new neighborhood and reports feeling isolated. No family support nearby."
"""
        
        files = {
            'file': ('test_export_document.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Export Test Project'),
            'description': (None, 'Test document for per-user export functionality')
        }
        
        success, response = self.run_test(
            "Create Test Document",
            "POST",
            "documents/upload",
            200,
            files=files,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and 'id' in response:
            self.test_document_id = response['id']
            print(f"   Document ID: {self.test_document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
            
            # Get sentences for annotation testing
            success, sentences = self.run_test(
                "Get Document Sentences",
                "GET",
                f"documents/{self.test_document_id}/sentences",
                200,
                headers={'Authorization': f'Bearer {self.user_token}'}
            )
            
            if success and sentences:
                self.test_sentence_ids = [s['id'] for s in sentences[:3]]  # Use first 3 sentences
                print(f"   Got {len(self.test_sentence_ids)} sentence IDs for testing")
            
            return True
        
        return False

    def create_test_annotations(self):
        """Create test annotations with both admin and regular user"""
        if not self.test_sentence_ids:
            print("❌ No sentence IDs available for annotation")
            return False
        
        # Create annotations as regular user
        for i, sentence_id in enumerate(self.test_sentence_ids):
            if i == 0:
                # Tagged annotation with confidence and duration
                annotation_data = {
                    "sentence_id": sentence_id,
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
                    "skipped": False,
                    "confidence": 4,
                    "duration_ms": 15000
                }
            elif i == 1:
                # Skipped annotation with confidence and duration
                annotation_data = {
                    "sentence_id": sentence_id,
                    "tags": [],
                    "notes": "Insufficient information to determine SDOH factors",
                    "skipped": True,
                    "confidence": 2,
                    "duration_ms": 8000
                }
            else:
                # Another tagged annotation
                annotation_data = {
                    "sentence_id": sentence_id,
                    "tags": [
                        {
                            "domain": "Social and Community Context",
                            "category": "Social Cohesion",
                            "tag": "Social Isolation",
                            "valence": "negative"
                        }
                    ],
                    "notes": "Patient reports feeling isolated in new neighborhood",
                    "skipped": False,
                    "confidence": 5,
                    "duration_ms": 12000
                }
            
            success, response = self.run_test(
                f"Create Annotation {i+1} (Regular User)",
                "POST",
                "annotations",
                200,
                data=annotation_data,
                headers={'Authorization': f'Bearer {self.user_token}'}
            )
            
            if success and 'id' in response:
                self.created_annotation_ids.append(response['id'])
        
        # Create one annotation as admin user for comparison
        if self.test_sentence_ids:
            admin_annotation = {
                "sentence_id": self.test_sentence_ids[0],  # Same sentence as first user annotation
                "tags": [
                    {
                        "domain": "Health Care Access and Quality",
                        "category": "Access to Primary Care",
                        "tag": "Geographic Barriers to Care",
                        "valence": "negative"
                    }
                ],
                "notes": "Rural location creates access barriers",
                "skipped": False,
                "confidence": 3,
                "duration_ms": 10000
            }
            
            success, response = self.run_test(
                "Create Admin Annotation",
                "POST",
                "annotations",
                200,
                data=admin_annotation,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
        
        print(f"   Created {len(self.created_annotation_ids)} annotations for testing")
        return len(self.created_annotation_ids) > 0

    def test_per_user_csv_export_auth(self):
        """Test per-user CSV export authentication"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        # Test without authentication - should fail
        success, _ = self.run_test(
            "Per-User CSV Export - No Auth (should fail)",
            "GET",
            f"download/my-annotations-csv/{self.test_document_id}",
            401
        )
        
        return success

    def test_per_user_csv_export_regular_user(self):
        """Test per-user CSV export as regular user"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        success, csv_content = self.run_test(
            "Per-User CSV Export - Regular User",
            "GET",
            f"download/my-annotations-csv/{self.test_document_id}",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        if success and csv_content:
            # Parse CSV and validate content
            csv_text = csv_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            
            print(f"   CSV contains {len(rows)} rows")
            
            # Check required columns
            expected_columns = [
                "document_id", "sentence_id", "subject_id", "row_index", 
                "sentence_index", "sentence_text", "tag_domain", "tag_category", 
                "tag", "valence", "notes", "is_skipped", "confidence", "duration_ms"
            ]
            
            if rows:
                actual_columns = list(rows[0].keys())
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                
                if missing_columns:
                    print(f"   ❌ Missing columns: {missing_columns}")
                    return False
                else:
                    print(f"   ✅ All required columns present")
                
                # Check for confidence and duration_ms values
                confidence_found = any(row.get('confidence') for row in rows)
                duration_found = any(row.get('duration_ms') for row in rows)
                
                print(f"   Confidence values found: {confidence_found}")
                print(f"   Duration values found: {duration_found}")
                
                # Verify only current user's annotations are included
                # (This is implicit since we're using the user's token)
                tagged_rows = [row for row in rows if row.get('is_skipped') == 'False' and row.get('tag_domain')]
                skipped_rows = [row for row in rows if row.get('is_skipped') == 'True']
                
                print(f"   Tagged annotations: {len(tagged_rows)}")
                print(f"   Skipped annotations: {len(skipped_rows)}")
                
                return True
        
        return False

    def test_per_user_csv_export_admin(self):
        """Test per-user CSV export as admin user"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        success, csv_content = self.run_test(
            "Per-User CSV Export - Admin User",
            "GET",
            f"download/my-annotations-csv/{self.test_document_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and csv_content:
            csv_text = csv_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            
            print(f"   Admin CSV contains {len(rows)} rows")
            
            # Admin should only see their own annotations
            admin_tagged_rows = [row for row in rows if row.get('is_skipped') == 'False' and row.get('tag_domain')]
            print(f"   Admin tagged annotations: {len(admin_tagged_rows)}")
            
            return True
        
        return False

    def test_per_user_paragraph_export_auth(self):
        """Test per-user paragraph export authentication"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        # Test without authentication - should fail
        success, _ = self.run_test(
            "Per-User Paragraph Export - No Auth (should fail)",
            "GET",
            f"download/my-annotated-paragraphs/{self.test_document_id}",
            401
        )
        
        return success

    def test_per_user_paragraph_export_regular_user(self):
        """Test per-user paragraph export as regular user"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        success, csv_content = self.run_test(
            "Per-User Paragraph Export - Regular User",
            "GET",
            f"download/my-annotated-paragraphs/{self.test_document_id}",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        if success and csv_content:
            csv_text = csv_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            
            print(f"   Paragraph CSV contains {len(rows)} rows")
            
            # Check required columns
            expected_columns = ["row_index", "subject_id", "annotated_paragraph_text"]
            
            if rows:
                actual_columns = list(rows[0].keys())
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                
                if missing_columns:
                    print(f"   ❌ Missing columns: {missing_columns}")
                    return False
                else:
                    print(f"   ✅ All required columns present")
                
                # Check for inline tags in paragraph text
                tagged_paragraphs = 0
                for row in rows:
                    paragraph_text = row.get('annotated_paragraph_text', '')
                    if '[Tags:' in paragraph_text:
                        tagged_paragraphs += 1
                        print(f"   Sample tagged paragraph: {paragraph_text[:100]}...")
                
                print(f"   Paragraphs with inline tags: {tagged_paragraphs}")
                
                return True
        
        return False

    def test_admin_csv_export_with_confidence_duration(self):
        """Test updated admin CSV export with confidence and duration columns"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        success, csv_content = self.run_test(
            "Admin CSV Export with Confidence/Duration",
            "GET",
            f"admin/download/annotated-csv-inline/{self.test_document_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and csv_content:
            csv_text = csv_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            
            print(f"   Admin CSV contains {len(rows)} rows")
            
            # Check for new columns
            expected_columns = [
                "document_id", "sentence_id", "subject_id", "row_index", 
                "sentence_index", "sentence_text", "tag_domain", "tag_category", 
                "tag", "valence", "notes", "user_id", "user_display", 
                "is_skipped", "confidence", "duration_ms"
            ]
            
            if rows:
                actual_columns = list(rows[0].keys())
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                
                if missing_columns:
                    print(f"   ❌ Missing columns: {missing_columns}")
                    return False
                else:
                    print(f"   ✅ All required columns present including confidence and duration_ms")
                
                # Check for confidence and duration values
                confidence_values = [row.get('confidence') for row in rows if row.get('confidence')]
                duration_values = [row.get('duration_ms') for row in rows if row.get('duration_ms')]
                
                print(f"   Rows with confidence values: {len(confidence_values)}")
                print(f"   Rows with duration values: {len(duration_values)}")
                
                # Check that both admin and user annotations are included
                user_ids = set(row.get('user_id') for row in rows if row.get('user_id'))
                print(f"   Unique annotators in export: {len(user_ids)}")
                
                return True
        
        return False

    def test_admin_csv_export_with_user_filter(self):
        """Test admin CSV export with user_id filter"""
        if not self.test_document_id or not self.regular_user_id:
            print("❌ No test document or user ID available")
            return False
        
        success, csv_content = self.run_test(
            "Admin CSV Export with User Filter",
            "GET",
            f"admin/download/annotated-csv-inline/{self.test_document_id}?user_id={self.regular_user_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and csv_content:
            csv_text = csv_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
            
            print(f"   Filtered CSV contains {len(rows)} rows")
            
            # Verify only the specified user's annotations are included
            user_ids = set(row.get('user_id') for row in rows if row.get('user_id'))
            
            if len(user_ids) <= 1 and (not user_ids or self.regular_user_id in user_ids):
                print(f"   ✅ Filter working correctly - only specified user's annotations")
                return True
            else:
                print(f"   ❌ Filter not working - found annotations from {len(user_ids)} users")
                return False
        
        return False

    def test_admin_csv_export_auth_enforcement(self):
        """Test that admin CSV export requires admin role"""
        if not self.test_document_id:
            print("❌ No test document available")
            return False
        
        # Test with regular user token - should fail
        success, _ = self.run_test(
            "Admin CSV Export - Regular User (should fail)",
            "GET",
            f"admin/download/annotated-csv-inline/{self.test_document_id}",
            403,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        return success

    def test_nonexistent_document_handling(self):
        """Test handling of non-existent document IDs"""
        fake_doc_id = "nonexistent-document-12345"
        
        # Test per-user CSV export
        success1, _ = self.run_test(
            "Per-User CSV Export - Non-existent Document",
            "GET",
            f"download/my-annotations-csv/{fake_doc_id}",
            404,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        # Test per-user paragraph export
        success2, _ = self.run_test(
            "Per-User Paragraph Export - Non-existent Document",
            "GET",
            f"download/my-annotated-paragraphs/{fake_doc_id}",
            404,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        # Test admin CSV export
        success3, _ = self.run_test(
            "Admin CSV Export - Non-existent Document",
            "GET",
            f"admin/download/annotated-csv-inline/{fake_doc_id}",
            404,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        return success1 and success2 and success3

    def cleanup_test_data(self):
        """Clean up test data"""
        # Delete test document
        if self.test_document_id:
            success, _ = self.run_test(
                "Cleanup - Delete Test Document",
                "DELETE",
                f"admin/documents/{self.test_document_id}",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print("   ✅ Test document deleted")
        
        # Delete test user
        if self.regular_user_id:
            success, _ = self.run_test(
                "Cleanup - Delete Test User",
                "DELETE",
                f"admin/users/{self.regular_user_id}",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print("   ✅ Test user deleted")

    def run_all_tests(self):
        """Run all per-user export tests"""
        print("🚀 Starting Per-User Annotation Export Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_auth():
            print("❌ Admin authentication failed")
            return False
        
        if not self.setup_regular_user():
            print("❌ Regular user setup failed")
            return False
        
        if not self.create_test_document():
            print("❌ Test document creation failed")
            return False
        
        if not self.create_test_annotations():
            print("❌ Test annotation creation failed")
            return False
        
        # Run export tests
        print("\n" + "=" * 25 + " PER-USER EXPORT TESTS " + "=" * 25)
        
        # Per-user CSV export tests
        self.test_per_user_csv_export_auth()
        self.test_per_user_csv_export_regular_user()
        self.test_per_user_csv_export_admin()
        
        # Per-user paragraph export tests
        self.test_per_user_paragraph_export_auth()
        self.test_per_user_paragraph_export_regular_user()
        
        # Admin CSV export with new columns
        self.test_admin_csv_export_with_confidence_duration()
        self.test_admin_csv_export_with_user_filter()
        self.test_admin_csv_export_auth_enforcement()
        
        # Error handling tests
        self.test_nonexistent_document_handling()
        
        # Cleanup
        print("\n" + "=" * 30 + " CLEANUP " + "=" * 30)
        self.cleanup_test_data()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All per-user export tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = PerUserExportTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())