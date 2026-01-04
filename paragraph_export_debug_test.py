#!/usr/bin/env python3
"""
Debug test for paragraph annotation export issue.
Tests the specific issue where annotations are not showing up in the text when downloading paragraphs.
"""

import requests
import sys
import json
import io
import csv
from datetime import datetime

class ParagraphExportDebugger:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.admin_user_id = None
        self.user_id = None
        self.document_id = None
        self.sentence_ids = []
        self.annotation_ids = []

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def make_request(self, method, endpoint, token=None, data=None, files=None, expected_status=200):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if not files and data:
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

            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code == expected_status:
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        return True, response.json()
                    elif 'text/csv' in response.headers.get('content-type', ''):
                        return True, response.text
                    else:
                        return True, response.content
                except:
                    return True, response.text
            else:
                self.log(f"❌ Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"Error details: {error_data}", "ERROR")
                except:
                    self.log(f"Error text: {response.text}", "ERROR")
                return False, None

        except Exception as e:
            self.log(f"❌ Request failed: {str(e)}", "ERROR")
            return False, None

    def step_1_admin_login(self):
        """Step 1: Login as admin (admin@sdoh.com / admin123)"""
        self.log("=== STEP 1: Admin Login ===")
        
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.make_request("POST", "auth/login", data=admin_credentials)
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log("✅ Admin login successful")
            
            # Get admin user info
            success, user_info = self.make_request("GET", "auth/me", token=self.admin_token)
            if success:
                self.admin_user_id = user_info.get('id')
                self.log(f"✅ Admin user ID: {self.admin_user_id}")
                self.log(f"✅ Admin role: {user_info.get('role')}")
                return True
        
        self.log("❌ Admin login failed", "ERROR")
        return False

    def step_2_get_document_with_annotations(self):
        """Step 2: Get a document ID that has annotations"""
        self.log("=== STEP 2: Find Document with Annotations ===")
        
        # Get all documents
        success, documents = self.make_request("GET", "documents", token=self.admin_token)
        if not success or not documents:
            self.log("❌ No documents found", "ERROR")
            return False
        
        self.log(f"Found {len(documents)} documents")
        
        # Check each document for annotations
        for doc in documents:
            doc_id = doc['id']
            self.log(f"Checking document: {doc.get('filename', 'Unknown')} (ID: {doc_id})")
            
            # Get sentences for this document
            success, sentences = self.make_request("GET", f"documents/{doc_id}/sentences", token=self.admin_token)
            if success and sentences:
                # Check if any sentences have annotations
                has_annotations = False
                for sentence in sentences:
                    if sentence.get('annotations') and len(sentence['annotations']) > 0:
                        has_annotations = True
                        break
                
                if has_annotations:
                    self.document_id = doc_id
                    self.log(f"✅ Found document with annotations: {doc.get('filename')} (ID: {doc_id})")
                    return True
                else:
                    self.log(f"   No annotations found in document: {doc.get('filename')}")
        
        self.log("❌ No documents with annotations found", "ERROR")
        return False

    def step_3_check_annotations_exist(self):
        """Step 3: Check annotations exist - Call /api/documents/{document_id}/annotations"""
        self.log("=== STEP 3: Verify Annotations Exist ===")
        
        if not self.document_id:
            self.log("❌ No document ID available", "ERROR")
            return False
        
        success, annotations = self.make_request("GET", f"documents/{self.document_id}/annotations", token=self.admin_token)
        
        if not success:
            self.log("❌ Failed to get document annotations", "ERROR")
            return False
        
        if not annotations or len(annotations) == 0:
            self.log("❌ No annotations found for document", "ERROR")
            return False
        
        self.log(f"✅ Found {len(annotations)} annotations")
        
        # Analyze annotations
        tagged_annotations = []
        skipped_annotations = []
        
        for ann in annotations:
            if ann.get('skipped'):
                skipped_annotations.append(ann)
            else:
                tags = ann.get('tags', [])
                if tags and len(tags) > 0:
                    tagged_annotations.append(ann)
                    self.annotation_ids.append(ann['id'])
        
        self.log(f"   Tagged annotations: {len(tagged_annotations)}")
        self.log(f"   Skipped annotations: {len(skipped_annotations)}")
        
        if len(tagged_annotations) == 0:
            self.log("❌ No tagged annotations found (only skipped)", "ERROR")
            return False
        
        # Show sample tagged annotation
        sample_ann = tagged_annotations[0]
        self.log(f"   Sample annotation:")
        self.log(f"     Sentence ID: {sample_ann.get('sentence_id')}")
        self.log(f"     User ID: {sample_ann.get('user_id')}")
        self.log(f"     Tags: {sample_ann.get('tags')}")
        self.log(f"     Notes: {sample_ann.get('notes', 'None')}")
        
        return True

    def step_4_download_admin_paragraphs(self):
        """Step 4: Download admin paragraphs and check if tags appear in the text"""
        self.log("=== STEP 4: Download Admin Annotated Paragraphs ===")
        
        if not self.document_id:
            self.log("❌ No document ID available", "ERROR")
            return False
        
        success, csv_content = self.make_request("GET", f"admin/download/annotated-paragraphs/{self.document_id}", token=self.admin_token)
        
        if not success:
            self.log("❌ Failed to download admin paragraphs", "ERROR")
            return False
        
        self.log("✅ Admin paragraphs downloaded successfully")
        
        # Parse CSV content
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            self.log(f"   CSV contains {len(rows)} rows")
            
            if len(rows) == 0:
                self.log("❌ CSV is empty", "ERROR")
                return False
            
            # Check CSV headers
            headers = csv_reader.fieldnames
            self.log(f"   CSV headers: {headers}")
            
            expected_headers = ['row_index', 'subject_id', 'annotated_paragraph_text']
            missing_headers = [h for h in expected_headers if h not in headers]
            if missing_headers:
                self.log(f"❌ Missing expected headers: {missing_headers}", "ERROR")
                return False
            
            # Analyze paragraph content for tags
            rows_with_tags = 0
            rows_without_tags = 0
            
            for i, row in enumerate(rows):
                paragraph_text = row.get('annotated_paragraph_text', '')
                
                if '[Tags:' in paragraph_text:
                    rows_with_tags += 1
                    if i < 3:  # Show first 3 examples
                        self.log(f"   Row {i} WITH tags: {paragraph_text[:100]}...")
                else:
                    rows_without_tags += 1
                    if i < 3 and rows_with_tags == 0:  # Show examples if no tags found
                        self.log(f"   Row {i} WITHOUT tags: {paragraph_text[:100]}...")
            
            self.log(f"   Rows with tags: {rows_with_tags}")
            self.log(f"   Rows without tags: {rows_without_tags}")
            
            if rows_with_tags == 0:
                self.log("❌ NO TAGS FOUND in paragraph text - This is the issue!", "ERROR")
                return False
            else:
                self.log(f"✅ Tags found in {rows_with_tags} paragraphs")
                return True
                
        except Exception as e:
            self.log(f"❌ Failed to parse CSV: {str(e)}", "ERROR")
            return False

    def step_5_create_regular_user_and_login(self):
        """Step 5: Login as a regular user who has made annotations"""
        self.log("=== STEP 5: Create Regular User and Login ===")
        
        # First, create a regular user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test User {timestamp}"
        }
        
        success, response = self.make_request("POST", "auth/register", data=user_data)
        
        if not success:
            self.log("❌ Failed to create regular user", "ERROR")
            return False
        
        self.user_id = response.get('id')
        self.log(f"✅ Created regular user: {user_data['email']}")
        
        # Login as the regular user
        login_data = {
            "email": user_data['email'],
            "password": user_data['password']
        }
        
        success, response = self.make_request("POST", "auth/login", data=login_data)
        
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            self.log("✅ Regular user login successful")
            return True
        
        self.log("❌ Regular user login failed", "ERROR")
        return False

    def step_6_create_user_annotations(self):
        """Step 6: Create annotations as the regular user"""
        self.log("=== STEP 6: Create User Annotations ===")
        
        if not self.document_id or not self.user_token:
            self.log("❌ Missing document ID or user token", "ERROR")
            return False
        
        # Get sentences for the document
        success, sentences = self.make_request("GET", f"documents/{self.document_id}/sentences", token=self.user_token)
        
        if not success or not sentences:
            self.log("❌ Failed to get sentences", "ERROR")
            return False
        
        self.log(f"Found {len(sentences)} sentences")
        
        # Create annotations for first few sentences
        annotations_created = 0
        for i, sentence in enumerate(sentences[:3]):  # Annotate first 3 sentences
            sentence_id = sentence['id']
            
            annotation_data = {
                "sentence_id": sentence_id,
                "tags": [
                    {
                        "domain": "Economic Stability",
                        "category": "Employment",
                        "tag": "Unemployed",
                        "valence": "negative"
                    }
                ],
                "notes": f"Test annotation by regular user for sentence {i+1}",
                "skipped": False,
                "confidence": 4,
                "duration_ms": 5000
            }
            
            success, response = self.make_request("POST", "annotations", token=self.user_token, data=annotation_data)
            
            if success:
                annotations_created += 1
                self.log(f"   ✅ Created annotation for sentence {i+1}")
            else:
                self.log(f"   ❌ Failed to create annotation for sentence {i+1}")
        
        self.log(f"✅ Created {annotations_created} annotations as regular user")
        return annotations_created > 0

    def step_7_download_user_paragraphs(self):
        """Step 7: Download user paragraphs and check if tags appear"""
        self.log("=== STEP 7: Download User Annotated Paragraphs ===")
        
        if not self.document_id or not self.user_token:
            self.log("❌ Missing document ID or user token", "ERROR")
            return False
        
        success, csv_content = self.make_request("GET", f"download/my-annotated-paragraphs/{self.document_id}", token=self.user_token)
        
        if not success:
            self.log("❌ Failed to download user paragraphs", "ERROR")
            return False
        
        self.log("✅ User paragraphs downloaded successfully")
        
        # Parse CSV content
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            self.log(f"   CSV contains {len(rows)} rows")
            
            if len(rows) == 0:
                self.log("❌ CSV is empty", "ERROR")
                return False
            
            # Check CSV headers
            headers = csv_reader.fieldnames
            self.log(f"   CSV headers: {headers}")
            
            # Analyze paragraph content for tags
            rows_with_tags = 0
            rows_without_tags = 0
            
            for i, row in enumerate(rows):
                paragraph_text = row.get('annotated_paragraph_text', '')
                
                if '[Tags:' in paragraph_text:
                    rows_with_tags += 1
                    self.log(f"   Row {i} WITH tags: {paragraph_text[:150]}...")
                else:
                    rows_without_tags += 1
                    self.log(f"   Row {i} WITHOUT tags: {paragraph_text[:150]}...")
            
            self.log(f"   Rows with tags: {rows_with_tags}")
            self.log(f"   Rows without tags: {rows_without_tags}")
            
            if rows_with_tags == 0:
                self.log("❌ NO TAGS FOUND in user paragraph text - This confirms the issue!", "ERROR")
                return False
            else:
                self.log(f"✅ Tags found in {rows_with_tags} paragraphs")
                return True
                
        except Exception as e:
            self.log(f"❌ Failed to parse CSV: {str(e)}", "ERROR")
            return False

    def step_8_analyze_format_sentence_tags_function(self):
        """Step 8: Analyze the format_sentence_tags function behavior"""
        self.log("=== STEP 8: Analyze format_sentence_tags Function ===")
        
        # This step involves examining the backend code logic
        # Let's test the actual annotation data to see what's happening
        
        if not self.document_id:
            self.log("❌ No document ID available", "ERROR")
            return False
        
        # Get document sentences with annotations
        success, sentences = self.make_request("GET", f"documents/{self.document_id}/sentences", token=self.admin_token)
        
        if not success:
            self.log("❌ Failed to get sentences", "ERROR")
            return False
        
        self.log(f"Analyzing {len(sentences)} sentences for annotation data...")
        
        sentences_with_annotations = 0
        for sentence in sentences:
            annotations = sentence.get('annotations', [])
            if annotations:
                sentences_with_annotations += 1
                self.log(f"   Sentence ID {sentence['id']} has {len(annotations)} annotations")
                
                for ann in annotations:
                    tags = ann.get('tags', [])
                    skipped = ann.get('skipped', False)
                    user_id = ann.get('user_id', 'Unknown')
                    
                    if skipped:
                        self.log(f"     - SKIPPED annotation by user {user_id}")
                    elif tags:
                        self.log(f"     - TAGGED annotation by user {user_id}: {len(tags)} tags")
                        for tag in tags:
                            domain = tag.get('domain', '')
                            category = tag.get('category', '')
                            tag_name = tag.get('tag', '')
                            valence = tag.get('valence', '')
                            self.log(f"       * {domain}:{category}:{tag_name}({valence})")
                    else:
                        self.log(f"     - EMPTY annotation by user {user_id} (no tags, not skipped)")
        
        self.log(f"Found {sentences_with_annotations} sentences with annotations")
        
        return sentences_with_annotations > 0

    def run_debug_test(self):
        """Run the complete debugging test"""
        self.log("🔍 Starting Paragraph Export Debug Test")
        self.log("=" * 60)
        
        # Step 1: Admin login
        if not self.step_1_admin_login():
            return False
        
        # Step 2: Get document with annotations
        if not self.step_2_get_document_with_annotations():
            return False
        
        # Step 3: Check annotations exist
        if not self.step_3_check_annotations_exist():
            return False
        
        # Step 4: Download admin paragraphs
        admin_paragraphs_ok = self.step_4_download_admin_paragraphs()
        
        # Step 5: Create regular user
        if not self.step_5_create_regular_user_and_login():
            return False
        
        # Step 6: Create user annotations
        if not self.step_6_create_user_annotations():
            return False
        
        # Step 7: Download user paragraphs
        user_paragraphs_ok = self.step_7_download_user_paragraphs()
        
        # Step 8: Analyze function behavior
        self.step_8_analyze_format_sentence_tags_function()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 DEBUG TEST SUMMARY")
        self.log("=" * 60)
        
        if admin_paragraphs_ok and user_paragraphs_ok:
            self.log("✅ ISSUE NOT REPRODUCED: Tags are appearing in paragraph exports")
        elif not admin_paragraphs_ok and not user_paragraphs_ok:
            self.log("❌ ISSUE CONFIRMED: Tags are NOT appearing in either admin or user paragraph exports")
        elif not admin_paragraphs_ok:
            self.log("❌ ISSUE CONFIRMED: Tags are NOT appearing in admin paragraph exports")
        elif not user_paragraphs_ok:
            self.log("❌ ISSUE CONFIRMED: Tags are NOT appearing in user paragraph exports")
        
        return admin_paragraphs_ok and user_paragraphs_ok

def main():
    debugger = ParagraphExportDebugger()
    success = debugger.run_debug_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())