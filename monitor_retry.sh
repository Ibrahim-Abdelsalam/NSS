#!/bin/bash
# Monitor retry progress

LOG_FILE="retry_output.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "Error: $LOG_FILE not found"
    exit 1
fi

# Count completed configs
COMPLETED=$(grep -c "✓ SUCCESS" "$LOG_FILE" || echo 0)
FAILED=$(grep -c "✗ FAILED" "$LOG_FILE" || echo 0)
TOTAL=40

echo "============================================"
echo "Retry Progress Monitor"
echo "============================================"
echo "Completed: $COMPLETED/$TOTAL"
echo "Failed: $FAILED/$TOTAL"
echo "Remaining: $((TOTAL - COMPLETED - FAILED))"
echo ""
echo "Latest activity:"
echo "--------------------------------------------"
tail -15 "$LOG_FILE"
echo ""
echo "To follow in real-time: tail -f $LOG_FILE"
