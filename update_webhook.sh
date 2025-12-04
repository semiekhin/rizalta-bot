#!/bin/bash
sleep 10
TUNNEL_URL=$(journalctl -u cloudflared-quick -n 50 --no-pager | grep -o 'https://[a-z-]*\.trycloudflare\.com' | tail -1)
if [ -n "$TUNNEL_URL" ]; then
    curl -s "https://api.telegram.org/bot8343378629:AAHHacgXmIVhShhtPtdEooKEkV34ZD1t59s/setWebhook?url=${TUNNEL_URL}/telegram/webhook"
    echo "$(date): RIZALTA webhook updated to: $TUNNEL_URL" >> /var/log/rizalta-webhook.log
fi
