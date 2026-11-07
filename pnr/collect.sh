#!/usr/bin/env bash
# Copy the files summarize.py reads from an ORFS run into reports/pnr/.
# Usage, from anywhere after the flow has finished:
#   bash pnr/collect.sh ~/OpenROAD-flow-scripts/flow
set -euo pipefail

FLOW=${1:?path to ORFS flow/ directory}
REPO=$(cd "$(dirname "$0")/.." && pwd)
NAME=nangate45/rv32i_pipeline

declare -A CLOCK=([base]=10p0ns [fast]=2p2ns [p2p0]=2p0ns [p1p8]=1p8ns
                  [p1p6]=1p6ns [p1p4]=1p4ns [p1p2]=1p2ns)
# Full timing reports are kept for the clocks discussed in pnr/README.md.
FULL_REPORT="p1p6 p1p4 p1p2"

for v in "${!CLOCK[@]}"; do
    out=$REPO/reports/pnr/${CLOCK[$v]}
    mkdir -p "$out"
    cp "$FLOW/logs/$NAME/$v/6_report.json" "$out/"
    cp "$FLOW/results/$NAME/$v/6_final.sdc" "$out/"
    wc -l < "$FLOW/reports/$NAME/$v/5_route_drc.rpt" | tr -d ' ' > "$out/route_drc_count.txt"
    tail -n 1 "$FLOW/logs/$NAME/$v/6_final_lec_check.log" | sed 's/.*\] //' > "$out/lec_result.txt"
    if [[ " $FULL_REPORT " == *" $v "* ]]; then
        cp "$FLOW/reports/$NAME/$v/6_finish.rpt" "$out/"
    fi
done
