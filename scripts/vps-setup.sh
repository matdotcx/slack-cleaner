#!/bin/bash
# VPS Quick Setup Script
# Run this on your VPS to automate the deployment process
#
# Usage: sudo bash vps-setup.sh

set -e

echo "=== Slack Message Deletion Bot - VPS Setup ==="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

# Configuration
APP_DIR="/opt/slack-cleaner"
SERVICE_USER="slack-bot"
PYTHON_VERSION="python3.11"

echo "Step 1/8: Updating system packages..."
apt update && apt upgrade -y

echo
echo "Step 2/8: Installing Python and dependencies..."
apt install -y python3.11 python3.11-venv python3-pip curl git sqlite3

echo
echo "Step 3/8: Creating service user..."
if id "$SERVICE_USER" &>/dev/null; then
    echo "User $SERVICE_USER already exists, skipping..."
else
    useradd -r -m -d "$APP_DIR" -s /bin/bash "$SERVICE_USER"
    echo "User $SERVICE_USER created"
fi

echo
echo "Step 4/8: Setting up application directory..."
if [ -d "$APP_DIR" ]; then
    echo "Directory $APP_DIR already exists"
    echo "Do you want to:"
    echo "  1) Keep existing files (skip)"
    echo "  2) Backup and replace"
    read -p "Enter choice (1 or 2): " choice

    if [ "$choice" = "2" ]; then
        backup_dir="${APP_DIR}-backup-$(date +%Y%m%d-%H%M%S)"
        echo "Creating backup at $backup_dir..."
        cp -r "$APP_DIR" "$backup_dir"
        echo "Backup created"
    fi
else
    mkdir -p "$APP_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
fi

echo
echo "Step 5/8: Installing Python dependencies..."
cd "$APP_DIR"

if [ ! -d "venv" ]; then
    sudo -u "$SERVICE_USER" $PYTHON_VERSION -m venv venv
    echo "Virtual environment created"
fi

if [ -f "requirements.txt" ]; then
    sudo -u "$SERVICE_USER" venv/bin/pip install --upgrade pip
    sudo -u "$SERVICE_USER" venv/bin/pip install -r requirements.txt
    echo "Dependencies installed"
else
    echo "WARNING: requirements.txt not found - you'll need to install dependencies manually"
fi

echo
echo "Step 6/8: Setting up environment variables..."
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"
        echo
        echo "IMPORTANT: Edit $APP_DIR/.env with your Slack tokens:"
        echo "  sudo nano $APP_DIR/.env"
        echo
    else
        echo "WARNING: .env.example not found - you'll need to create .env manually"
    fi
else
    echo ".env already exists, skipping..."
fi

echo
echo "Step 7/8: Installing systemd service..."
if [ -f "$APP_DIR/systemd/slack-cleaner.service" ]; then
    cp "$APP_DIR/systemd/slack-cleaner.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "systemd service installed"
else
    echo "WARNING: systemd service file not found at $APP_DIR/systemd/slack-cleaner.service"
fi

echo
echo "Step 8/8: Setting up health monitoring..."
if [ -f "$APP_DIR/scripts/health-check.sh" ]; then
    chmod +x "$APP_DIR/scripts/health-check.sh"

    # Create health log file
    touch /var/log/slack-cleaner-health.log
    chmod 644 /var/log/slack-cleaner-health.log

    # Add cron job if not already present
    if ! crontab -l 2>/dev/null | grep -q "health-check.sh"; then
        (crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/scripts/health-check.sh") | crontab -
        echo "Health monitoring cron job installed"
    else
        echo "Health monitoring cron job already exists"
    fi

    # Set up log rotation
    cat > /etc/logrotate.d/slack-cleaner <<EOF
/var/log/slack-cleaner-health.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
}
EOF
    echo "Log rotation configured"
else
    echo "WARNING: health-check.sh not found at $APP_DIR/scripts/health-check.sh"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. Edit environment variables:"
echo "   sudo nano $APP_DIR/.env"
echo
echo "2. Test the application:"
echo "   sudo -u $SERVICE_USER $APP_DIR/venv/bin/python $APP_DIR/app.py"
echo "   (Press Ctrl+C to stop)"
echo
echo "3. Enable and start the service:"
echo "   sudo systemctl enable slack-cleaner"
echo "   sudo systemctl start slack-cleaner"
echo
echo "4. Check service status:"
echo "   sudo systemctl status slack-cleaner"
echo
echo "5. View logs:"
echo "   sudo journalctl -u slack-cleaner -f"
echo
