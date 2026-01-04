#!/usr/bin/env python3
"""
Resource Upload/Download Testing Script
Tests the fixed GridFS resource upload and download functionality
"""

import requests
import sys
import json
import io
import os
from datetime import datetime

class ResourceUploadTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.uploaded_resource_ids = []

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

    def admin_login(self):
        """Login as admin user"""
        print("🔐 Logging in as admin...")
        
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=admin_credentials,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                self.log_test("Admin Login", True, f"Token obtained: {self.admin_token[:20]}...")
                return True
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def create_test_pdf_content(self):
        """Create a simple PDF-like content for testing"""
        # Simple PDF header (not a real PDF, but has PDF extension)
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"

    def create_test_image_content(self):
        """Create a simple PNG-like content for testing"""
        # Simple PNG header
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'

    def test_resource_upload_pdf(self):
        """Test uploading a PDF file"""
        print("\n📄 Testing PDF upload...")
        
        if not self.admin_token:
            self.log_test("PDF Upload", False, "No admin token available")
            return False

        # Create test PDF content
        pdf_content = self.create_test_pdf_content()
        
        try:
            files = {
                'file': ('test_document.pdf', pdf_content, 'application/pdf')
            }
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/admin/resources/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                resource_id = data.get('id')
                if resource_id:
                    self.uploaded_resource_ids.append(resource_id)
                    self.log_test("PDF Upload", True, f"Resource ID: {resource_id}")
                    return resource_id
                else:
                    self.log_test("PDF Upload", False, "No resource ID in response")
                    return False
            else:
                self.log_test("PDF Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("PDF Upload", False, f"Error: {str(e)}")
            return False

    def test_resource_upload_image(self):
        """Test uploading an image file"""
        print("\n🖼️ Testing image upload...")
        
        if not self.admin_token:
            self.log_test("Image Upload", False, "No admin token available")
            return False

        # Create test image content
        image_content = self.create_test_image_content()
        
        try:
            files = {
                'file': ('test_image.png', image_content, 'image/png')
            }
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/admin/resources/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                resource_id = data.get('id')
                if resource_id:
                    self.uploaded_resource_ids.append(resource_id)
                    self.log_test("Image Upload", True, f"Resource ID: {resource_id}")
                    return resource_id
                else:
                    self.log_test("Image Upload", False, "No resource ID in response")
                    return False
            else:
                self.log_test("Image Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Image Upload", False, f"Error: {str(e)}")
            return False

    def test_resource_download(self, resource_id, expected_content):
        """Test downloading a resource"""
        print(f"\n⬇️ Testing resource download for ID: {resource_id}...")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            response = requests.get(
                f"{self.base_url}/resources/{resource_id}/download",
                headers=headers
            )
            
            if response.status_code == 200:
                downloaded_content = response.content
                if downloaded_content == expected_content:
                    self.log_test("Resource Download", True, f"Content matches (size: {len(downloaded_content)} bytes)")
                    return True
                else:
                    self.log_test("Resource Download", False, f"Content mismatch. Expected: {len(expected_content)} bytes, Got: {len(downloaded_content)} bytes")
                    return False
            else:
                self.log_test("Resource Download", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resource Download", False, f"Error: {str(e)}")
            return False

    def test_upload_unsupported_file_type(self):
        """Test uploading unsupported file type"""
        print("\n🚫 Testing unsupported file type upload...")
        
        if not self.admin_token:
            self.log_test("Unsupported File Upload", False, "No admin token available")
            return False

        # Create test file with unsupported extension
        test_content = b"This is a test file with unsupported extension"
        
        try:
            files = {
                'file': ('test_file.xyz', test_content, 'application/octet-stream')
            }
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/admin/resources/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 400:
                self.log_test("Unsupported File Upload", True, "Correctly rejected unsupported file type")
                return True
            else:
                self.log_test("Unsupported File Upload", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Unsupported File Upload", False, f"Error: {str(e)}")
            return False

    def test_upload_without_file(self):
        """Test uploading without providing a file"""
        print("\n📭 Testing upload without file...")
        
        if not self.admin_token:
            self.log_test("Upload Without File", False, "No admin token available")
            return False

        try:
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            # Send request without files
            response = requests.post(
                f"{self.base_url}/admin/resources/upload",
                headers=headers
            )
            
            if response.status_code == 422:
                self.log_test("Upload Without File", True, "Correctly rejected request without file")
                return True
            else:
                self.log_test("Upload Without File", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Upload Without File", False, f"Error: {str(e)}")
            return False

    def test_unauthorized_upload(self):
        """Test uploading without admin privileges"""
        print("\n🔒 Testing unauthorized upload...")
        
        # Create test content
        test_content = self.create_test_pdf_content()
        
        try:
            files = {
                'file': ('unauthorized_test.pdf', test_content, 'application/pdf')
            }
            # No Authorization header
            
            response = requests.post(
                f"{self.base_url}/admin/resources/upload",
                files=files
            )
            
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Upload", True, f"Correctly rejected unauthorized request (status: {response.status_code})")
                return True
            else:
                self.log_test("Unauthorized Upload", False, f"Expected 401/403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Unauthorized Upload", False, f"Error: {str(e)}")
            return False

    def test_resource_metadata_storage(self):
        """Test that resource metadata is properly stored"""
        print("\n📊 Testing resource metadata storage...")
        
        if not self.admin_token:
            self.log_test("Resource Metadata Storage", False, "No admin token available")
            return False

        try:
            headers = {
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            response = requests.get(
                f"{self.base_url}/resources",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                resources = data.get('items', []) if isinstance(data, dict) else data
                
                # Check if our uploaded resources appear in the list
                uploaded_found = 0
                for resource_id in self.uploaded_resource_ids:
                    for resource in resources:
                        if resource.get('id') == resource_id:
                            uploaded_found += 1
                            print(f"   Found resource: {resource.get('filename')} (ID: {resource_id})")
                            break
                
                if uploaded_found == len(self.uploaded_resource_ids):
                    self.log_test("Resource Metadata Storage", True, f"All {uploaded_found} uploaded resources found in metadata")
                    return True
                else:
                    self.log_test("Resource Metadata Storage", False, f"Only {uploaded_found}/{len(self.uploaded_resource_ids)} resources found in metadata")
                    return False
            else:
                self.log_test("Resource Metadata Storage", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resource Metadata Storage", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all resource upload/download tests"""
        print("🚀 Starting Resource Upload/Download Tests")
        print("=" * 60)
        
        # Login as admin
        if not self.admin_login():
            print("❌ Cannot proceed without admin access")
            return False
        
        # Test successful uploads
        pdf_content = self.create_test_pdf_content()
        image_content = self.create_test_image_content()
        
        pdf_resource_id = self.test_resource_upload_pdf()
        image_resource_id = self.test_resource_upload_image()
        
        # Test downloads if uploads succeeded
        if pdf_resource_id:
            self.test_resource_download(pdf_resource_id, pdf_content)
        
        if image_resource_id:
            self.test_resource_download(image_resource_id, image_content)
        
        # Test error conditions
        self.test_upload_unsupported_file_type()
        self.test_upload_without_file()
        self.test_unauthorized_upload()
        
        # Test metadata storage
        if self.uploaded_resource_ids:
            self.test_resource_metadata_storage()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All resource upload/download tests passed!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} test(s) failed")
            return False

def main():
    """Main function to run the resource upload tests"""
    tester = ResourceUploadTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())