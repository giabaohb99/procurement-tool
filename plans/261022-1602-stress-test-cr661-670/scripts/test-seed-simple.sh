#!/bin/bash
# Simple seed idempotency test - just run each seed script 3 times and check for errors

set -e

RESULTS_FILE="/tmp/seed-idempotency-results.txt"
> "$RESULTS_FILE"

echo "=== Seed Idempotency Test ===" | tee -a "$RESULTS_FILE"
echo "Testing help seed scripts for idempotency..." | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

SEEDS=(
    "python -m app.seed_help_nghi_phep"
    "python -m app.seed_help_van_ban"
    "python -m app.seed_help_cong_viec"
    "python -m app.seed_help_nhan_su"
)

for seed_cmd in "${SEEDS[@]}"; do
    seed_name=$(echo "$seed_cmd" | sed 's/.*seed_help_//' | sed 's/python -m app.//')
    echo "Testing $seed_name..." | tee -a "$RESULTS_FILE"

    run_count=0
    error_count=0

    for run in 1 2 3; do
        echo "  Run $run/3..." | tee -a "$RESULTS_FILE"
        run_count=$((run_count + 1))

        if eval "cd /app && $seed_cmd" >/dev/null 2>&1; then
            echo "    ✓ OK" | tee -a "$RESULTS_FILE"
        else
            echo "    ✗ FAILED" | tee -a "$RESULTS_FILE"
            error_count=$((error_count + 1))
        fi
    done

    if [ $error_count -eq 0 ]; then
        echo "  Result: PASS (all 3 runs succeeded)" | tee -a "$RESULTS_FILE"
    else
        echo "  Result: FAIL ($error_count/$run_count runs failed)" | tee -a "$RESULTS_FILE"
    fi
    echo "" | tee -a "$RESULTS_FILE"
done

echo "=== Testing Concurrent Seed Execution ===" | tee -a "$RESULTS_FILE"
echo "Running 2 copies of seed_help_thu_mua_cap_nhat concurrently..." | tee -a "$RESULTS_FILE"

(cd /app && python -m app.seed_help_thu_mua_cap_nhat >/dev/null 2>&1) &
PID1=$!

(cd /app && python -m app.seed_help_thu_mua_cap_nhat >/dev/null 2>&1) &
PID2=$!

wait $PID1 2>/dev/null
RESULT1=$?

wait $PID2 2>/dev/null
RESULT2=$?

if [ $RESULT1 -eq 0 ] && [ $RESULT2 -eq 0 ]; then
    echo "Concurrent runs: PASS" | tee -a "$RESULTS_FILE"
else
    echo "Concurrent runs: FAIL (return codes: $RESULT1, $RESULT2)" | tee -a "$RESULTS_FILE"
fi

echo "" | tee -a "$RESULTS_FILE"
echo "Test complete. Results written to $RESULTS_FILE"
cat "$RESULTS_FILE"
