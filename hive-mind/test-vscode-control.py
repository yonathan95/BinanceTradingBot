#!/usr/bin/env python3
"""
Test script to verify if the backend can control VS Code Git context.
"""

import requests
import json
import time
import sys

def test_vscode_control():
    """Test if the backend can control VS Code."""
    base_url = "http://localhost:5000"
    
    print("\n=== Testing Hive Mind VS Code Control ===\n")
    
    # Step 1: Check if the API is running
    try:
        print("1. Checking if the backend is running...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print(f"❌ Backend responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to the backend. Make sure it's running on http://localhost:5000")
        return False
    
    # Step 2: Get list of connected VS Code clients
    print("\n2. Checking for connected VS Code clients...")
    try:
        response = requests.get(f"{base_url}/api/vscode/clients")
        if response.status_code != 200:
            print(f"❌ Failed to get client list: {response.status_code}")
            return False
        
        clients_data = response.json()
        clients = clients_data.get("clients", {})
        
        if not clients:
            print("❌ No VS Code clients connected. Make sure VS Code is running with the extension installed")
            return False
        
        print(f"✅ Found {len(clients)} connected client(s)!")
        for client_id, client in clients.items():
            connection_status = "Connected" if client.get("connected") else "Disconnected"
            print(f"   • Client ID: {client_id[:8]}... ({connection_status})")
            print(f"     Workspace: {client.get('workspace_name')}")
            print(f"     Current Branch: {client.get('current_branch')}")
        
        # Get the first client ID
        client_id = next(iter(clients.keys()))
        workspace_name = clients[client_id].get("workspace_name")
        current_branch = clients[client_id].get("current_branch")
        
    except Exception as e:
        print(f"❌ Error getting clients: {str(e)}")
        return False
    
    # Step 3: Try to change branch
    print(f"\n3. Attempting to change branch for client {client_id[:8]}...")
    
    # Determine target branch (different from current)
    target_branch = "main" if current_branch != "main" else "develop"
    
    try:
        checkout_data = {
            "branch": target_branch,
            "clientId": client_id,
            "message": "Test branch switch from backend"
        }
        
        response = requests.post(
            f"{base_url}/api/vscode/checkout", 
            json=checkout_data
        )
        
        if response.status_code in (200, 201):
            print(f"✅ Sent command to switch to branch '{target_branch}'")
            print(f"   Response: {response.json()}")
            
            # Wait a bit and check if branch was changed
            print("\n   Waiting 3 seconds for VS Code to process the change...")
            time.sleep(3)
            
            response = requests.get(f"{base_url}/api/vscode/client/{client_id}")
            if response.status_code == 200:
                client_data = response.json()
                new_branch = client_data.get("current_branch")
                
                if new_branch == target_branch:
                    print(f"✅ SUCCESS! Branch successfully changed to '{new_branch}'")
                    print("\n=== VS Code control is working correctly! ===")
                    return True
                else:
                    print(f"❌ Branch didn't change. Still on '{new_branch}'")
                    print("   This might be because:")
                    print("   • The target branch doesn't exist in the repository")
                    print("   • VS Code couldn't execute the Git command")
                    print("   • The backend didn't properly track the change")
        else:
            print(f"❌ Failed to send checkout command: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending checkout command: {str(e)}")
    
    print("\n=== Test completed with errors ===")
    return False

if __name__ == "__main__":
    test_vscode_control() 