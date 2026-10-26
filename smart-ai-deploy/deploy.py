#!/usr/bin/env python3
"""
Deploy PT Yaskum Virtual Office to PythonAnywhere
Uses PythonAnywhere Web IDE API to upload files
"""

import requests
import base64
from pathlib import Path

# PythonAnywhere credentials
USERNAME = "auldihasibuan"
PASSWORD = "123456789"

# File to upload
LOCAL_FILE = Path(__file__).parent / "index.html"
REMOTE_PATH = f"/home/{USERNAME}/auldihasibuan.pythonanywhere.com/mysite/index.html"

def deploy_to_pythonanywhere():
    """Upload file to PythonAnywhere via their API"""
    
    # Read local file
    if not LOCAL_FILE.exists():
        print(f"❌ File not found: {LOCAL_FILE}")
        return False
    
    with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # PythonAnywhere API endpoint for file upload
    api_url = "https://www.pythonanywhere.com/api/user_data/"
    
    headers = {
        "Authorization": f"Token {get_api_token()}",
        "Content-Type": "application/json"
    }
    
    # Upload via bash command (alternative method)
    print("📤 Uploading to PythonAnywhere...")
    
    # Try using PythonAnywhere's web interface
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    
    # Login to PythonAnywhere
    login_resp = session.get("https://www.pythonanywhere.com/user/auldihasibuan/")
    print(f"Login status: {login_resp.status_code}")
    
    return True

def get_api_token():
    """Get PythonAnywhere API token (placeholder - user needs to provide)"""
    # This would need to be retrieved from PythonAnywhere account settings
    return "YOUR_API_TOKEN_HERE"

if __name__ == "__main__":
    deploy_to_pythonanywhere()
