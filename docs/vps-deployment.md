# VPS Deployment Guide

This guide provides a robust VPS deployment with automatic restart policies, health monitoring, and proper logging to prevent "silent failures".

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Python 3.11 or higher
- Root or sudo access
- All required Slack tokens (see [required-scopes.md](required-scopes.md))

## Why VPS?

**Advantages over PaaS:**
- No cold starts or container stopping issues
- Full control over the environment
- Lower cost for always-on services
- Better logging and debugging capabilities
- No platform-specific quirks

**This guide addresses common VPS issues:**
- Automatic restart on failure
- Health monitoring to detect silent failures
- Proper logging via systemd journal
- Resource limits to prevent runaway processes
- Security hardening

## Installation Steps

### 1. Create Service User

Create a dedicated user for security isolation:

```bash
sudo useradd -r -m -d /opt/slack-cleaner -s /bin/bash slack-bot
```

### 2. Install Python and Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3.11+ and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip curl git

# Verify Python version
python3.11 --version
```

### 3. Deploy Application Code

```bash
# Clone or copy your code to the server
sudo -u slack-bot git clone https://github.com/yourusername/slack-cleaner.git /opt/slack-cleaner

# Or use rsync to copy local files
# rsync -avz --exclude '.git' --exclude 'venv' ./ user@vps:/opt/slack-cleaner/

# Change to app directory
cd /opt/slack-cleaner

# Create virtual environment
sudo -u slack-bot python3.11 -m venv venv

# Install dependencies
sudo -u slack-bot venv/bin/pip install --upgrade pip
sudo -u slack-bot venv/bin/pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Create .env file
sudo -u slack-bot nano /opt/slack-cleaner/.env
```

Add your configuration:

```env
# Slack API Tokens (required)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_USER_TOKEN=xoxp-your-user-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# Admin Configuration (required)
ADMIN_USER_IDS=U123456,U789012
ADMIN_REVIEW_CHANNEL=C123456789

# Optional Configuration
AUDIT_LOG_CHANNEL=C987654321
ALLOW_ALL_CHANNEL_MEMBERS=false
PORT=3000

# Database Configuration
# Leave DATABASE_URL unset to use SQLite (recommended for VPS)
```

Secure the environment file:

```bash
sudo chmod 600 /opt/slack-cleaner/.env
sudo chown slack-bot:slack-bot /opt/slack-cleaner/.env
```

### 5. Test the Application

Before setting up systemd, test the application manually:

```bash
sudo -u slack-bot /opt/slack-cleaner/venv/bin/python /opt/slack-cleaner/app.py
```

You should see:
```
INFO:__main__:HTTP health check server running on 0.0.0.0:3000 (IPv4)
INFO:__main__:⚡️ Slack app is running!
```

Test the health endpoint:
```bash
curl http://localhost:3000/
# Should return: OK
```

If everything works, press Ctrl+C to stop and proceed to systemd setup.

### 6. Install systemd Service

```bash
# Copy service file
sudo cp /opt/slack-cleaner/systemd/slack-cleaner.service /etc/systemd/system/

# Reload systemd to recognise new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable slack-cleaner

# Start the service
sudo systemctl start slack-cleaner

# Check status
sudo systemctl status slack-cleaner
```

You should see:
```
● slack-cleaner.service - Slack Message Deletion Bot
     Loaded: loaded (/etc/systemd/system/slack-cleaner.service; enabled)
     Active: active (running) since...
```

### 7. Set Up Health Monitoring (Recommended)

This prevents "silent failures" by automatically restarting the service if it becomes unresponsive:

```bash
# Make health check script executable
sudo chmod +x /opt/slack-cleaner/scripts/health-check.sh

# Create cron job to run health check every 5 minutes
sudo crontab -e
```

Add this line:
```
*/5 * * * * /opt/slack-cleaner/scripts/health-check.sh
```

Create the log file:
```bash
sudo touch /var/log/slack-cleaner-health.log
sudo chmod 644 /var/log/slack-cleaner-health.log
```

### 8. Configure Log Rotation

Prevent logs from filling up disk space:

```bash
sudo nano /etc/logrotate.d/slack-cleaner
```

Add:
```
/var/log/slack-cleaner-health.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

