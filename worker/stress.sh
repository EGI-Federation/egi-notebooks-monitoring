#!/bin/bash

# Simple script to stress test a jupyter deployment by spawning
# a set of notebooks in parallel

MAX_SERVERS=60

OUTDIR=$(mktemp -d)
for USER in $(seq -w $MAX_SERVERS); do
    SINGLE_EXECUTION=TRUE DEBUG=TRUE STATUS_FILE="$OUTDIR/status$USER.json" JUPYTERHUB_USER="stress$USER" \
	    python monitor.py 2>&1 | tee "$OUTDIR/monitor_$USER.log" &
done
wait
echo "Results at $OUTDIR"

