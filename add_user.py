#!/usr/bin/env python3
"""
Script to add or update username/password pairs in credentials.json
Usage: python add_user.py <username> <password>
"""

import sys
import json
import os
from werkzeug.security import generate_password_hash

CREDENTIALS_FILE = 'credentials.json'

def load_credentials():
    """Load existing credentials from file"""
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
                # Filter out comment/metadata keys
                return {k: v for k, v in data.items() if not k.startswith('_')}
        except json.JSONDecodeError:
            print(f"Warning: {CREDENTIALS_FILE} exists but is not valid JSON. Creating new file.")
            return {}
    return {}

def save_credentials(credentials):
    """Save credentials to file"""
    # Preserve any existing metadata/comments
    output = {}
    
    # Try to load existing file to preserve comments
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                existing = json.load(f)
                # Copy metadata keys
                for key, value in existing.items():
                    if key.startswith('_'):
                        output[key] = value
        except:
            pass
    
    # Add credentials
    output.update(credentials)
    
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Credentials saved to {CREDENTIALS_FILE}")

def add_user(username, password):
    """Add or update a user in credentials file"""
    if not username or not password:
        print("Error: Username and password are required")
        return False
    
    # Load existing credentials
    credentials = load_credentials()
    
    # Check if user already exists
    if username in credentials:
        response = input(f"User '{username}' already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return False
    
    # Generate password hash
    password_hash = generate_password_hash(password)
    
    # Add/update user
    credentials[username] = password_hash
    
    # Save credentials
    save_credentials(credentials)
    
    print(f"✓ User '{username}' added/updated successfully")
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python add_user.py <username> <password>")
        print("\nExample:")
        print("  python add_user.py teacher1 mypassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    add_user(username, password)

if __name__ == '__main__':
    main()