## Verification

### Test the Service

1. **Check service status:**
   ```bash
   sudo systemctl status slack-cleaner
   ```

2. **View recent logs:**
   ```bash
   sudo journalctl -u slack-cleaner -n 50 --no-pager
   ```

3. **Follow logs in real-time:**
   ```bash
   sudo journalctl -u slack-cleaner -f
   ```

4. **Test health endpoint:**
   ```bash
   curl http://localhost:3000/
   ```

5. **Test in Slack:**
   - Right-click a message you sent
   - Select "Delete my message"
   - Check admin review channel for request
   - React with tick mark to approve

### Test Automatic Recovery

Simulate a crash to verify automatic restart:

```bash
# Kill the process
sudo pkill -9 -f "python app.py"

# Watch it restart automatically
sudo journalctl -u slack-cleaner -f

# Check status after a few seconds
sudo systemctl status slack-cleaner
```

You should see systemd automatically restart the service within 10 seconds.

## Monitoring and Maintenance

### View Logs

**Recent logs:**
```bash
sudo journalctl -u slack-cleaner -n 100
```

**Logs from today:**
```bash
sudo journalctl -u slack-cleaner --since today
```

**Logs with errors only:**
```bash
sudo journalctl -u slack-cleaner -p err
```

**Health check logs:**
```bash
sudo tail -f /var/log/slack-cleaner-health.log
```

### Check Resource Usage

```bash
# Memory usage
sudo systemctl status slack-cleaner | grep Memory

# Full process details
ps aux | grep "python app.py"
```

### Restart Service

```bash
sudo systemctl restart slack-cleaner
```

### Stop Service

```bash
sudo systemctl stop slack-cleaner
```

### Disable Auto-Start

```bash
sudo systemctl disable slack-cleaner
```

## Updating the Application

```bash
# Navigate to app directory
cd /opt/slack-cleaner

# Pull latest changes (if using git)
sudo -u slack-bot git pull

# Or rsync new files from local machine
# rsync -avz --exclude '.git' --exclude 'venv' ./ user@vps:/opt/slack-cleaner/

# Update dependencies if requirements.txt changed
sudo -u slack-bot venv/bin/pip install -r requirements.txt

# Restart service
sudo systemctl restart slack-cleaner

# Verify it's running
sudo systemctl status slack-cleaner
```

## Troubleshooting

### Service Won't Start

1. **Check logs for errors:**
   ```bash
   sudo journalctl -u slack-cleaner -n 50
   ```

2. **Verify environment variables:**
   ```bash
   sudo -u slack-bot cat /opt/slack-cleaner/.env
   ```

3. **Test manually:**
   ```bash
   sudo -u slack-bot /opt/slack-cleaner/venv/bin/python /opt/slack-cleaner/app.py
   ```

4. **Check file permissions:**
   ```bash
   ls -la /opt/slack-cleaner/
   ```

### Service Keeps Restarting

1. **View crash logs:**
   ```bash
   sudo journalctl -u slack-cleaner -p err
   ```

2. **Check for common issues:**
   - Invalid Slack tokens
   - Missing environment variables
   - Database file permissions
   - Network connectivity

### Health Check Failures

1. **View health check log:**
   ```bash
   sudo tail -20 /var/log/slack-cleaner-health.log
   ```

2. **Manually test health endpoint:**
   ```bash
   curl -v http://localhost:3000/
   ```

3. **Check if port is in use:**
   ```bash
   sudo netstat -tlnp | grep 3000
   ```

### High Memory Usage

If memory usage exceeds limits:

1. **Check current usage:**
   ```bash
   systemctl status slack-cleaner | grep Memory
   ```

2. **Adjust memory limits in service file:**
   ```bash
   sudo nano /etc/systemd/system/slack-cleaner.service
   # Increase MemoryMax and MemoryHigh values

   sudo systemctl daemon-reload
   sudo systemctl restart slack-cleaner
   ```

### Database Issues

If using SQLite:

1. **Check database file:**
   ```bash
   ls -lh /opt/slack-cleaner/deletion_requests.db
   ```

