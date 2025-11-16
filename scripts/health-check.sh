#!/bin/bash
# Health check script for monitoring Slack bot
# Run this via cron every 5 minutes to detect silent failures

HEALTH_URL="http://localhost:3000/"
LOG_FILE="/var/log/slack-cleaner-health.log"
SERVICE_NAME="slack-cleaner"

# Check if health endpoint responds
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    # Health check passed
    exit 0
else
    # Health check failed
    echo "[$(date -Iseconds)] Health check failed - attempting restart" >> "$LOG_FILE"

    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "[$(date -Iseconds)] Service is running but unresponsive - restarting" >> "$LOG_FILE"
        systemctl restart "$SERVICE_NAME"
    else
        echo "[$(date -Iseconds)] Service is stopped - starting" >> "$LOG_FILE"
        systemctl start "$SERVICE_NAME"
    fi

    # Wait 10 seconds and check again
    sleep 10
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "[$(date -Iseconds)] Service recovered successfully" >> "$LOG_FILE"
    else
        echo "[$(date -Iseconds)] CRITICAL: Service failed to recover" >> "$LOG_FILE"
        # You could send an alert email here
        # echo "Slack bot failed to recover" | mail -s "ALERT: Slack Bot Down" admin@example.com
    fi

    exit 1
fi
