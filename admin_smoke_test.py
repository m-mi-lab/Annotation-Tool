#!/usr/bin/env python3
"""
Smoke test for admin endpoints - validates all required functionality
"""

import requests
import json
from datetime import datetime

def test_admin_endpoints():
    base_url = "https://sdoh-tagger.preview.emergentagent.com/api"
    
    # Login as admin
    login_response = requests.post(f"{base_url}/auth/login", 
                                 json={"email": "admin@sdoh.com", "password": "admin123"})
    
    if login_response.status_code != 200:
        print("❌ Admin login failed")
        return False
    
    admin_token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    print("🔍 Testing Admin Endpoints...")
    
    # Test 1: GET /api/admin/users
    response = requests.get(f"{base_url}/admin/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        if users and all('role' in user for user in users):
            print("✅ GET /api/admin/users - Returns users with role field")
        else:
            print("❌ GET /api/admin/users - Missing role field in some users")
            return False
    else:
        print(f"❌ GET /api/admin/users failed - Status: {response.status_code}")
        return False
    
    # Test 2: POST /api/admin/users (create annotator)
    timestamp = datetime.now().strftime('%H%M%S')
    new_user = {
        "email": f"test_annotator_{timestamp}@test.com",
        "password": "TestPass123!",
        "full_name": f"Test Annotator {timestamp}",
        "role": "annotator"
    }
    
    response = requests.post(f"{base_url}/admin/users", headers=headers, json=new_user)
    if response.status_code == 200:
        created_user = response.json()
        user_id = created_user.get('id')
        if user_id and created_user.get('role') == 'annotator' and 'password' not in created_user:
            print("✅ POST /api/admin/users - Creates user without exposing password")
        else:
            print("❌ POST /api/admin/users - Invalid response format")
            return False
    else:
        print(f"❌ POST /api/admin/users failed - Status: {response.status_code}")
        return False
    
    # Test 3: PUT /api/admin/users/{user_id}
    update_data = {"is_active": False, "role": "admin"}
    response = requests.put(f"{base_url}/admin/users/{user_id}", headers=headers, json=update_data)
    if response.status_code == 200:
        updated_user = response.json()
        if updated_user.get('is_active') == False and updated_user.get('role') == 'admin':
            print("✅ PUT /api/admin/users/{user_id} - Updates is_active and role")
        else:
            print("❌ PUT /api/admin/users/{user_id} - Update failed")
            return False
    else:
        print(f"❌ PUT /api/admin/users/{user_id} failed - Status: {response.status_code}")
        return False
    
    # Test 4: DELETE /api/admin/users/{user_id}
    response = requests.delete(f"{base_url}/admin/users/{user_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if 'message' in result and 'user_name' in result:
            print("✅ DELETE /api/admin/users/{user_id} - Deletes user successfully")
        else:
            print("❌ DELETE /api/admin/users/{user_id} - Invalid response format")
            return False
    else:
        print(f"❌ DELETE /api/admin/users/{user_id} failed - Status: {response.status_code}")
        return False
    
    # Test 5: POST /api/admin/users/bulk-delete
    # Create 2 test users first
    test_user_ids = []
    for i in range(2):
        test_user = {
            "email": f"bulk_test_{timestamp}_{i}@test.com",
            "password": "TestPass123!",
            "full_name": f"Bulk Test User {i}",
            "role": "annotator"
        }
        response = requests.post(f"{base_url}/admin/users", headers=headers, json=test_user)
        if response.status_code == 200:
            test_user_ids.append(response.json()['id'])
    
    if len(test_user_ids) == 2:
        bulk_delete_data = {"ids": test_user_ids}
        response = requests.post(f"{base_url}/admin/users/bulk-delete", headers=headers, json=bulk_delete_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('deleted') == 2:
                print("✅ POST /api/admin/users/bulk-delete - Deletes multiple users")
            else:
                print(f"❌ POST /api/admin/users/bulk-delete - Expected 2 deleted, got {result.get('deleted')}")
                return False
        else:
            print(f"❌ POST /api/admin/users/bulk-delete failed - Status: {response.status_code}")
            return False
    else:
        print("❌ Could not create test users for bulk delete test")
        return False
    
    # Test 6: POST /api/admin/documents/bulk-delete
    # Create test documents first
    import io
    csv_content = """patient_id,discharge_summary
1,"Test patient with diabetes"
2,"Another test patient"
"""
    
    doc_ids = []
    for i in range(2):
        files = {
            'file': (f'bulk_test_{i}.csv', csv_content, 'text/csv'),
            'project_name': (None, f'Bulk Test Project {i}')
        }
        response = requests.post(f"{base_url}/documents/upload", 
                               files=files, 
                               headers={'Authorization': f'Bearer {admin_token}'})
        if response.status_code == 200:
            doc_ids.append(response.json()['id'])
    
    if len(doc_ids) == 2:
        bulk_delete_data = {"ids": doc_ids}
        response = requests.post(f"{base_url}/admin/documents/bulk-delete", headers=headers, json=bulk_delete_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('deleted') == 2:
                print("✅ POST /api/admin/documents/bulk-delete - Deletes multiple documents")
            else:
                print(f"❌ POST /api/admin/documents/bulk-delete - Expected 2 deleted, got {result.get('deleted')}")
                return False
        else:
            print(f"❌ POST /api/admin/documents/bulk-delete failed - Status: {response.status_code}")
            return False
    else:
        print("❌ Could not create test documents for bulk delete test")
        return False
    
    # Test 7: RBAC - Non-admin access should be denied
    # Create regular user
    regular_user = {
        "email": f"rbac_test_{timestamp}@test.com",
        "password": "TestPass123!",
        "full_name": "RBAC Test User"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=regular_user)
    if response.status_code == 200:
        # Login as regular user
        login_response = requests.post(f"{base_url}/auth/login", 
                                     json={"email": regular_user["email"], "password": regular_user["password"]})
        if login_response.status_code == 200:
            regular_token = login_response.json()['access_token']
            regular_headers = {'Authorization': f'Bearer {regular_token}'}
            
            # Try to access admin endpoint
            response = requests.get(f"{base_url}/admin/users", headers=regular_headers)
            if response.status_code == 403:
                print("✅ RBAC - Non-admin access properly denied (403)")
            else:
                print(f"❌ RBAC - Expected 403, got {response.status_code}")
                return False
        else:
            print("❌ Could not login as regular user for RBAC test")
            return False
    else:
        print("❌ Could not create regular user for RBAC test")
        return False
    
    print("\n🎉 All admin endpoint tests passed!")
    return True

if __name__ == "__main__":
    success = test_admin_endpoints()
    exit(0 if success else 1)