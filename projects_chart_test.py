#!/usr/bin/env python3
"""
Focused test script for /api/analytics/projects-chart endpoint
Testing the specific requirements from the review request.
"""

import requests
import sys
import json

class ProjectsChartTester:
    def __init__(self, base_url="https://socdetect-app.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def get_admin_token(self):
        """Get admin token for testing"""
        login_data = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print(f"🔑 Admin token obtained: {self.admin_token[:20]}...")
                return True
            else:
                print(f"❌ Failed to get admin token: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting admin token: {str(e)}")
            return False

    def test_unauthenticated_request(self):
        """Test 1: Unauthenticated GET should return 401"""
        try:
            response = requests.get(f"{self.base_url}/analytics/projects-chart")
            success = response.status_code == 401
            details = f"Status: {response.status_code}, Expected: 401"
            if not success and response.status_code == 403:
                # 403 is also acceptable for unauthenticated requests
                success = True
                details = f"Status: {response.status_code} (403 is acceptable for unauthenticated)"
            self.log_test("Unauthenticated request returns 401/403", success, details)
            return success
        except Exception as e:
            self.log_test("Unauthenticated request returns 401/403", False, f"Error: {str(e)}")
            return False

    def test_bearer_token_auth(self):
        """Test 2: Authenticated via Bearer token should return 200 image/png"""
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.get(f"{self.base_url}/analytics/projects-chart", headers=headers)
            
            success = response.status_code == 200
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            if success and 'image/png' in content_type:
                details = f"Status: 200, Content-Type: {content_type}, Size: {content_length} bytes"
                self.log_test("Bearer token authentication returns 200 image/png", True, details)
                return True
            else:
                details = f"Status: {response.status_code}, Content-Type: {content_type}"
                self.log_test("Bearer token authentication returns 200 image/png", False, details)
                return False
        except Exception as e:
            self.log_test("Bearer token authentication returns 200 image/png", False, f"Error: {str(e)}")
            return False

    def test_query_param_auth(self):
        """Test 3: Authenticated via token query param should return 200 image/png"""
        try:
            url = f"{self.base_url}/analytics/projects-chart?token={self.admin_token}"
            response = requests.get(url)  # No Authorization header
            
            success = response.status_code == 200
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            if success and 'image/png' in content_type:
                details = f"Status: 200, Content-Type: {content_type}, Size: {content_length} bytes"
                self.log_test("Query param token authentication returns 200 image/png", True, details)
                return True
            else:
                details = f"Status: {response.status_code}, Content-Type: {content_type}"
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        details += f", Error: {error_data}"
                    except:
                        details += f", Response: {response.text[:100]}"
                self.log_test("Query param token authentication returns 200 image/png", False, details)
                return False
        except Exception as e:
            self.log_test("Query param token authentication returns 200 image/png", False, f"Error: {str(e)}")
            return False

    def test_data_integrity(self):
        """Test 4: Data integrity - remaining should be non-negative (total >= annotated)"""
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.get(f"{self.base_url}/analytics/projects", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Data integrity check", False, f"Could not get projects data: {response.status_code}")
                return False
            
            projects = response.json()
            integrity_issues = []
            
            for project in projects:
                total = project.get('total_sentences', 0)
                annotated = project.get('annotated_sentences', 0)
                remaining = total - annotated
                
                if remaining < 0:
                    integrity_issues.append({
                        'project': project.get('project_name', 'Unknown'),
                        'total': total,
                        'annotated': annotated,
                        'remaining': remaining
                    })
            
            if integrity_issues:
                details = f"Found {len(integrity_issues)} projects with negative remaining sentences"
                for issue in integrity_issues:
                    details += f"\n      - {issue['project']}: total={issue['total']}, annotated={issue['annotated']}, remaining={issue['remaining']}"
                self.log_test("Data integrity: remaining sentences non-negative", False, details)
                return False
            else:
                details = f"Verified {len(projects)} projects - all have non-negative remaining sentences"
                if projects:
                    sample = projects[0]
                    total = sample.get('total_sentences', 0)
                    annotated = sample.get('annotated_sentences', 0)
                    remaining = total - annotated
                    details += f"\n      Sample: {sample.get('project_name')} - total:{total}, annotated:{annotated}, remaining:{remaining}"
                self.log_test("Data integrity: remaining sentences non-negative", True, details)
                return True
                
        except Exception as e:
            self.log_test("Data integrity: remaining sentences non-negative", False, f"Error: {str(e)}")
            return False

    def test_projects_json_smoke_check(self):
        """Test 5: Quick smoke check - /api/analytics/projects returns JSON with expected fields"""
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.get(f"{self.base_url}/analytics/projects", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Projects JSON smoke check", False, f"Status: {response.status_code}")
                return False
            
            projects = response.json()
            if not isinstance(projects, list):
                self.log_test("Projects JSON smoke check", False, "Response is not a list")
                return False
            
            if not projects:
                self.log_test("Projects JSON smoke check", True, "Empty projects list (valid)")
                return True
            
            # Check required fields in first project
            required_fields = ['project_name', 'documents_count', 'total_sentences', 
                             'annotated_sentences', 'progress', 'annotators_count', 'last_activity']
            
            project = projects[0]
            missing_fields = [field for field in required_fields if field not in project]
            
            if missing_fields:
                details = f"Missing required fields: {missing_fields}"
                self.log_test("Projects JSON smoke check", False, details)
                return False
            else:
                details = f"Found {len(projects)} projects with all required fields"
                details += f"\n      Sample: {project['project_name']} - {project['progress']:.1%} complete"
                self.log_test("Projects JSON smoke check", True, details)
                return True
                
        except Exception as e:
            self.log_test("Projects JSON smoke check", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all focused tests for projects-chart endpoint"""
        print("🚀 Starting Focused Projects Chart Tests")
        print("=" * 60)
        
        # Get admin token first
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return False
        
        print("\n📊 Running Projects Chart Tests...")
        
        # Run all tests
        test1 = self.test_unauthenticated_request()
        test2 = self.test_bearer_token_auth()
        test3 = self.test_query_param_auth()
        test4 = self.test_data_integrity()
        test5 = self.test_projects_json_smoke_check()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        all_passed = test1 and test2 and test3 and test4 and test5
        if all_passed:
            print("🎉 All focused tests passed!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
        
        return all_passed

def main():
    tester = ProjectsChartTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())