#!/bin/bash

# Fish Speech v1.2.0 Complete API Test Suite
# Tests all endpoints including new Speaker Management APIs

API_URL="http://localhost:7864"
TEST_AUDIO="test_reference.wav"
OUTPUT_DIR="api_test_outputs"

# Colors
GREEN='\033[0.32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Fish Speech v1.2.0 API Test Suite"
echo "=========================================="
echo ""

# Test counter
TOTAL=0
PASSED=0
FAILED=0

test_api() {
    local name="$1"
    local command="$2"
    TOTAL=$((TOTAL + 1))
    
    echo -n "Test $TOTAL: $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# ==================== Health Checks ====================
echo "=== Health Checks ==="

test_api "Health endpoint" \
    "curl -sf $API_URL/health | jq -e '.status == \"ok\"'"

test_api "V1 Health endpoint" \
    "curl -sf $API_URL/v1/health | jq -e '.status == \"ok\"'"

# ==================== GPU Management ====================
echo ""
echo "=== GPU Management ==="

test_api "GPU status" \
    "curl -sf $API_URL/api/gpu/status | jq -e '.model_loaded'"

test_api "GPU offload" \
    "curl -sf -X POST $API_URL/api/gpu/offload | jq -e '.status == \"offloaded\"'"

# ==================== Transcription ====================
echo ""
echo "=== Transcription ==="

if [ -f "$TEST_AUDIO" ]; then
    test_api "Transcribe audio" \
        "curl -sf -X POST $API_URL/api/transcribe -F 'audio=@$TEST_AUDIO' | jq -e '.text'"
else
    echo -e "${YELLOW}⚠ Skipped: $TEST_AUDIO not found${NC}"
fi

# ==================== Speaker Management ====================
echo ""
echo "=== Speaker Management ==="

test_api "List speakers (empty)" \
    "curl -sf $API_URL/api/speakers | jq -e '.total >= 0'"

# Create a test speaker
if [ -f "$TEST_AUDIO" ]; then
    echo -n "Creating test speaker... "
    SPEAKER_RESPONSE=$(curl -sf -X POST $API_URL/api/speakers \
        -F "name=Test Speaker" \
        -F "description=Test speaker for API testing" \
        -F "audio=@$TEST_AUDIO")
    
    if echo "$SPEAKER_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        SPEAKER_ID=$(echo "$SPEAKER_RESPONSE" | jq -r '.speaker_id')
        echo -e "${GREEN}✓ Created (ID: $SPEAKER_ID)${NC}"
        
        test_api "Get speaker by ID" \
            "curl -sf $API_URL/api/speakers/$SPEAKER_ID | jq -e '.id == \"$SPEAKER_ID\"'"
        
        test_api "List speakers (with data)" \
            "curl -sf $API_URL/api/speakers | jq -e '.total > 0'"
        
        test_api "Update speaker" \
            "curl -sf -X PUT $API_URL/api/speakers/$SPEAKER_ID \
                -F 'name=Updated Speaker' \
                -F 'description=Updated description' | jq -e '.success'"
        
        # Test TTS with speaker
        echo -n "Test TTS with speaker... "
        if curl -sf -X POST "$API_URL/api/tts/speaker/$SPEAKER_ID" \
            -F "text=你好，这是测试。" \
            -o "$OUTPUT_DIR/speaker_output.wav"; then
            if [ -f "$OUTPUT_DIR/speaker_output.wav" ] && [ -s "$OUTPUT_DIR/speaker_output.wav" ]; then
                echo -e "${GREEN}✓ PASSED${NC}"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}✗ FAILED (empty file)${NC}"
                FAILED=$((FAILED + 1))
            fi
        else
            echo -e "${RED}✗ FAILED${NC}"
            FAILED=$((FAILED + 1))
        fi
        TOTAL=$((TOTAL + 1))
        
        test_api "Delete speaker" \
            "curl -sf -X DELETE $API_URL/api/speakers/$SPEAKER_ID | jq -e '.success'"
        
    else
        echo -e "${RED}✗ Failed to create speaker${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipped speaker tests: $TEST_AUDIO not found${NC}"
fi

# ==================== Basic TTS ====================
echo ""
echo "=== Basic TTS ==="

echo -n "Test basic TTS... "
if curl -sf -X POST "$API_URL/api/tts" \
    -F "text=你好世界" \
    -o "$OUTPUT_DIR/basic_tts.wav"; then
    if [ -f "$OUTPUT_DIR/basic_tts.wav" ] && [ -s "$OUTPUT_DIR/basic_tts.wav" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED (empty file)${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

# Test TTS with reference audio
if [ -f "$TEST_AUDIO" ]; then
    echo -n "Test TTS with reference audio... "
    if curl -sf -X POST "$API_URL/api/tts" \
        -F "text=我们不对模型的任何滥用负责。" \
        -F "reference_audio=@$TEST_AUDIO" \
        -o "$OUTPUT_DIR/tts_with_ref.wav"; then
        if [ -f "$OUTPUT_DIR/tts_with_ref.wav" ] && [ -s "$OUTPUT_DIR/tts_with_ref.wav" ]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAILED (empty file)${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
    
    # Test TTS with emotion markers
    echo -n "Test TTS with emotions... "
    if curl -sf -X POST "$API_URL/api/tts" \
        -F "text=(excited) 太棒了！(laughing) 哈哈哈！" \
        -F "reference_audio=@$TEST_AUDIO" \
        -o "$OUTPUT_DIR/tts_emotion.wav"; then
        if [ -f "$OUTPUT_DIR/tts_emotion.wav" ] && [ -s "$OUTPUT_DIR/tts_emotion.wav" ]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAILED (empty file)${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
fi

# ==================== Summary ====================
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total:  $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Generated files in $OUTPUT_DIR/:"
    ls -lh "$OUTPUT_DIR/"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
