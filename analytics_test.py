import requests
import json
import io
import csv
from datetime import datetime

class AnalyticsAPITester:
    def __init__(self, base_url="https://socdetect-app.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.test_document_ids = []
        self.test_sentence_ids = []
        self.test_annotation_ids = []
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None, check_content_type=None):
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
            
            # Check content type if specified
            if success and check_content_type:
                actual_content_type = response.headers.get('content-type', '').lower()
                if check_content_type.lower() not in actual_content_type:
                    print(f"❌ Failed - Expected content-type {check_content_type}, got {actual_content_type}")
                    return False, {}
                else:
                    print(f"   ✅ Content-Type verified: {actual_content_type}")
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Handle different response types
                if check_content_type and 'image/png' in check_content_type:
                    print(f"   Response: PNG image with {len(response.content)} bytes")
                    return True, response.content
                elif response.headers.get('content-type', '').startswith('text/csv'):
                    print(f"   Response: CSV file with {len(response.content)} bytes")
                    return True, response.content
                else:
                    try:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
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
            print(f"   ✅ Admin token obtained")
            return True
        return False

    def setup_user_auth(self):
        """Setup regular user authentication"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"analytics_test_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Analytics Test User {timestamp}"
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
            print(f"   ✅ User token obtained")
            return True
        return False

    def create_test_data(self):
        """Create test data for analytics testing"""
        print("\n📊 Creating test data for analytics...")
        
        # Create two test documents with different project names
        test_documents = [
            {
                'filename': 'analytics_project_a.csv',
                'project_name': 'Analytics Project A',
                'description': 'Test project A for analytics testing',
                'content': """patient_id,discharge_summary,notes
1,"Patient with diabetes and financial hardship affecting medication compliance. Lives in low-income housing.","Economic barriers to healthcare"
2,"Elderly patient with limited transportation to medical appointments. Rural area with poor public transit.","Geographic barriers to care"
3,"Young mother with postpartum depression. Lacks family support and childcare for therapy sessions.","Social isolation affecting mental health"
"""
            },
            {
                'filename': 'analytics_project_b.csv',
                'project_name': 'Analytics Project B',
                'description': 'Test project B for analytics testing',
                'content': """patient_id,discharge_summary,notes
