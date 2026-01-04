#!/usr/bin/env python3
"""
Test what happens when downloading paragraphs from a document with no annotations
"""

import requests
import sys
import json
import io
import csv

def test_empty_document():
    base_url = "https://data-fixer-1.preview.emergentagent.com/api"
    
    # Login as admin
    admin_credentials = {"email": "admin@sdoh.com", "password": "admin123"}
    response = requests.post(f"{base_url}/auth/login", json=admin_credentials)
    admin_token = response.json()['access_token']
    
    # Get documents
    response = requests.get(f"{base_url}/documents", headers={'Authorization': f'Bearer {admin_token}'})
    documents = response.json()
    
    print(f"Testing all {len(documents)} documents for annotation status:")
    
    for doc in documents:
        document_id = doc['id']
        filename = doc.get('filename', 'Unknown')
        
        print(f"\n--- Document: {filename} (ID: {document_id}) ---")
        
        # Check annotations
        response = requests.get(f"{base_url}/documents/{document_id}/annotations", 
                              headers={'Authorization': f'Bearer {admin_token}'})
        
        if response.status_code == 200:
            annotations = response.json()
            tagged_count = sum(1 for ann in annotations if not ann.get('skipped') and ann.get('tags'))
            skipped_count = sum(1 for ann in annotations if ann.get('skipped'))
            
            print(f"  Annotations: {len(annotations)} total ({tagged_count} tagged, {skipped_count} skipped)")
            
            # Test admin paragraph export
            response = requests.get(f"{base_url}/admin/download/annotated-paragraphs/{document_id}", 
                                  headers={'Authorization': f'Bearer {admin_token}'})
            
            if response.status_code == 200:
                csv_content = response.text
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                rows = list(csv_reader)
                
                print(f"  Admin export: {len(rows)} rows")
                
                if len(rows) > 0:
                    # Check if any rows have tags
                    rows_with_tags = sum(1 for row in rows if '[Tags:' in row.get('annotated_paragraph_text', ''))
                    print(f"  Rows with tags: {rows_with_tags}")
                    
                    if rows_with_tags == 0 and tagged_count > 0:
                        print(f"  ⚠️  ISSUE: Document has {tagged_count} tagged annotations but no tags in export!")
                        
                        # Show first row content
                        first_row = rows[0]
                        paragraph_text = first_row.get('annotated_paragraph_text', '')
                        print(f"  First row text (first 200 chars): {paragraph_text[:200]}...")
                    elif rows_with_tags > 0:
                        print(f"  ✅ Tags found in export")
                else:
                    print(f"  ⚠️  Empty CSV export")
            else:
                print(f"  ❌ Admin export failed: {response.status_code}")
        else:
            print(f"  ❌ Failed to get annotations: {response.status_code}")

if __name__ == "__main__":
    test_empty_document()