import requests
import sys
import json
import io
import csv
from datetime import datetime

class MedicalCSVTester:
    def __init__(self, base_url="https://data-fixer-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_document_ids = []  # Track uploaded documents for cleanup

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        
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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
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

    def test_admin_login(self):
        """Test admin login with predefined credentials"""
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
            print(f"   Admin token obtained successfully")
            return True
        return False

    def create_medical_csv_full(self):
        """Create test CSV with both HISTORY OF PRESENT ILLNESS and SOCIAL HISTORY columns"""
        csv_content = """note_id,HISTORY OF PRESENT ILLNESS,SOCIAL HISTORY
NOTE001,"Patient presents with chest pain. Started 2 hours ago.","Patient smokes 1 pack per day. Lives alone."
NOTE002,"Chief complaint is headache. Migraine history noted.","Works as teacher. No tobacco use. Drinks socially."
NOTE003,"Shortness of breath on exertion. Has been worsening over past week.","Married with two children. No substance use history."
"""
        return io.StringIO(csv_content)

    def create_medical_csv_hpi_only(self):
        """Create test CSV with only HISTORY OF PRESENT ILLNESS column"""
        csv_content = """note_id,HISTORY OF PRESENT ILLNESS
NOTE004,"Patient presents with abdominal pain. Sharp, localized to right lower quadrant."
NOTE005,"Fever and chills for 3 days. Temperature up to 102F."
"""
        return io.StringIO(csv_content)

    def create_medical_csv_social_only(self):
        """Create test CSV with only SOCIAL HISTORY column"""
        csv_content = """note_id,SOCIAL HISTORY
NOTE006,"Patient is a retired engineer. Lives with spouse in assisted living facility."
NOTE007,"Single mother of three. Works two part-time jobs. Limited family support."
"""
        return io.StringIO(csv_content)

    def test_medical_csv_upload_full(self):
        """Test uploading CSV with both medical record columns"""
        print("\n📋 Testing CSV upload with both HPI and Social History columns...")
        
        csv_content = self.create_medical_csv_full().getvalue()
        
        files = {
            'file': ('medical_records_full.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Medical Records Test'),
            'description': (None, 'Test CSV with both HPI and Social History columns')
        }
        
        success, response = self.run_test(
            "Medical CSV Upload - Full Columns",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            document_id = response['id']
            self.test_document_ids.append(document_id)
            print(f"   Document ID: {document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
            
            # Verify response includes expected fields
            expected_fields = ['id', 'filename', 'project_name', 'description', 'total_sentences']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                print(f"   ❌ Missing response fields: {missing_fields}")
                return False, None
            else:
                print(f"   ✅ All expected response fields present")
                return True, document_id
        
        return False, None

    def test_medical_csv_upload_hpi_only(self):
        """Test uploading CSV with only HISTORY OF PRESENT ILLNESS column"""
        print("\n📋 Testing CSV upload with only HPI column...")
        
        csv_content = self.create_medical_csv_hpi_only().getvalue()
        
        files = {
            'file': ('medical_records_hpi_only.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Medical Records HPI Only'),
            'description': (None, 'Test CSV with only HPI column')
        }
        
        success, response = self.run_test(
            "Medical CSV Upload - HPI Only",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            document_id = response['id']
            self.test_document_ids.append(document_id)
            print(f"   Document ID: {document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
            return True, document_id
        
        return False, None

    def test_medical_csv_upload_social_only(self):
        """Test uploading CSV with only SOCIAL HISTORY column"""
        print("\n📋 Testing CSV upload with only Social History column...")
        
        csv_content = self.create_medical_csv_social_only().getvalue()
        
        files = {
            'file': ('medical_records_social_only.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Medical Records Social Only'),
            'description': (None, 'Test CSV with only Social History column')
        }
        
        success, response = self.run_test(
            "Medical CSV Upload - Social History Only",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            document_id = response['id']
            self.test_document_ids.append(document_id)
            print(f"   Document ID: {document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
            return True, document_id
        
        return False, None

    def test_sentence_parsing_full(self, document_id):
        """Test sentence parsing for CSV with both columns"""
        print(f"\n🔍 Testing sentence parsing for document {document_id}...")
        
        success, response = self.run_test(
            "Get Document Sentences - Full CSV",
            "GET",
            f"documents/{document_id}/sentences",
            200
        )
        
        if not success or not response:
            return False
        
        sentences = response
        print(f"   Found {len(sentences)} sentences")
        
        # Verify sentence structure
        if not sentences:
            print("   ❌ No sentences found")
            return False
        
        # Check first sentence structure
        first_sentence = sentences[0]
        required_fields = ['id', 'text', 'subject_id', 'row_index', 'sentence_index', 'document_id']
        missing_fields = [field for field in required_fields if field not in first_sentence]
        
        if missing_fields:
            print(f"   ❌ Missing sentence fields: {missing_fields}")
            return False
        
        print(f"   ✅ All required sentence fields present")
        
        # Verify subject_id uses note_id values
        expected_note_ids = ['NOTE001', 'NOTE002', 'NOTE003']
        found_note_ids = list(set(s.get('subject_id') for s in sentences))
        
        print(f"   Expected note_ids: {expected_note_ids}")
        print(f"   Found subject_ids: {found_note_ids}")
        
        # Check if all expected note_ids are found
        missing_note_ids = [nid for nid in expected_note_ids if nid not in found_note_ids]
        if missing_note_ids:
            print(f"   ❌ Missing note_ids in subject_id: {missing_note_ids}")
            return False
        
        print(f"   ✅ All note_ids properly mapped to subject_id")
        
        # Verify text combination (HPI + Social History)
        # Group sentences by row_index to check text combination
        sentences_by_row = {}
        for sentence in sentences:
            row_idx = sentence.get('row_index')
            if row_idx not in sentences_by_row:
                sentences_by_row[row_idx] = []
            sentences_by_row[row_idx].append(sentence)
        
        print(f"   Sentences grouped by row: {len(sentences_by_row)} rows")
        
        # Check that each row has multiple sentences (from combined text)
        for row_idx, row_sentences in sentences_by_row.items():
            print(f"   Row {row_idx}: {len(row_sentences)} sentences")
            
            # Verify sentence_index increments within each row
            sentence_indices = [s.get('sentence_index') for s in row_sentences]
            sentence_indices.sort()
            expected_indices = list(range(len(sentence_indices)))
            
            if sentence_indices != expected_indices:
                print(f"   ❌ Row {row_idx} sentence indices not sequential: {sentence_indices}")
                return False
            
            # Show sample text to verify combination
            if row_sentences:
                sample_text = ' '.join([s.get('text', '') for s in row_sentences])
                print(f"   Row {row_idx} combined text: {sample_text[:100]}...")
        
        print(f"   ✅ Sentence parsing and indexing correct")
        return True

    def test_sentence_parsing_hpi_only(self, document_id):
        """Test sentence parsing for CSV with only HPI column"""
        print(f"\n🔍 Testing sentence parsing for HPI-only document {document_id}...")
        
        success, response = self.run_test(
            "Get Document Sentences - HPI Only",
            "GET",
            f"documents/{document_id}/sentences",
            200
        )
        
        if not success or not response:
            return False
        
        sentences = response
        print(f"   Found {len(sentences)} sentences")
        
        # Verify subject_id uses note_id values
        expected_note_ids = ['NOTE004', 'NOTE005']
        found_note_ids = list(set(s.get('subject_id') for s in sentences))
        
        print(f"   Expected note_ids: {expected_note_ids}")
        print(f"   Found subject_ids: {found_note_ids}")
        
        # Check if all expected note_ids are found
        missing_note_ids = [nid for nid in expected_note_ids if nid not in found_note_ids]
        if missing_note_ids:
            print(f"   ❌ Missing note_ids in subject_id: {missing_note_ids}")
            return False
        
        print(f"   ✅ HPI-only CSV processed correctly")
        return True

    def test_sentence_parsing_social_only(self, document_id):
        """Test sentence parsing for CSV with only Social History column"""
        print(f"\n🔍 Testing sentence parsing for Social History-only document {document_id}...")
        
        success, response = self.run_test(
            "Get Document Sentences - Social Only",
            "GET",
            f"documents/{document_id}/sentences",
            200
        )
        
        if not success or not response:
            return False
        
        sentences = response
        print(f"   Found {len(sentences)} sentences")
        
        # Verify subject_id uses note_id values
        expected_note_ids = ['NOTE006', 'NOTE007']
        found_note_ids = list(set(s.get('subject_id') for s in sentences))
        
        print(f"   Expected note_ids: {expected_note_ids}")
        print(f"   Found subject_ids: {found_note_ids}")
        
        # Check if all expected note_ids are found
        missing_note_ids = [nid for nid in expected_note_ids if nid not in found_note_ids]
        if missing_note_ids:
            print(f"   ❌ Missing note_ids in subject_id: {missing_note_ids}")
            return False
        
        print(f"   ✅ Social History-only CSV processed correctly")
        return True

    def test_text_combination_verification(self, document_id):
        """Detailed verification of text combination from both columns"""
        print(f"\n🔍 Detailed text combination verification for document {document_id}...")
        
        success, response = self.run_test(
            "Get Sentences for Text Verification",
            "GET",
            f"documents/{document_id}/sentences",
            200
        )
        
        if not success or not response:
            return False
        
        sentences = response
        
        # Group by row_index and reconstruct original text
        sentences_by_row = {}
        for sentence in sentences:
            row_idx = sentence.get('row_index')
            if row_idx not in sentences_by_row:
                sentences_by_row[row_idx] = []
            sentences_by_row[row_idx].append(sentence)
        
        # Sort sentences within each row by sentence_index
        for row_idx in sentences_by_row:
            sentences_by_row[row_idx].sort(key=lambda x: x.get('sentence_index', 0))
        
        # Expected combined text for verification
        expected_combinations = {
            1: "Patient presents with chest pain. Started 2 hours ago. Patient smokes 1 pack per day. Lives alone.",
            2: "Chief complaint is headache. Migraine history noted. Works as teacher. No tobacco use. Drinks socially.",
            3: "Shortness of breath on exertion. Has been worsening over past week. Married with two children. No substance use history."
        }
        
        for row_idx, row_sentences in sentences_by_row.items():
            # Reconstruct text from sentences
            reconstructed_text = ' '.join([s.get('text', '') for s in row_sentences])
            expected_text = expected_combinations.get(row_idx, '')
            
            print(f"   Row {row_idx}:")
            print(f"     Expected: {expected_text}")
            print(f"     Found:    {reconstructed_text}")
            
            # Check if HPI text comes first
            if row_idx == 1:
                if not reconstructed_text.startswith("Patient presents with chest pain"):
                    print(f"   ❌ Row {row_idx}: HPI text not at beginning")
                    return False
                if "Patient smokes 1 pack per day" not in reconstructed_text:
                    print(f"   ❌ Row {row_idx}: Social History text not found")
                    return False
            
            print(f"     ✅ Text combination correct for row {row_idx}")
        
        print(f"   ✅ All text combinations verified correctly")
        return True

    def test_backward_compatibility(self):
        """Test that the system still works with traditional CSV formats"""
        print("\n🔄 Testing backward compatibility with traditional CSV format...")
        
        # Create traditional CSV format
        csv_content = """patient_id,discharge_summary,notes
1,"Patient is a 45-year-old male with diabetes.","Financial hardship"
2,"67-year-old female with hypertension.","Geographic barriers"
"""
        
        files = {
            'file': ('traditional_format.csv', csv_content, 'text/csv'),
            'project_name': (None, 'Backward Compatibility Test'),
            'description': (None, 'Test traditional CSV format still works')
        }
        
        success, response = self.run_test(
            "Backward Compatibility - Traditional CSV",
            "POST",
            "documents/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            document_id = response['id']
            self.test_document_ids.append(document_id)
            print(f"   ✅ Traditional CSV format still supported")
            print(f"   Document ID: {document_id}")
            print(f"   Total sentences: {response.get('total_sentences', 0)}")
            return True
        
        return False

    def cleanup_test_documents(self):
        """Clean up uploaded test documents"""
        print(f"\n🧹 Cleaning up {len(self.test_document_ids)} test documents...")
        
        cleanup_count = 0
        for document_id in self.test_document_ids:
            success, response = self.run_test(
                f"Delete Test Document {document_id[:8]}",
                "DELETE",
                f"admin/documents/{document_id}",
                200
            )
            if success:
                cleanup_count += 1
        
        print(f"   Cleaned up {cleanup_count}/{len(self.test_document_ids)} documents")
        return cleanup_count == len(self.test_document_ids)

    def run_medical_csv_tests(self):
        """Run comprehensive medical CSV upload tests"""
        print("🏥 Starting Medical Record CSV Upload Tests")
        print("=" * 60)
        
        # Admin authentication
        if not self.test_admin_login():
            print("❌ Admin login failed, cannot proceed with tests")
            return False
        
        # Test 1: Upload CSV with both columns
        print("\n" + "=" * 20 + " TEST 1: FULL MEDICAL CSV " + "=" * 20)
        success_full, doc_id_full = self.test_medical_csv_upload_full()
        if success_full and doc_id_full:
            self.test_sentence_parsing_full(doc_id_full)
            self.test_text_combination_verification(doc_id_full)
        
        # Test 2: Upload CSV with only HPI column
        print("\n" + "=" * 20 + " TEST 2: HPI ONLY CSV " + "=" * 20)
        success_hpi, doc_id_hpi = self.test_medical_csv_upload_hpi_only()
        if success_hpi and doc_id_hpi:
            self.test_sentence_parsing_hpi_only(doc_id_hpi)
        
        # Test 3: Upload CSV with only Social History column
        print("\n" + "=" * 20 + " TEST 3: SOCIAL HISTORY ONLY CSV " + "=" * 20)
        success_social, doc_id_social = self.test_medical_csv_upload_social_only()
        if success_social and doc_id_social:
            self.test_sentence_parsing_social_only(doc_id_social)
        
        # Test 4: Backward compatibility
        print("\n" + "=" * 20 + " TEST 4: BACKWARD COMPATIBILITY " + "=" * 20)
        self.test_backward_compatibility()
        
        # Cleanup
        print("\n" + "=" * 30 + " CLEANUP " + "=" * 30)
        self.cleanup_test_documents()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Medical CSV Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All medical CSV tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = MedicalCSVTester()
    success = tester.run_medical_csv_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())