#!/bin/bash
# Monitor GPU memory usage to ensure we stay under 40%

echo "DGX Spark GPU Memory Monitor"
echo "=============================="
echo ""

nvidia-smi --query-gpu=memory.used,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits | while read line; do
    used=$(echo $line | cut -d',' -f1 | tr -d ' ')
    total=$(echo $line | cut -d',' -f2 | tr -d ' ')
    free=$(echo $line | cut -d',' -f3 | tr -d ' ')
    util=$(echo $line | cut -d',' -f4 | tr -d ' ')

    percent=$(awk "BEGIN {printf \"%.1f\", ($used/$total)*100}")

    echo "Memory Used:  ${used} MiB / ${total} MiB (${percent}%)"
    echo "Memory Free:  ${free} MiB"
    echo "GPU Util:     ${util}%"
    echo ""

    # Warning if over 35%
    if (( $(echo "$percent > 35" | bc -l) )); then
        echo "⚠️  WARNING: Approaching 40% memory limit!"
    fi

    # Critical if over 40%
    if (( $(echo "$percent > 40" | bc -l) )); then
        echo "🚨 CRITICAL: Over 40% memory! DGX may crash!"
    fi

    echo "Safe operating range: < 40%"
done
