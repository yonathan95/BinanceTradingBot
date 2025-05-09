#!/usr/bin/env python3
"""
Test script to verify if the Hive Mind backend is accessible.
"""

import requests
import argparse
import sys

def test_connection(url):
    """Test if the backend is accessible at the given URL."""
    print(f"Testing connection to {url}...")
    
    try:
        # Test basic API connection
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible!")
            print(f"Response: {response.json()}")
            
            # Test VS Code API
            vscode_url = f"{url}/api/vscode/clients"
            print(f"\nTesting VS Code API at {vscode_url}...")
            
            try:
                response = requests.get(vscode_url, timeout=5)
                if response.status_code == 200:
                    print("✅ VS Code API is accessible!")
                    data = response.json()
                    client_count = len(data.get("clients", {}))
                    print(f"Found {client_count} connected VS Code clients")
                else:
                    print(f"❌ VS Code API returned status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Failed to connect to VS Code API: {str(e)}")
                
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Backend is not accessible.")
        print("Possible reasons:")
        print("  • The backend is not running")
        print("  • The URL is incorrect")
        print("  • Network issues or firewall blocking the connection")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection timed out. Backend might be running but is slow to respond.")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test connection to Hive Mind backend.")
    parser.add_argument("--url", "-u", default="http://localhost:5000", 
                      help="Backend URL (default: http://localhost:5000)")
    
    args = parser.parse_args()
    
    success = test_connection(args.url)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 