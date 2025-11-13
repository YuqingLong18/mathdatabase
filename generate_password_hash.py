#!/usr/bin/env python3
"""
Helper script to generate password hashes for credentials.json
Usage: python generate_password_hash.py <username> <password>
"""

import sys
from werkzeug.security import generate_password_hash

if len(sys.argv) != 3:
    print("Usage: python generate_password_hash.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

password_hash = generate_password_hash(password)

print(f"\nAdd this to your credentials.json file:")
print(f'  "{username}": "{password_hash}"')
print(f"\nOr use this complete entry:")
print(f'{{')
print(f'  "{username}": "{password_hash}"')
print(f'}}')

