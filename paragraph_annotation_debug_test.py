#!/usr/bin/env python3
"""
Paragraph Annotation Export Debug Test

This test investigates why tagged annotations are not showing up in paragraph exports.
Follows the specific investigation steps from the review request.
"""

import requests
import sys
import json
import io
import csv
from datetime import datetime

class ParagraphAnnotationDebugger:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user_id = None
        self.test_document_id = None
        self.test_sentence_ids = []
        self.created_annotation_ids = []

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def make_request(self, method, endpoint, expected_status=200, data=None, files=None, headers=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.admin_token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if not files and data is not None:
            headers['Content-Type'] = 'application/json'

        self.log(f"{method} {url}")
        
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
                self.log(f"✅ Success - Status: {response.status_code}")
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        return True, response.json()
                    else:
                        return True, response.content
                except:
                    return True, response.text
            else:
                self.log(f"❌ Failed - Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"Error details: {error_data}", "ERROR")
                except:
                    self.log(f"Error text: {response.text}", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"❌ Request failed: {str(e)}", "ERROR")
            return False, {}

    def step_1_admin_login(self):
        """Step 1: Login as admin (admin@sdoh.com / admin123)"""
        self.log("=== STEP 1: Admin Login ===")
        
        admin_credentials = {
            "email": "admin@sdoh.com",
            "password": "admin123"
        }
        
        success, response = self.make_request(
            "POST", 
            "auth/login", 
            200, 
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log("✅ Admin login successful")
            
            # Get admin user info
            success, user_info = self.make_request("GET", "auth/me", 200)
            if success:
                self.admin_user_id = user_info.get('id')
                self.log(f"Admin user ID: {self.admin_user_id}")
                self.log(f"Admin role: {user_info.get('role')}")
            return True
        else:
            self.log("❌ Admin login failed", "ERROR")
            return False

    def step_2_find_test_document(self):
        """Step 2: Get the document 'test_discharge_summaries.csv'"""
        self.log("=== STEP 2: Find test_discharge_summaries.csv Document ===")
        
        success, documents = self.make_request("GET", "documents", 200)
        
        if not success:
            self.log("❌ Failed to get documents", "ERROR")
            return False
        
        self.log(f"Found {len(documents)} documents")
        
        # Look for test_discharge_summaries.csv
        target_document = None
        for doc in documents:
            filename = doc.get('filename', '')
            self.log(f"Document: {filename} (ID: {doc.get('id', 'N/A')})")
            if 'test_discharge_summaries.csv' in filename:
                target_document = doc
                break
        
        if target_document:
            self.test_document_id = target_document['id']
            self.log(f"✅ Found target document: {target_document['filename']}")
            self.log(f"Document ID: {self.test_document_id}")
            self.log(f"Project: {target_document.get('project_name', 'N/A')}")
            self.log(f"Total sentences: {target_document.get('total_sentences', 'N/A')}")
            return True
        else:
            self.log("❌ test_discharge_summaries.csv not found", "ERROR")
            self.log("Available documents:")
            for doc in documents:
                self.log(f"  - {doc.get('filename', 'N/A')}")
            return False

    def step_3_check_document_annotations(self):
        """Step 3: Check what annotations exist for this document via /api/documents/{document_id}/annotations"""
        self.log("=== STEP 3: Check Document Annotations ===")
        
        if not self.test_document_id:
            self.log("❌ No test document ID available", "ERROR")
            return False
        
        success, annotations = self.make_request(
            "GET", 
            f"documents/{self.test_document_id}/annotations", 
            200
        )
        
        if not success:
            self.log("❌ Failed to get document annotations", "ERROR")
            return False
        
        self.log(f"Found {len(annotations)} annotations for document")
        
        # Analyze annotations
        tagged_annotations = []
        skipped_annotations = []
        
        for ann in annotations:
            if ann.get('skipped', False):
                skipped_annotations.append(ann)
            else:
                tags = ann.get('tags', [])
                if tags:
                    tagged_annotations.append(ann)
        
        self.log(f"Tagged annotations: {len(tagged_annotations)}")
        self.log(f"Skipped annotations: {len(skipped_annotations)}")
        
        # Show detailed tag structure for tagged annotations
        if tagged_annotations:
            self.log("=== Tagged Annotation Details ===")
            for i, ann in enumerate(tagged_annotations[:5]):  # Show first 5
                self.log(f"Annotation {i+1}:")
                self.log(f"  User ID: {ann.get('user_id', 'N/A')}")
                self.log(f"  Sentence ID: {ann.get('sentence_id', 'N/A')}")
                self.log(f"  Sentence Text: {ann.get('sentence_text', 'N/A')[:100]}...")
                
                tags = ann.get('tags', [])
                self.log(f"  Tags ({len(tags)}):")
                for tag in tags:
                    domain = tag.get('domain', 'N/A')
                    category = tag.get('category', 'N/A')
                    tag_name = tag.get('tag', 'N/A')
                    valence = tag.get('valence', 'N/A')
                    self.log(f"    - {domain}:{category}:{tag_name}({valence})")
                
                notes = ann.get('notes', '')
                if notes:
                    self.log(f"  Notes: {notes}")
        else:
            self.log("⚠️  No tagged annotations found - only skipped annotations exist")
        
        return True

    def step_4_download_admin_paragraph_export(self):
        """Step 4: Download the admin paragraph export and analyze content"""
        self.log("=== STEP 4: Download Admin Paragraph Export ===")
        
        if not self.test_document_id:
            self.log("❌ No test document ID available", "ERROR")
            return False
        
        success, csv_content = self.make_request(
            "GET", 
            f"admin/download/annotated-paragraphs/{self.test_document_id}", 
            200
        )
        
        if not success:
            self.log("❌ Failed to download paragraph export", "ERROR")
            return False
        
        self.log("✅ Successfully downloaded paragraph export")
        
        # Parse CSV content
        if isinstance(csv_content, bytes):
            csv_text = csv_content.decode('utf-8')
        else:
            csv_text = str(csv_content)
        
        self.log(f"CSV content length: {len(csv_text)} characters")
        
        # Parse and analyze CSV
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(csv_reader)
        
        self.log(f"CSV rows: {len(rows)}")
        
        if rows:
            # Check column headers
            headers = list(rows[0].keys())
            self.log(f"CSV headers: {headers}")
            
            # Analyze paragraph text for tags
            rows_with_tags = 0
            rows_without_tags = 0
            
            self.log("=== Paragraph Content Analysis ===")
            for i, row in enumerate(rows[:10]):  # Analyze first 10 rows
                paragraph_text = row.get('annotated_paragraph_text', '')
                row_index = row.get('row_index', 'N/A')
                subject_id = row.get('subject_id', 'N/A')
                
                # Check if paragraph contains tags
                has_tags = '[Tags:' in paragraph_text
                
                if has_tags:
                    rows_with_tags += 1
                    self.log(f"Row {i+1} (row_index={row_index}, subject_id={subject_id}): HAS TAGS")
                    # Extract and show tags
                    import re
                    tag_matches = re.findall(r'\[Tags: ([^\]]+)\]', paragraph_text)
                    for match in tag_matches:
                        self.log(f"  Tags found: {match}")
                else:
                    rows_without_tags += 1
                    self.log(f"Row {i+1} (row_index={row_index}, subject_id={subject_id}): NO TAGS")
                
                # Show paragraph text sample
                text_sample = paragraph_text[:200] + "..." if len(paragraph_text) > 200 else paragraph_text
                self.log(f"  Text sample: {text_sample}")
            
            self.log(f"Summary: {rows_with_tags} rows with tags, {rows_without_tags} rows without tags")
            
            # Print actual CSV content for inspection
            self.log("=== ACTUAL CSV CONTENT (First 2000 chars) ===")
            self.log(csv_text[:2000])
            if len(csv_text) > 2000:
                self.log("... (content truncated)")
        
        return True

    def step_5_create_fresh_annotation(self):
        """Step 5: Create a fresh annotation with tags on a sentence"""
        self.log("=== STEP 5: Create Fresh Annotation with Tags ===")
        
        if not self.test_document_id:
            self.log("❌ No test document ID available", "ERROR")
            return False
        
        # First get sentences from the document
        success, sentences = self.make_request(
            "GET", 
            f"documents/{self.test_document_id}/sentences", 
            200
        )
        
        if not success or not sentences:
            self.log("❌ Failed to get document sentences", "ERROR")
            return False
        
        # Pick the first sentence for annotation
        target_sentence = sentences[0]
        sentence_id = target_sentence['id']
        sentence_text = target_sentence['text']
        
        self.log(f"Target sentence ID: {sentence_id}")
        self.log(f"Target sentence text: {sentence_text[:100]}...")
        
        # Create a comprehensive annotation with multiple tags
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
                    "domain": "Social and Community Context",
                    "category": "Social Cohesion",
                    "tag": "Social Isolation",
                    "valence": "negative"
                }
            ],
            "notes": "DEBUG TEST: Fresh annotation created for paragraph export testing",
            "skipped": False,
            "confidence": 5,
            "duration_ms": 30000
        }
        
        success, response = self.make_request(
            "POST", 
            "annotations", 
            200, 
            data=annotation_data
        )
        
        if success:
            annotation_id = response.get('id')
            self.created_annotation_ids.append(annotation_id)
            self.log(f"✅ Created fresh annotation with ID: {annotation_id}")
            self.log(f"Tags created: {len(annotation_data['tags'])}")
            for tag in annotation_data['tags']:
                self.log(f"  - {tag['domain']}:{tag['category']}:{tag['tag']}({tag['valence']})")
            return True
        else:
            self.log("❌ Failed to create fresh annotation", "ERROR")
            return False

    def step_6_verify_fresh_annotation_in_export(self):
        """Step 6: Immediately download paragraphs again and verify if the new tag shows up"""
        self.log("=== STEP 6: Verify Fresh Annotation in Export ===")
        
        # Download paragraph export again
        success, csv_content = self.make_request(
            "GET", 
            f"admin/download/annotated-paragraphs/{self.test_document_id}", 
            200
        )
        
        if not success:
            self.log("❌ Failed to download updated paragraph export", "ERROR")
            return False
        
        # Parse CSV content
        if isinstance(csv_content, bytes):
            csv_text = csv_content.decode('utf-8')
        else:
            csv_text = str(csv_content)
        
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(csv_reader)
        
        self.log(f"Updated CSV has {len(rows)} rows")
        
        # Look for our fresh annotation tags
        found_fresh_tags = False
        debug_tag_text = "DEBUG TEST"
        
        for i, row in enumerate(rows):
            paragraph_text = row.get('annotated_paragraph_text', '')
            
            # Check if this row contains our debug annotation
            if debug_tag_text in paragraph_text or 'Economic Stability:Employment:Unemployed' in paragraph_text:
                found_fresh_tags = True
                self.log(f"✅ Found fresh annotation in row {i+1}")
                self.log(f"Row content: {paragraph_text}")
                break
        
        if not found_fresh_tags:
            self.log("❌ Fresh annotation NOT found in paragraph export", "ERROR")
            self.log("This indicates an issue with the paragraph export functionality")
            
            # Show all paragraph content for debugging
            self.log("=== ALL PARAGRAPH CONTENT FOR DEBUGGING ===")
            for i, row in enumerate(rows):
                paragraph_text = row.get('annotated_paragraph_text', '')
                self.log(f"Row {i+1}: {paragraph_text}")
        else:
            self.log("✅ Fresh annotation successfully appears in paragraph export")
        
        return found_fresh_tags

    def step_7_test_user_paragraph_export(self):
        """Step 7: Test user-specific paragraph export endpoint"""
        self.log("=== STEP 7: Test User-Specific Paragraph Export ===")
        
        success, csv_content = self.make_request(
            "GET", 
            f"download/my-annotated-paragraphs/{self.test_document_id}", 
            200
        )
        
        if not success:
            self.log("❌ Failed to download user paragraph export", "ERROR")
            return False
        
        # Parse CSV content
        if isinstance(csv_content, bytes):
            csv_text = csv_content.decode('utf-8')
        else:
            csv_text = str(csv_content)
        
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(csv_reader)
        
        self.log(f"User-specific CSV has {len(rows)} rows")
        
        # Analyze user-specific content
        rows_with_tags = 0
        for row in rows:
            paragraph_text = row.get('annotated_paragraph_text', '')
            if '[Tags:' in paragraph_text:
                rows_with_tags += 1
        
        self.log(f"User-specific export: {rows_with_tags} rows with tags out of {len(rows)} total")
        
        # Show sample content
        if rows:
            self.log("=== User-Specific Export Sample ===")
            sample_row = rows[0]
            self.log(f"Sample paragraph: {sample_row.get('annotated_paragraph_text', '')[:300]}...")
        
        return True

    def cleanup_created_annotations(self):
        """Clean up annotations created during testing"""
        self.log("=== CLEANUP: Removing Created Annotations ===")
        
        for annotation_id in self.created_annotation_ids:
            success, _ = self.make_request(
                "DELETE", 
                f"annotations/{annotation_id}", 
                200
            )
            if success:
                self.log(f"✅ Deleted annotation {annotation_id}")
            else:
                self.log(f"❌ Failed to delete annotation {annotation_id}", "ERROR")

    def run_investigation(self):
        """Run the complete paragraph annotation investigation"""
        self.log("🔍 Starting Paragraph Annotation Export Investigation")
        self.log("=" * 80)
        
        try:
            # Step 1: Admin login
            if not self.step_1_admin_login():
                return False
            
            # Step 2: Find test document
            if not self.step_2_find_test_document():
                return False
            
            # Step 3: Check existing annotations
            if not self.step_3_check_document_annotations():
                return False
            
            # Step 4: Download and analyze paragraph export
            if not self.step_4_download_admin_paragraph_export():
                return False
            
            # Step 5: Create fresh annotation
            if not self.step_5_create_fresh_annotation():
                return False
            
            # Step 6: Verify fresh annotation appears
            fresh_annotation_works = self.step_6_verify_fresh_annotation_in_export()
            
            # Step 7: Test user-specific export
            self.step_7_test_user_paragraph_export()
            
            # Cleanup
            self.cleanup_created_annotations()
            
            # Final analysis
            self.log("=" * 80)
            self.log("🔍 INVESTIGATION SUMMARY")
            self.log("=" * 80)
            
            if fresh_annotation_works:
                self.log("✅ CONCLUSION: Paragraph export functionality is WORKING correctly")
                self.log("   - Fresh annotations with tags appear in paragraph exports")
                self.log("   - Tags are formatted as [Tags: Domain:Category:Tag(+/-)@UserName]")
                self.log("   - Issue may be that user was testing with documents containing only skipped annotations")
            else:
                self.log("❌ CONCLUSION: Paragraph export functionality has ISSUES")
                self.log("   - Fresh annotations with tags do NOT appear in paragraph exports")
                self.log("   - This indicates a bug in the format_sentence_tags function or annotation matching")
            
            return fresh_annotation_works
            
        except Exception as e:
            self.log(f"❌ Investigation failed with error: {str(e)}", "ERROR")
            return False

def main():
    debugger = ParagraphAnnotationDebugger()
    success = debugger.run_investigation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())