4,"Patient with chronic pain unable to afford specialized care. Insurance coverage limitations.","Economic and healthcare access barriers"
5,"Homeless individual with substance use disorder. Difficulty maintaining consistent healthcare.","Housing instability affecting health"
"""
            }
        ]
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        for doc_data in test_documents:
            files = {
                'file': (doc_data['filename'], doc_data['content'], 'text/csv'),
                'project_name': (None, doc_data['project_name']),
                'description': (None, doc_data['description'])
            }
            
            success, response = self.run_test(
                f"Create Test Document - {doc_data['project_name']}",
                "POST",
                "documents/upload",
                200,
                files=files,
                headers=headers
            )
            
            if success and 'id' in response:
                self.test_document_ids.append(response['id'])
                print(f"   ✅ Created document: {response['id']} with {response.get('total_sentences', 0)} sentences")
        
        return len(self.test_document_ids) > 0

    def create_test_annotations(self):
        """Create some test annotations for analytics"""
        if not self.test_document_ids:
            print("❌ No test documents available for annotations")
            return False
            
        print("\n📝 Creating test annotations...")
        
        # Get sentences from first document
        headers = {'Authorization': f'Bearer {self.user_token}'}
        success, response = self.run_test(
            "Get Sentences for Annotations",
            "GET",
            f"documents/{self.test_document_ids[0]}/sentences",
            200,
            headers=headers
        )
        
        if not success or not response:
            return False
            
        sentences = response[:3]  # Take first 3 sentences
        
        # Create annotations for some sentences
        for i, sentence in enumerate(sentences):
            if i < 2:  # Annotate first 2 sentences
                annotation_data = {
                    "sentence_id": sentence['id'],
                    "tags": [
                        {
                            "domain": "Economic Stability",
                            "category": "Employment",
                            "tag": "Unemployed" if i == 0 else "Employed",
                            "valence": "negative" if i == 0 else "positive"
                        }
                    ],
                    "notes": f"Test annotation {i+1}",
                    "skipped": False
                }
            else:  # Skip the third sentence
                annotation_data = {
                    "sentence_id": sentence['id'],
                    "tags": [],
                    "notes": "Skipped for testing",
                    "skipped": True
                }
            
            success, response = self.run_test(
                f"Create Test Annotation {i+1}",
                "POST",
                "annotations",
                200,
                data=annotation_data,
                headers=headers
            )
            
            if success and 'id' in response:
                self.test_annotation_ids.append(response['id'])
        
        print(f"   ✅ Created {len(self.test_annotation_ids)} test annotations")
        return len(self.test_annotation_ids) > 0

    def test_projects_analytics_no_auth(self):
        """Test /api/analytics/projects without authentication - should fail"""
        return self.run_test(
            "Projects Analytics - No Auth (Should Fail)",
            "GET",
            "analytics/projects",
            401  # Expect unauthorized
        )

    def test_projects_analytics_with_auth(self):
        """Test /api/analytics/projects with authentication"""
        headers = {'Authorization': f'Bearer {self.user_token}'}
        success, response = self.run_test(
            "Projects Analytics - With Auth",
            "GET",
            "analytics/projects",
            200,
            headers=headers
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Returned array with {len(response)} projects")
            
            # Validate structure of each project
            for project in response:
                required_fields = ['project_name', 'documents_count', 'total_sentences', 
                                 'annotated_sentences', 'progress', 'annotators_count', 'last_activity']
                
                missing_fields = [field for field in required_fields if field not in project]
                if missing_fields:
                    print(f"   ❌ Missing fields in project: {missing_fields}")
                    return False
                
                # Validate data types and logic
                if not isinstance(project['documents_count'], int) or project['documents_count'] < 0:
                    print(f"   ❌ Invalid documents_count: {project['documents_count']}")
                    return False
                    
                if not isinstance(project['total_sentences'], int) or project['total_sentences'] < 0:
                    print(f"   ❌ Invalid total_sentences: {project['total_sentences']}")
                    return False
                    
                if not isinstance(project['annotated_sentences'], int) or project['annotated_sentences'] < 0:
                    print(f"   ❌ Invalid annotated_sentences: {project['annotated_sentences']}")
                    return False
                    
                if project['annotated_sentences'] > project['total_sentences']:
                    print(f"   ❌ Annotated sentences ({project['annotated_sentences']}) > total sentences ({project['total_sentences']})")
                    return False
                    
                if not isinstance(project['progress'], (int, float)) or project['progress'] < 0 or project['progress'] > 1:
                    print(f"   ❌ Invalid progress: {project['progress']}")
                    return False
                    
                if not isinstance(project['annotators_count'], int) or project['annotators_count'] < 0:
                    print(f"   ❌ Invalid annotators_count: {project['annotators_count']}")
                    return False
            
            # Show sample project data
            if response:
                sample_project = response[0]
                print(f"   Sample project: {sample_project['project_name']}")
                print(f"   - Documents: {sample_project['documents_count']}")
                print(f"   - Total sentences: {sample_project['total_sentences']}")
                print(f"   - Annotated sentences: {sample_project['annotated_sentences']}")
                print(f"   - Progress: {sample_project['progress']:.2%}")
                print(f"   - Annotators: {sample_project['annotators_count']}")
            
            return True
        
        return False

    def test_projects_chart_no_auth(self):
        """Test /api/analytics/projects-chart without authentication - should fail"""
        return self.run_test(
            "Projects Chart - No Auth (Should Fail)",
            "GET",
            "analytics/projects-chart",
            401  # Expect unauthorized
        )

    def test_projects_chart_with_auth(self):
        """Test /api/analytics/projects-chart with authentication"""
        headers = {'Authorization': f'Bearer {self.user_token}'}
        success, response = self.run_test(
            "Projects Chart - With Auth",
            "GET",
            "analytics/projects-chart",
            200,
            headers=headers,
            check_content_type='image/png'
        )
        
        if success and isinstance(response, bytes):
            # Verify it's a valid PNG by checking PNG signature
            png_signature = b'\x89PNG\r\n\x1a\n'
            if response.startswith(png_signature):
                print(f"   ✅ Valid PNG image returned ({len(response)} bytes)")
                return True
            else:
                print(f"   ❌ Invalid PNG signature")
                return False
        
        return False

    def test_existing_analytics_endpoints(self):
        """Test existing analytics endpoints for regression"""
        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        # Test /api/analytics/enhanced
        success1, response1 = self.run_test(
            "Analytics Enhanced - Regression Test",
            "GET",
            "analytics/enhanced",
            200,
            headers=headers
        )
        
        if success1:
            # Validate enhanced analytics structure
            required_keys = ['per_user', 'sentences_left_overall', 'irr_pairs']
            missing_keys = [key for key in required_keys if key not in response1]
            if missing_keys:
                print(f"   ❌ Missing keys in enhanced analytics: {missing_keys}")
                success1 = False
            else:
                print(f"   ✅ Enhanced analytics structure validated")
        
        # Test /api/analytics/tag-prevalence-chart
        success2, response2 = self.run_test(
            "Tag Prevalence Chart - Regression Test",
            "GET",
            "analytics/tag-prevalence-chart",
            200,
            headers=headers,
            check_content_type='image/png'
        )
        
        if success2 and isinstance(response2, bytes):
            png_signature = b'\x89PNG\r\n\x1a\n'
            if not response2.startswith(png_signature):
                print(f"   ❌ Invalid PNG for tag prevalence chart")
                success2 = False
            else:
                print(f"   ✅ Tag prevalence chart PNG validated")
        
        # Test /api/analytics/valence-chart
        success3, response3 = self.run_test(
            "Valence Chart - Regression Test",
            "GET",
            "analytics/valence-chart",
            200,
            headers=headers,
            check_content_type='image/png'
        )
        
        if success3 and isinstance(response3, bytes):
            png_signature = b'\x89PNG\r\n\x1a\n'
            if not response3.startswith(png_signature):
                print(f"   ❌ Invalid PNG for valence chart")
                success3 = False
            else:
                print(f"   ✅ Valence chart PNG validated")
        
        return success1 and success2 and success3

    def validate_stacked_chart_logic(self):
        """Validate the stacked chart logic: remaining = total - annotated and never negative"""
        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        # Get projects data
        success, projects = self.run_test(
            "Get Projects for Chart Logic Validation",
            "GET",
            "analytics/projects",
            200,
            headers=headers
        )
        
        if not success or not projects:
            return False
        
        print(f"\n🔍 Validating stacked chart logic for {len(projects)} projects...")
        
        for project in projects:
            total = project['total_sentences']
            annotated = project['annotated_sentences']
            remaining = total - annotated
            
            print(f"   Project: {project['project_name']}")
            print(f"   - Total: {total}, Annotated: {annotated}, Remaining: {remaining}")
            
            # Validate remaining is never negative
            if remaining < 0:
                print(f"   ❌ Remaining sentences is negative: {remaining}")
                return False
            
            # Validate progress calculation
            expected_progress = annotated / total if total > 0 else 0.0
            actual_progress = project['progress']
            
            if abs(expected_progress - actual_progress) > 0.001:  # Allow small floating point differences
                print(f"   ❌ Progress calculation error: expected {expected_progress}, got {actual_progress}")
                return False
            
            print(f"   ✅ Chart logic validated for {project['project_name']}")
        
        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        if not self.test_document_ids:
            return True
            
        print("\n🧹 Cleaning up test data...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        cleanup_success = True
        for doc_id in self.test_document_ids:
            success, response = self.run_test(
                f"Cleanup Document {doc_id[:8]}...",
                "DELETE",
                f"admin/documents/{doc_id}",
                200,
                headers=headers
            )
            if not success:
                cleanup_success = False
        
        if cleanup_success:
            print("   ✅ All test data cleaned up successfully")
        
        return cleanup_success

    def run_analytics_tests(self):
        """Run focused analytics endpoint tests"""
        print("🚀 Starting Analytics Endpoint Tests")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_admin_auth():
            print("❌ Admin authentication failed")
            return False
            
        if not self.setup_user_auth():
            print("❌ User authentication failed")
            return False
        
        # Create test data
        if not self.create_test_data():
            print("❌ Failed to create test data")
            return False
        
        # Create some annotations for meaningful analytics
        if not self.create_test_annotations():
            print("❌ Failed to create test annotations")
            return False
        
        print("\n" + "=" * 25 + " NEW ANALYTICS ENDPOINTS " + "=" * 25)
        
        # Test new analytics endpoints
        self.test_projects_analytics_no_auth()
        self.test_projects_analytics_with_auth()
        self.test_projects_chart_no_auth()
        self.test_projects_chart_with_auth()
        
        # Validate chart logic
        self.validate_stacked_chart_logic()
        
        print("\n" + "=" * 25 + " REGRESSION TESTS " + "=" * 25)
        
        # Test existing endpoints for regression
        self.test_existing_analytics_endpoints()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Analytics Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All analytics tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} analytics tests failed")
            return False

def main():
    tester = AnalyticsAPITester()
    success = tester.run_analytics_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())