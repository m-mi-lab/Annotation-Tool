#!/usr/bin/env python3
"""
Focused test script for Word Document Preview functionality
Tests all requirements from the review request
"""

import requests
import sys
import json
import io

class WordPreviewTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_word_resource_id = None
        self.test_pdf_resource_id = None
        self.test_image_resource_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {}
        
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if headers:
            test_headers.update(headers)
        
        if not files and method in ['POST', 'PUT']:
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

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return True, response
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text[:200]}")
                return False, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def admin_login(self):
        """Login as admin"""
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
        
        if success:
            response_data = response.json()
            if 'access_token' in response_data:
                self.admin_token = response_data['access_token']
                print(f"   Admin token obtained successfully")
                return True
        return False

    def create_test_docx_file(self):
        """Create a test .docx file"""
        # Minimal DOCX structure for testing
        docx_content = b'PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00'
        return docx_content

    def create_test_pdf_file(self):
        """Create a simple test PDF file"""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
204
%%EOF"""
        return pdf_content

    def create_test_image_file(self):
        """Create a simple test image file (PNG)"""
        # Minimal PNG header
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        return png_content

    def upload_test_files(self):
        """Upload test files for preview testing"""
        print("\n" + "=" * 50)
        print("UPLOADING TEST FILES")
        print("=" * 50)
        
        # Upload Word document
        docx_content = self.create_test_docx_file()
        files = {
            'file': ('test_document.docx', docx_content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        success, response = self.run_test(
            "Upload Word Document",
            "POST",
            "admin/resources/upload",
            200,
            files=files
        )
        
        if success:
            response_data = response.json()
            self.test_word_resource_id = response_data['id']
            print(f"   Word document uploaded with ID: {self.test_word_resource_id}")
        
        # Upload PDF document
        pdf_content = self.create_test_pdf_file()
        files = {
            'file': ('test_document.pdf', pdf_content, 'application/pdf')
        }
        
        success, response = self.run_test(
            "Upload PDF Document",
            "POST",
            "admin/resources/upload",
            200,
            files=files
        )
        
        if success:
            response_data = response.json()
            self.test_pdf_resource_id = response_data['id']
            print(f"   PDF document uploaded with ID: {self.test_pdf_resource_id}")
        
        # Upload Image file
        image_content = self.create_test_image_file()
        files = {
            'file': ('test_image.png', image_content, 'image/png')
        }
        
        success, response = self.run_test(
            "Upload Image File",
            "POST",
            "admin/resources/upload",
            200,
            files=files
        )
        
        if success:
            response_data = response.json()
            self.test_image_resource_id = response_data['id']
            print(f"   Image file uploaded with ID: {self.test_image_resource_id}")

    def test_word_document_preview(self):
        """Test Word document preview endpoint with authentication"""
        if not self.test_word_resource_id:
            print("❌ No Word document resource ID available")
            return False
        
        success, response = self.run_test(
            "Word Document Preview (Authenticated)",
            "GET",
            f"resources/{self.test_word_resource_id}/preview",
            200
        )
        
        if success:
            content_type = response.headers.get('content-type', '')
            content = response.text
            
            # Verify it's HTML content
            if 'text/html' in content_type:
                print(f"   ✅ Content-Type: {content_type}")
                
                # Check for HTML structure and styling
                html_checks = [
                    ('<!DOCTYPE html>' in content, 'DOCTYPE declaration'),
                    ('<html>' in content, 'HTML tag'),
                    ('<head>' in content, 'HEAD section'),
                    ('<body>' in content, 'BODY section'),
                    ('font-family:' in content, 'CSS styling for body'),
                    ('margin:' in content, 'CSS styling for paragraphs'),
                    ('border-collapse:' in content, 'CSS styling for tables'),
                    ('background-color:' in content, 'CSS styling for table headers')
                ]
                
                passed_checks = 0
                for check, description in html_checks:
                    if check:
                        passed_checks += 1
                        print(f"      ✅ {description}")
                    else:
                        print(f"      ❌ {description}")
                
                print(f"   HTML validation: {passed_checks}/{len(html_checks)} checks passed")
                print(f"   Content preview: {content[:200]}...")
                
                return passed_checks >= 6  # Require most checks to pass
            else:
                print(f"   ❌ Wrong content type: {content_type}")
                return False
        
        return False

    def test_authentication_required(self):
        """Test that authentication is required"""
        if not self.test_word_resource_id:
            print("❌ No Word document resource ID available")
            return False
        
        # Remove token for unauthenticated request
        original_token = self.admin_token
        self.admin_token = None
        
        success, response = self.run_test(
            "Word Preview Without Authentication",
            "GET",
            f"resources/{self.test_word_resource_id}/preview",
            403  # Expect forbidden
        )
        
        if success:
            print("   ✅ Authentication properly required")
        
        # Restore token
        self.admin_token = original_token
        return success

    def test_pdf_rejection(self):
        """Test that PDF files are rejected"""
        if not self.test_pdf_resource_id:
            print("❌ No PDF document resource ID available")
            return False
        
        success, response = self.run_test(
            "PDF Document Preview (Should be rejected)",
            "GET",
            f"resources/{self.test_pdf_resource_id}/preview",
            400
        )
        
        if success:
            response_data = response.json()
            error_message = response_data.get('detail', '')
            if 'Preview only available for Word documents' in error_message:
                print("   ✅ PDF documents properly rejected")
                print(f"   Error message: {error_message}")
                return True
            else:
                print(f"   ❌ Unexpected error message: {error_message}")
        
        return False

    def test_image_rejection(self):
        """Test that image files are rejected"""
        if not self.test_image_resource_id:
            print("❌ No image file resource ID available")
            return False
        
        success, response = self.run_test(
            "Image File Preview (Should be rejected)",
            "GET",
            f"resources/{self.test_image_resource_id}/preview",
            400
        )
        
        if success:
            response_data = response.json()
            error_message = response_data.get('detail', '')
            if 'Preview only available for Word documents' in error_message:
                print("   ✅ Image files properly rejected")
                print(f"   Error message: {error_message}")
                return True
            else:
                print(f"   ❌ Unexpected error message: {error_message}")
        
        return False

    def test_content_type_detection(self):
        """Test that both .doc and .docx files are supported"""
        # Upload a .doc file (using same content but different extension)
        doc_content = self.create_test_docx_file()
        files = {
            'file': ('test_document.doc', doc_content, 'application/msword')
        }
        
        success, response = self.run_test(
            "Upload .doc File",
            "POST",
            "admin/resources/upload",
            200,
            files=files
        )
        
        if success:
            response_data = response.json()
            doc_resource_id = response_data['id']
            print(f"   .doc file uploaded with ID: {doc_resource_id}")
            
            # Test preview of .doc file
            success, response = self.run_test(
                ".doc File Preview",
                "GET",
                f"resources/{doc_resource_id}/preview",
                200
            )
            
            if success:
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    print("   ✅ .doc files supported for preview")
                    return True
                else:
                    print(f"   ❌ Wrong content type for .doc preview: {content_type}")
            
        return False

    def run_all_tests(self):
        """Run all Word document preview tests"""
        print("🚀 Starting Word Document Preview Tests")
        print("=" * 60)
        
        # Login as admin
        if not self.admin_login():
            print("❌ Admin login failed, stopping tests")
            return False
        
        # Upload test files
        self.upload_test_files()
        
        print("\n" + "=" * 50)
        print("WORD DOCUMENT PREVIEW FUNCTIONALITY TESTS")
        print("=" * 50)
        
        # Test 1: Word Document Preview Endpoint
        test1_passed = self.test_word_document_preview()
        
        # Test 2: Authentication Required
        test2_passed = self.test_authentication_required()
        
        # Test 3: File Type Validation - PDF
        test3_passed = self.test_pdf_rejection()
        
        # Test 4: File Type Validation - Image
        test4_passed = self.test_image_rejection()
        
        # Test 5: Content Type Detection (.doc files)
        test5_passed = self.test_content_type_detection()
        
        # Print final results
        print("\n" + "=" * 60)
        print("WORD DOCUMENT PREVIEW TEST RESULTS")
        print("=" * 60)
        
        test_results = [
            ("Word Document Preview Endpoint", test1_passed),
            ("Authentication Required", test2_passed),
            ("PDF File Rejection", test3_passed),
            ("Image File Rejection", test4_passed),
            ("Content Type Detection (.doc/.docx)", test5_passed)
        ]
        
        passed_count = 0
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status} - {test_name}")
            if passed:
                passed_count += 1
        
        print(f"\n📊 Overall Results: {passed_count}/{len(test_results)} tests passed")
        print(f"📊 API Calls: {self.tests_passed}/{self.tests_run} successful")
        
        if passed_count == len(test_results):
            print("🎉 All Word document preview tests passed!")
            return True
        else:
            print(f"⚠️  {len(test_results) - passed_count} tests failed")
            return False

def main():
    tester = WordPreviewTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())