#!/bin/bash
# ══════════════════════════════════════════════════════════
# GroupsApp Microservices – Integration Test Script
# Tests the full flow through the API Gateway (port 80)
# ══════════════════════════════════════════════════════════
set -e

BASE="http://localhost"
PASS=0
FAIL=0

ok() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1: $2"; }

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   GroupsApp Microservices – Integration Tests    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ────────────────────────────────────────────────────────
echo "🏥 1. HEALTH CHECKS (every service responds)"
echo "────────────────────────────────────────────"

GW=$(curl -sf $BASE/health)
[ "$GW" = '{"status":"ok","service":"api-gateway"}' ] && ok "API Gateway" || fail "API Gateway" "$GW"

# ────────────────────────────────────────────────────────
echo ""
echo "🔐 2. AUTH SERVICE (svc-auth:8001)"
echo "────────────────────────────────────────────"

# Register user A
REG_A=$(curl -sf -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice_ms","email":"alice@ms.com","password":"Secret123!","display_name":"Alice MS"}')
if echo "$REG_A" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['username']=='alice_ms'" 2>/dev/null; then
  ok "Register user Alice"
else
  fail "Register Alice" "$REG_A"
fi

# Register user B
REG_B=$(curl -sf -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"bob_ms","email":"bob@ms.com","password":"Secret123!","display_name":"Bob MS"}')
if echo "$REG_B" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['username']=='bob_ms'" 2>/dev/null; then
  ok "Register user Bob"
else
  fail "Register Bob" "$REG_B"
fi

# Login Alice
LOGIN_A=$(curl -sf -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice_ms","password":"Secret123!"}')
TOKEN_A=$(echo "$LOGIN_A" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
if [ -n "$TOKEN_A" ]; then
  ok "Login Alice → token received"
else
  fail "Login Alice" "$LOGIN_A"
fi

# Login Bob
LOGIN_B=$(curl -sf -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"bob_ms","password":"Secret123!"}')
TOKEN_B=$(echo "$LOGIN_B" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
if [ -n "$TOKEN_B" ]; then
  ok "Login Bob → token received"
else
  fail "Login Bob" "$LOGIN_B"
fi

# /auth/me
ME=$(curl -sf $BASE/auth/me -H "Authorization: Bearer $TOKEN_A")
if echo "$ME" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['username']=='alice_ms'" 2>/dev/null; then
  ok "/auth/me returns Alice's profile"
else
  fail "/auth/me" "$ME"
fi

ALICE_ID=$(echo "$ME" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
BOB_ID=$(echo "$REG_B" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# ────────────────────────────────────────────────────────
echo ""
echo "👥 3. USERS SERVICE (svc-users:8002)"
echo "────────────────────────────────────────────"

SEARCH=$(curl -sf "$BASE/users/search?q=bob" -H "Authorization: Bearer $TOKEN_A")
if echo "$SEARCH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['users'])>0" 2>/dev/null; then
  ok "Search users for 'bob'"
else
  fail "Search users" "$SEARCH"
fi

PROFILE=$(curl -sf "$BASE/users/$BOB_ID" -H "Authorization: Bearer $TOKEN_A")
if echo "$PROFILE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['username']=='bob_ms'" 2>/dev/null; then
  ok "Get Bob's profile by ID"
else
  fail "Get profile" "$PROFILE"
fi

# ────────────────────────────────────────────────────────
echo ""
echo "📁 4. GROUPS SERVICE (svc-groups:8003)"
echo "────────────────────────────────────────────"

# Create group
GROUP=$(curl -sf -X POST $BASE/groups \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestGroup-MS","description":"Microservices test group"}')
GROUP_ID=$(echo "$GROUP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -n "$GROUP_ID" ]; then
  ok "Create group 'TestGroup-MS'"
else
  fail "Create group" "$GROUP"
fi

# List groups
MY_GROUPS=$(curl -sf $BASE/groups -H "Authorization: Bearer $TOKEN_A")
if echo "$MY_GROUPS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['groups'])>0" 2>/dev/null; then
  ok "List my groups"
else
  fail "List groups" "$MY_GROUPS"
fi

# Add Bob to group
ADD_MEM=$(curl -sf -X POST "$BASE/groups/$GROUP_ID/members" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$BOB_ID\"}")
if echo "$ADD_MEM" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['user_id']" 2>/dev/null; then
  ok "Add Bob to group"
else
  fail "Add member" "$ADD_MEM"
fi

# List members
MEMBERS=$(curl -sf "$BASE/groups/$GROUP_ID/members" -H "Authorization: Bearer $TOKEN_A")
if echo "$MEMBERS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['members'])==2" 2>/dev/null; then
  ok "List members (2 expected)"
else
  fail "List members" "$MEMBERS"
fi

# ────────────────────────────────────────────────────────
echo ""
echo "📺 5. CHANNELS SERVICE (svc-channels:8004)"
echo "────────────────────────────────────────────"

# List channels (should have #general auto-created)
CHANNELS=$(curl -sf "$BASE/groups/$GROUP_ID/channels" -H "Authorization: Bearer $TOKEN_A")
CHANNEL_ID=$(echo "$CHANNELS" | python3 -c "import sys,json; print(json.load(sys.stdin)['channels'][0]['id'])" 2>/dev/null)
if [ -n "$CHANNEL_ID" ]; then
  ok "List channels (#general auto-created)"
else
  fail "List channels" "$CHANNELS"
fi

# Create new channel
NEW_CH=$(curl -sf -X POST "$BASE/groups/$GROUP_ID/channels" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"name":"dev-chat","description":"Development channel"}')
NEW_CH_ID=$(echo "$NEW_CH" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -n "$NEW_CH_ID" ]; then
  ok "Create channel 'dev-chat'"
else
  fail "Create channel" "$NEW_CH"
fi

# ────────────────────────────────────────────────────────
echo ""
echo "💬 6. MESSAGES SERVICE (svc-messages:8005)"
echo "────────────────────────────────────────────"

# Send channel message
CMSG=$(curl -sf -X POST "$BASE/channels/$CHANNEL_ID/messages" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello from microservices!"}')
MSG_ID=$(echo "$CMSG" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -n "$MSG_ID" ]; then
  ok "Send channel message"
else
  fail "Send channel msg" "$CMSG"
fi

# List channel messages
CMSGS=$(curl -sf "$BASE/channels/$CHANNEL_ID/messages" -H "Authorization: Bearer $TOKEN_A")
if echo "$CMSGS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['messages'])>0" 2>/dev/null; then
  ok "List channel messages"
else
  fail "List channel msgs" "$CMSGS"
fi

# Send DM from Alice to Bob
DM=$(curl -sf -X POST "$BASE/users/$BOB_ID/messages" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hey Bob, this is a DM via microservices!"}')
DM_ID=$(echo "$DM" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -n "$DM_ID" ]; then
  ok "Send direct message (Alice → Bob)"
else
  fail "Send DM" "$DM"
fi

# List DMs
DMS=$(curl -sf "$BASE/users/$BOB_ID/messages" -H "Authorization: Bearer $TOKEN_A")
if echo "$DMS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['messages'])>0" 2>/dev/null; then
  ok "List direct messages"
else
  fail "List DMs" "$DMS"
fi

# List conversations
CONVS=$(curl -sf "$BASE/conversations" -H "Authorization: Bearer $TOKEN_A")
if echo "$CONVS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['conversations'])>0" 2>/dev/null; then
  ok "List conversations"
else
  fail "List conversations" "$CONVS"
fi

# Mark as read
READ=$(curl -sf -X POST "$BASE/messages/$DM_ID/read" -H "Authorization: Bearer $TOKEN_B")
if echo "$READ" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']" 2>/dev/null; then
  ok "Mark message as read (Bob reads Alice's DM)"
else
  fail "Mark as read" "$READ"
fi

# ────────────────────────────────────────────────────────
echo ""
echo "💓 7. PRESENCE SERVICE (svc-presence:8007)"
echo "────────────────────────────────────────────"

HB=$(curl -sf -X POST $BASE/presence/heartbeat -H "Authorization: Bearer $TOKEN_A")
if echo "$HB" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='online'" 2>/dev/null; then
  ok "Heartbeat (Alice goes online)"
else
  fail "Heartbeat" "$HB"
fi

PRES=$(curl -sf "$BASE/users/$ALICE_ID/presence" -H "Authorization: Bearer $TOKEN_B")
if echo "$PRES" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='online'" 2>/dev/null; then
  ok "Check Alice's presence (online)"
else
  fail "Get presence" "$PRES"
fi

# ────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "══════════════════════════════════════════════"
echo ""

[ $FAIL -eq 0 ] && exit 0 || exit 1