2. **Verify database integrity:**
   ```bash
   sudo -u slack-bot sqlite3 /opt/slack-cleaner/deletion_requests.db "PRAGMA integrity_check;"
   ```

3. **View recent requests:**
   ```bash
   sudo -u slack-bot sqlite3 /opt/slack-cleaner/deletion_requests.db "SELECT * FROM deletion_requests ORDER BY created_at DESC LIMIT 10;"
   ```

## Security Best Practices

1. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Use firewall:**
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

3. **Restrict .env file:**
   ```bash
   sudo chmod 600 /opt/slack-cleaner/.env
   ```

4. **Regular backups:**
   ```bash
   # Backup database
   sudo cp /opt/slack-cleaner/deletion_requests.db /opt/slack-cleaner/backups/deletion_requests-$(date +%Y%m%d).db
   ```

5. **Monitor auth logs:**
   ```bash
   sudo tail -f /var/log/auth.log
   ```

## Alerting (Optional)

For production deployments, consider setting up alerts:

### Email Alerts on Service Failure

Install mail utilities:
```bash
sudo apt install -y mailutils
```

Modify `/opt/slack-cleaner/scripts/health-check.sh` to send emails on critical failures (uncomment the mail command).

### Slack Alerts

You could create a separate Slack webhook to send alerts to a monitoring channel when the service fails.

## Cost Comparison

Typical VPS costs:
- **DigitalOcean Droplet (Basic):** $6/month (1GB RAM, 1 vCPU)
- **Linode Nanode:** $5/month (1GB RAM, 1 vCPU)
- **Vultr Cloud Compute:** $5/month (1GB RAM, 1 vCPU)
- **Hetzner Cloud CX11:** ~$4/month (2GB RAM, 1 vCPU)

This app uses minimal resources (~50-100MB RAM), so the smallest tier is sufficient.

## Migration from Railway

If you're migrating from Railway:

1. **Stop Railway service** (don't delete it yet - keep it as backup)

2. **Follow all installation steps above**

3. **Test thoroughly on VPS:**
   - Submit deletion requests
   - Approve via reactions
   - Check audit logs
   - Verify health monitoring

4. **Monitor for 24-48 hours** to ensure stability

5. **Delete Railway project** once confident in VPS deployment

If Railway had PostgreSQL data you want to preserve:

```bash
# Export from Railway PostgreSQL
pg_dump railway-database-url > railway-export.sql

# Import to VPS (if using PostgreSQL on VPS)
psql your-vps-database-url < railway-export.sql

# Or just use SQLite on VPS - the migration won't preserve history but starts fresh
```

## Why This Prevents Silent Failures

1. **systemd Restart Policy:**
   - `Restart=always` ensures automatic restart on any crash
   - `RestartSec=10s` prevents restart loops
   - `StartLimitBurst=5` allows up to 5 restarts in 5 minutes

2. **Health Monitoring:**
   - Cron job checks health endpoint every 5 minutes
   - Automatically restarts if unresponsive
   - Logs all failures for investigation

3. **Comprehensive Logging:**
   - All output goes to systemd journal
   - Persisted across restarts
   - Filterable by severity level
   - Health check failures logged separately

4. **Resource Limits:**
   - Prevents runaway memory usage
   - systemd will restart if limits exceeded

5. **Error Handling:**
   - Global exception handler logs fatal errors
   - Graceful shutdown on SIGTERM
   - Proper logging at all levels

## Support

For VPS-specific issues:
- Check systemd journal: `sudo journalctl -u slack-cleaner`
- Check health logs: `sudo tail -f /var/log/slack-cleaner-health.log`
- Test manually: `sudo -u slack-bot /opt/slack-cleaner/venv/bin/python /opt/slack-cleaner/app.py`

For app-specific issues:
- Review Slack app configuration
- Verify environment variables
- Check Slack API scopes

## Next Steps

After deployment:
1. Monitor logs for first 24 hours
2. Test all features (create, approve, deny requests)
3. Verify health checks are working (check `/var/log/slack-cleaner-health.log`)
4. Set up backups for database file
5. Document any custom configuration for your team
