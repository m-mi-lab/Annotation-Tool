#!/usr/bin/env python3
"""
Detailed test to examine the exact CSV output from paragraph exports
"""

import requests
import sys
import json
import io
import csv
from datetime import datetime

def test_paragraph_exports():
    base_url = "https://data-fixer-1.preview.emergentagent.com/api"
    
    # Login as admin
    admin_credentials = {"email": "admin@sdoh.com", "password": "admin123"}
    response = requests.post(f"{base_url}/auth/login", json=admin_credentials)
    admin_token = response.json()['access_token']
    
    # Get documents
    response = requests.get(f"{base_url}/documents", headers={'Authorization': f'Bearer {admin_token}'})
    documents = response.json()
    
    print(f"Found {len(documents)} documents:")
    for doc in documents:
        print(f"  - {doc.get('filename')} (ID: {doc['id']})")
    
    # Use first document
    document_id = documents[0]['id']
    print(f"\nTesting with document: {documents[0].get('filename')} (ID: {document_id})")
    
    # Check annotations exist
    response = requests.get(f"{base_url}/documents/{document_id}/annotations", 
                          headers={'Authorization': f'Bearer {admin_token}'})
    annotations = response.json()
    print(f"\nFound {len(annotations)} annotations:")
    
    tagged_count = 0
    skipped_count = 0
    for ann in annotations:
        if ann.get('skipped'):
            skipped_count += 1
        else:
            tags = ann.get('tags', [])
            if tags:
                tagged_count += 1
                print(f"  - Tagged annotation: {len(tags)} tags by user {ann.get('user_id')}")
                for tag in tags:
                    print(f"    * {tag.get('domain')}:{tag.get('category')}:{tag.get('tag')}({tag.get('valence')})")
    
    print(f"\nSummary: {tagged_count} tagged, {skipped_count} skipped")
    
    # Test admin paragraph export
    print(f"\n=== ADMIN PARAGRAPH EXPORT ===")
    response = requests.get(f"{base_url}/admin/download/annotated-paragraphs/{document_id}", 
                          headers={'Authorization': f'Bearer {admin_token}'})
    
    if response.status_code == 200:
        print("✅ Admin export successful")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        
        # Parse CSV
        csv_content = response.text
        print(f"\nRAW CSV CONTENT:")
        print("=" * 80)
        print(csv_content)
        print("=" * 80)
        
        # Parse as CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        print(f"\nParsed CSV:")
        print(f"Headers: {csv_reader.fieldnames}")
        print(f"Rows: {len(rows)}")
        
        for i, row in enumerate(rows):
            print(f"\nRow {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
    else:
        print(f"❌ Admin export failed: {response.status_code}")
        print(response.text)
    
    # Create a regular user and test their export
    print(f"\n=== REGULAR USER PARAGRAPH EXPORT ===")
    
    # Register user
    timestamp = datetime.now().strftime('%H%M%S')
    user_data = {
        "email": f"test_user_{timestamp}@example.com",
        "password": "TestPass123!",
        "full_name": f"Test User {timestamp}"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code}")
        return
    
    # Login as user
    login_data = {"email": user_data['email'], "password": user_data['password']}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    user_token = response.json()['access_token']
    
    # Create some annotations as the user
    response = requests.get(f"{base_url}/documents/{document_id}/sentences", 
                          headers={'Authorization': f'Bearer {user_token}'})
    sentences = response.json()
    
    print(f"Creating annotations for user...")
    for i, sentence in enumerate(sentences[:2]):  # Annotate first 2 sentences
        annotation_data = {
            "sentence_id": sentence['id'],
            "tags": [
                {
                    "domain": "Economic Stability",
                    "category": "Employment",
                    "tag": "Unemployed",
                    "valence": "negative"
                }
            ],
            "notes": f"Test annotation {i+1}",
            "skipped": False
        }
        
        response = requests.post(f"{base_url}/annotations", json=annotation_data,
                               headers={'Authorization': f'Bearer {user_token}'})
        if response.status_code == 200:
            print(f"  ✅ Created annotation for sentence {i+1}")
        else:
            print(f"  ❌ Failed to create annotation for sentence {i+1}: {response.status_code}")
    
    # Test user paragraph export
    response = requests.get(f"{base_url}/download/my-annotated-paragraphs/{document_id}", 
                          headers={'Authorization': f'Bearer {user_token}'})
    
    if response.status_code == 200:
        print("✅ User export successful")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        
        # Parse CSV
        csv_content = response.text
        print(f"\nRAW CSV CONTENT:")
        print("=" * 80)
        print(csv_content)
        print("=" * 80)
        
        # Parse as CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        print(f"\nParsed CSV:")
        print(f"Headers: {csv_reader.fieldnames}")
        print(f"Rows: {len(rows)}")
        
        for i, row in enumerate(rows):
            print(f"\nRow {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
    else:
        print(f"❌ User export failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_paragraph_exports()