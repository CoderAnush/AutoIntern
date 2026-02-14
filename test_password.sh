#!/bin/bash

echo "Test: Password Change Endpoint"
echo ""

# Register a test user
echo "1. Registering user..."
REGISTER=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pwd_test3@example.com","password":"TestPass123!"}')

echo "Register response: $REGISTER"
echo ""

# Try with an existing registered user
echo "2. Login to get token..."
LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test_1770899561@example.com","password":"TestPass123!"}')

echo "Login response: $LOGIN"
TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -1)
echo "Extracted token: $TOKEN"
echo ""

if [ ! -z "$TOKEN" ]; then
  echo "3. Testing password change..."
  curl -s -X POST http://localhost:8000/api/users/change-password \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"current_password":"TestPass123!","new_password":"NewPass456!"}'
else
  echo "Failed to get token"
fi
