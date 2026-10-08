#!/bin/bash
# Usage: wait-for-url.sh URL INTERVAL MAXMINUTES
#
# Waits until the URL is available (responds with an HTTP status below 400,
# after following redirects), trying every INTERVAL seconds for at most
# MAXMINUTES minutes, and fails if it does not become available. Used to avoid
# reporting failures (or deploying a website with missing information) when a
# server like git.esss.dk is temporarily down.
set -u
url="$1"
interval="$2"
maxminutes="$3"
deadline=$(( $(date +%s) + 60 * maxminutes ))
while true; do
    if curl -fsSL -o /dev/null --max-time 30 "$url"; then
        echo "$url is available"
        exit 0
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
        echo "::error::$url was not available for $maxminutes minutes"
        exit 1
    fi
    echo "$url is not available, trying again in $interval seconds"
    sleep "$interval"
done
