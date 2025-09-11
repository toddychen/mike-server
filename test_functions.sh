#!/bin/bash

# Simple Function Calling API Test Script
# Port: 3000

echo "🧪 Testing Function Calling API (Port 3000)"
echo "=========================================="

BASE_URL="http://localhost:3000/api/functions"

echo -e "\n${YELLOW}Quick curl examples:${NC}"
echo "curl -X GET \"$BASE_URL/tools\""
echo "curl -X POST \"$BASE_URL/call\" -H \"Content-Type: application/json\" -d '{\"function_name\": \"search_entity\", \"parameters\": {\"query\": \"lebron\"}}'"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo -e "\n${YELLOW}1. Testing search_entity function${NC}"
echo "----------------------------------------"
response1=$(curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "search_entity",
    "parameters": {
      "query": "lebron",
      "entity_type": "player"
    }
  }')

if echo "$response1" | grep -q '"success":true'; then
    print_result 0 "search_entity function call successful"
    echo "Response:"
    echo "$response1" | python3 -m json.tool 2>/dev/null || echo "$response1"
else
    print_result 1 "search_entity function call failed"
    echo "Response: $response1"
fi

echo -e "\n${YELLOW}2. Testing get_league_games function${NC}"
echo "----------------------------------------"
response2=$(curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_league_games",
    "parameters": {
      "leagues": "nfl",
      "count": 2
    }
  }')

if echo "$response2" | grep -q '"success":true'; then
    print_result 0 "get_league_games function call successful"
    echo "Response:"
    echo "$response2" | python3 -m json.tool 2>/dev/null || echo "$response2"
else
    print_result 1 "get_league_games function call failed"
    echo "Response: $response2"
fi

echo -e "\n${YELLOW}3. Testing get_team_games function${NC}"
echo "----------------------------------------"
response3=$(curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_team_games",
    "parameters": {
      "team_id": "nfl.t.9"
    }
  }')

if echo "$response3" | grep -q '"success":true'; then
    print_result 0 "get_team_games function call successful"
    echo "Response:"
    echo "$response3" | python3 -m json.tool 2>/dev/null || echo "$response3"
else
    print_result 1 "get_team_games function call failed"
    echo "Response: $response3"
fi

echo -e "\n${YELLOW}4. Testing tools endpoint${NC}"
echo "----------------------------------------"
echo "Curl command: curl -s -X GET \"$BASE_URL/tools\""
response4=$(curl -s -X GET "$BASE_URL/tools")

if echo "$response4" | grep -q '"type":"function"'; then
    print_result 0 "Tools endpoint working"
    echo "Response:"
    echo "$response4" | python3 -m json.tool 2>/dev/null || echo "$response4"
else
    print_result 1 "Tools endpoint failed"
    echo "Response: $response4"
fi

echo -e "\n=========================================="
echo "Test completed!"
